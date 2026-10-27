"""One retriever for every compared system: similarity to the question, recency, or both.

SharedRetriever scores each record as (1 - alpha) * cosine(question, record) +
alpha * recency, where recency = 0.5 ** (age_days / half_life_days) and the age runs
from the record's created_at to the latest observed turn. The record's text is its
context line, exactly as the answer model will read it. Records are taken in
descending score, newest first among equal scores, while they fit the byte budget;
the selection is returned in time order. With alpha 1 the score depends on age alone,
so the ranking is the time order itself: no embedding is computed, and the selection
equals the controlled comparison's newest-first reader, tie-breaks included.

Compared systems differ only in alpha and half_life_days (describe). Everything else,
the embedding model included, must be equal across them (shared_settings).

OllamaEmbeddings embeds texts through an OpenAI-compatible /v1/embeddings endpoint,
by default a local Ollama server, and saves every embedding on disk, keyed by model
and text, so a text already embedded is never sent again.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence

from tracemem.model_client import LOCAL_BASE_URL
from tracemem.resolver import FatalModelError, ResolverConfigError
from tracemem.schema import Record

DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_CACHE_DIR = "cache/emb"
DEFAULT_HALF_LIFE_DAYS = 7.0
POLICY = "similarity_recency_newest_tiebreak_whole_lines_v1"
# Models trained with task prefixes, keyed by name without the tag: (query, document).
# Any other model embeds the bare text.
TASK_PREFIXES = {"nomic-embed-text": ("search_query: ", "search_document: ")}


def embed_model(environ: Mapping[str, str] | None = None) -> str:
    """The embedding model TRACEMEM_EMBED_MODEL names, nomic-embed-text by default."""
    env = os.environ if environ is None else environ
    return env.get("TRACEMEM_EMBED_MODEL", "").strip() or DEFAULT_EMBED_MODEL


def embedding_settings(model: str) -> dict:
    """What decides an embedding: the model and the task prefix put before each text."""
    query_prefix, document_prefix = TASK_PREFIXES.get(model.split(":", 1)[0], ("", ""))
    return {"api": "openai_compatible_embeddings", "model": model,
            "query_prefix": query_prefix, "document_prefix": document_prefix}


class Embedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("embeddings of different lengths cannot be compared")
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / norm if norm else 0.0


def recency(created_at: datetime, latest: datetime, half_life_days: float) -> float:
    """1 for a record of the latest turn, halving every half_life_days of age."""
    age_days = (latest - created_at).total_seconds() / 86400
    return 0.5 ** (age_days / half_life_days)


def _time_key(record: Record) -> tuple:
    return record.created_at, record.created_turn, record.item, record.value, record.record_id


class OllamaEmbeddings:
    """Embeddings from an OpenAI-compatible endpoint, saved on disk by model and text.

    Every text, after its task prefix, is looked up in the cache first; only the
    missing ones are sent, in batches. A failed request saves nothing. Connection
    failures, timeouts and transient statuses are retried up to max_attempts times
    in all; then, or on any other error status, the run stops with FatalModelError.
    """

    def __init__(self, *, base_url: str = LOCAL_BASE_URL, model: str = DEFAULT_EMBED_MODEL,
                 api_key: str = "local", cache_dir: str | os.PathLike = DEFAULT_CACHE_DIR,
                 timeout_seconds: float = 120.0, max_attempts: int = 3, batch_size: int = 64):
        try:
            import openai
        except ImportError:
            raise ResolverConfigError('Install the optional SDK with pip install -e ".[llm]"') from None
        if not model.strip():
            raise ResolverConfigError("TRACEMEM_EMBED_MODEL must name an embedding model")
        self._sdk = openai
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url, max_retries=0)
        self.base_url, self.model = base_url, model
        settings = embedding_settings(model)
        self.query_prefix, self.document_prefix = settings["query_prefix"], settings["document_prefix"]
        self.cache_dir = Path(cache_dir)
        self.timeout_seconds, self.max_attempts, self.batch_size = timeout_seconds, max_attempts, batch_size

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "OllamaEmbeddings":
        """The local server of TRACEMEM_LOCAL_BASE_URL and the model TRACEMEM_EMBED_MODEL."""
        env = os.environ if environ is None else environ
        return cls(base_url=env.get("TRACEMEM_LOCAL_BASE_URL", "").strip() or LOCAL_BASE_URL,
                   model=embed_model(env),
                   api_key=env.get("TRACEMEM_LOCAL_API_KEY", "").strip() or "local")

    def describe(self) -> dict:
        return {**embedding_settings(self.model), "base_url": self.base_url}

    def embed_query(self, text: str) -> list[float]:
        return self._embed([self.query_prefix + text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed([self.document_prefix + text for text in texts])

    def key(self, text: str) -> str:
        material = {"model": self.model, "text": text}
        return hashlib.sha256(json.dumps(material, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    def _path(self, text: str) -> Path:
        key = self.key(text)
        return self.cache_dir / key[:2] / f"{key}.json"

    def _embed(self, texts: list[str]) -> list[list[float]]:
        vectors = {}
        for text in dict.fromkeys(texts):
            saved = self._read(self._path(text))
            if saved is not None:
                vectors[text] = saved
        missing = [text for text in dict.fromkeys(texts) if text not in vectors]
        for start in range(0, len(missing), self.batch_size):
            batch = missing[start:start + self.batch_size]
            for text, vector in zip(batch, self._request(batch)):
                self._write(self._path(text), vector)
                vectors[text] = vector
        return [vectors[text] for text in texts]

    def _request(self, texts: list[str]) -> list[list[float]]:
        for _ in range(self.max_attempts):
            try:
                result = self._client.embeddings.create(model=self.model, input=texts, encoding_format="float",
                                                        timeout=self.timeout_seconds)
            except self._sdk.APIConnectionError:
                continue
            except self._sdk.APIStatusError as error:
                code = error.status_code
                if code in (408, 409, 429) or code >= 500:
                    continue
                raise FatalModelError(f"embedding server rejected the request (status {code}); "
                                      "check TRACEMEM_EMBED_MODEL and TRACEMEM_LOCAL_BASE_URL") from None
            rows = sorted(result.data, key=lambda row: row.index)
            vectors = [[float(value) for value in row.embedding] for row in rows]
            if len(vectors) != len(texts):
                raise FatalModelError("embedding server returned the wrong number of embeddings")
            if not all(vectors):
                raise FatalModelError("embedding server returned an empty embedding")
            return vectors
        raise FatalModelError(f"embedding server unavailable after {self.max_attempts} attempts")

    def _read(self, path: Path) -> list[float] | None:
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        # A malformed file is a miss; the next embedding replaces it.
        vector = saved.get("embedding") if isinstance(saved, dict) else None
        if not isinstance(vector, list) or not vector or not all(isinstance(v, (int, float)) for v in vector):
            return None
        return [float(value) for value in vector]

    def _write(self, path: Path, vector: list[float]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write then rename, so an interrupted run never leaves a half-written file.
        handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump({"model": self.model, "embedding": vector}, stream)
        os.replace(temporary, path)


class SharedRetriever:
    """Choose the records an answer model reads, by similarity to the question and recency."""

    def __init__(self, alpha: float, half_life_days: float, embedder: Embedder | None = None):
        for name, value in (("alpha", alpha), ("half_life_days", half_life_days)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{name} must be a finite number")
        if not 0 <= alpha <= 1:
            raise ValueError("alpha must be between 0 and 1")
        if half_life_days <= 0:
            raise ValueError("half_life_days must be positive")
        self.alpha, self.half_life_days = float(alpha), float(half_life_days)
        # Only a score with a similarity term needs embeddings; the default is the local server.
        self.embedder = embedder if embedder is not None or self.alpha == 1 else OllamaEmbeddings.from_env()

    def _embedder(self) -> dict | str | None:
        if self.alpha == 1:
            return None
        describe = getattr(self.embedder, "describe", None)
        return describe() if callable(describe) else type(self.embedder).__name__

    def describe(self) -> dict:
        """The settings compared systems may differ in, for the run manifest."""
        ranking = "newest_first" if self.alpha == 1 else "similarity" if self.alpha == 0 else "similarity_and_recency"
        return {"ranking": ranking, "alpha": self.alpha, "half_life_days": self.half_life_days,
                "embedder": self._embedder()}

    def shared_settings(self) -> dict:
        """The settings every compared system must share, for the comparison settings.

        A system that embeds records its embedder's model and prefixes; one that ranks
        by recency alone records those of TRACEMEM_EMBED_MODEL, the model a similarity
        system run alongside it embeds with. Runs embedded with different models then
        cannot be reported together. The server's address does not change an embedding,
        so it is not recorded here.
        """
        embedder = self._embedder()
        if embedder is None:
            embedding = embedding_settings(embed_model())
        elif isinstance(embedder, dict):
            embedding = {key: value for key, value in embedder.items() if key != "base_url"}
        else:
            embedding = embedder
        return {"policy": POLICY, "recency_age": "record_created_at_to_latest_observed_turn",
                "document_text": "context_line", "embedding": embedding}

    def select(self, question: str, records: Sequence[Record], latest: datetime | None, budget_bytes: int,
               line: Callable[[Record], str], top_k: int | None = None) -> list[Record]:
        """The records that fit budget_bytes, best first, returned in time order.

        A record costs its line's UTF-8 bytes, plus one for the newline before it
        unless it is the first chosen; a line that does not fit is skipped whole and
        the next one is tried. With top_k, at most top_k records are chosen, the
        best-scoring that fit; without it, every record that fits is. latest is the
        time of the latest observed turn; it is needed only when the score mixes
        similarity and recency.
        """
        if top_k is not None and (isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1):
            raise ValueError("top_k must be a positive integer")
        if not records:
            return []
        lines = [line(record) for record in records]
        if self.alpha == 1:
            # Recency falls strictly with age, so ranking by it is ranking by time.
            order = sorted(range(len(records)), key=lambda i: _time_key(records[i]), reverse=True)
        else:
            if self.alpha > 0 and latest is None:
                raise ValueError("a recency score needs the time of the latest observed turn")
            query = self.embedder.embed_query(question)
            vectors = self.embedder.embed_documents(lines)
            scores = [(1 - self.alpha) * cosine(query, vector)
                      + (self.alpha * recency(record.created_at, latest, self.half_life_days) if self.alpha else 0.0)
                      for record, vector in zip(records, vectors)]
            order = sorted(range(len(records)), key=lambda i: (scores[i], _time_key(records[i])), reverse=True)
        chosen, size = [], 0
        for index in order:
            if top_k is not None and len(chosen) >= top_k:
                break
            cost = len(lines[index].encode("utf-8")) + bool(chosen)
            if size + cost <= budget_bytes:
                chosen.append(index)
                size += cost
        # Newest first, then reversed: equal keys end up as the newest-first reader leaves them.
        chosen.sort(key=lambda i: _time_key(records[i]), reverse=True)
        return [records[index] for index in reversed(chosen)]
