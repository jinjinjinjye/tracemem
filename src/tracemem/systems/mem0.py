"""Real Mem0 OSS baseline for the TraceMem evaluation harness.

Mem0 receives only public dialogue turns, never scenario scripts, expected
answers, item values/aliases, or the gold timeline. Mem0 itself extracts and
updates memories; the separate answer model reads only Mem0 search results.

This is an end-to-end baseline. It deliberately does not accept gold candidates:
replacing Mem0's extraction with TraceMem's labels would no longer test Mem0's
normal memory-update pipeline.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from tracemem.schema import Answer, Candidate, ScenarioMeta, SystemQuestion, Turn, Usage, session_of


ANSWER_PROMPT = """You answer questions about a team's project using ONLY retrieved memories.
Treat suggestions and speculative statements as unconfirmed, not decisions.
For a dispute that has not been resolved, return conflict. For a question that
cannot be answered from the memories, return none. Do not guess from the
question's wording. A previous decision is not necessarily the current one.
For an as_of question, only use information established by the requested session.
Return a JSON object with exactly these fields:
  status: one of answer, none, conflict, abstain
  value: the exact project decision or task state if status is answer, else null
  cited_turn_ids: source turn IDs supporting the answer (only those provided)
Do not make up source turns or claim evidence that is not present."""


def _memory_rows(result: Any) -> list[dict]:
    """Read the OSS SDK's {results: [...]} search format defensively."""
    rows = result.get("results", []) if isinstance(result, dict) else result
    if not isinstance(rows, list):
        raise ValueError("unexpected Mem0 search response: expected a list of results")
    return [row for row in rows if isinstance(row, dict)]


def _source_turn(row: dict) -> str | None:
    """Mem0 may return custom metadata nested or flattened."""
    meta = row.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
    turn = meta.get("source_turn_id") or row.get("source_turn_id")
    return turn if isinstance(turn, str) else None


class Mem0System:
    """Run Mem0's own inference/update/search pipeline under the standard harness."""

    name = "mem0"
    accepts_gold_candidates = False

    def __init__(
        self,
        meta: ScenarioMeta,
        *,
        memory: Any | None = None,
        answer_client: Any | None = None,
        top_k: int = 10,
        memory_model: str | None = None,
        answer_model: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        self.meta = meta
        self.top_k = top_k
        self.memory_model = memory_model or os.getenv("MEM0_MEMORY_MODEL", "gpt-5-mini")
        self.answer_model = answer_model or os.getenv("MEM0_ANSWER_MODEL", "gpt-4.1-mini")
        self.embedding_model = embedding_model or os.getenv("MEM0_EMBEDDING_MODEL", "text-embedding-3-small")
        # A fresh unique scope for EVERY scenario and run; never re-use a project ID
        # as the sole Mem0 scope, because that would leak between repeated runs.
        self.user_id = f"tracemem-{uuid.uuid4().hex}"
        self._observed: dict[str, Turn] = {}
        self._local_store: tempfile.TemporaryDirectory[str] | None = None

        if memory is None:
            if not os.getenv("OPENAI_API_KEY"):
                raise RuntimeError("Mem0 baseline requires OPENAI_API_KEY")
            try:
                from mem0 import Memory
            except ImportError as exc:
                raise RuntimeError('Install the Mem0 baseline: pip install -e ".[mem0]"') from exc
            self._local_store = tempfile.TemporaryDirectory(prefix="tracemem-mem0-")
            root = Path(self._local_store.name)
            memory = Memory.from_config({
                "vector_store": {
                    "provider": "qdrant",
                    "config": {"collection_name": "tracemem", "path": str(root / "qdrant")},
                },
                "history_db_path": str(root / "history.db"),
                "llm": {"provider": "openai", "config": {"model": self.memory_model}},
                "embedder": {"provider": "openai", "config": {"model": self.embedding_model}},
            })
        self.memory = memory

        if answer_client is None:
            if not os.getenv("OPENAI_API_KEY"):
                raise RuntimeError("Mem0 answer model requires OPENAI_API_KEY")
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError('Install the Mem0 baseline: pip install -e ".[mem0]"') from exc
            answer_client = OpenAI()
        self.answer_client = answer_client

    def observe(self, turn: Turn, when: datetime, gold_candidates: list[Candidate] | None = None) -> None:
        if gold_candidates is not None:
            raise ValueError("Mem0 uses its own extraction; run with --condition end_to_end")
        if turn.id in self._observed:
            raise ValueError(f"duplicate turn: {turn.id}")
        # One write per turn, in harness order. Keep the speaker in the content:
        # all team members are dialogue participants, not the Mem0 assistant.
        self.memory.add(
            [{"role": "user", "content": f"{turn.speaker}: {turn.text}"}],
            user_id=self.user_id,
            metadata={
                "project_id": self.meta.project_id,
                "source_turn_id": turn.id,
                "session_id": session_of(turn.id),
                "speaker": turn.speaker,
                "scenario_time": when.isoformat(),
            },
            infer=True,
        )
        self._observed[turn.id] = turn

    def answer(self, question: SystemQuestion) -> Answer:
        raw = self.memory.search(
            question.text,
            filters={"user_id": self.user_id},
            top_k=self.top_k,
        )
        memories = []
        sources: set[str] = set()
        for row in _memory_rows(raw):
            content = row.get("memory")
            if not isinstance(content, str) or not content.strip():
                continue
            source = _source_turn(row)
            if source is not None and source not in self._observed:
                # Never pass unobserved references into the benchmark's answerer.
                continue
            if question.kind == "as_of":
                # A latest-state memory with no source time cannot be trusted as
                # evidence for an earlier checkpoint; avoid temporal leakage.
                if source is None or question.session is None:
                    continue
                if int(session_of(source)[1:]) > int(question.session[1:]):
                    continue
            if source is not None:
                sources.add(source)
            memories.append({"text": content, "source_turn_id": source})

        context_turn_ids = sorted(sources)
        if not memories:
            return Answer(status="none", context_turn_ids=context_turn_ids)

        response = self.answer_client.chat.completions.create(
            model=self.answer_model,
            response_format={"type": "json_object"},
            temperature=0,
            messages=[
                {"role": "system", "content": ANSWER_PROMPT},
                {"role": "user", "content": json.dumps({
                    "question": question.text,
                    "kind": question.kind,
                    "as_of_session": question.session,
                    "memories": memories,
                })},
            ],
        )
        try:
            output = json.loads(response.choices[0].message.content or "")
            status = output["status"]
            value = output.get("value")
            if status not in ("answer", "none", "conflict", "abstain"):
                raise ValueError("unknown answer status")
            if status == "answer" and (not isinstance(value, str) or not value.strip()):
                raise ValueError("answer has no value")
            if status != "answer":
                value = None
            requested = output.get("cited_turn_ids", [])
            if not isinstance(requested, list):
                requested = []
            cited = sorted({t for t in requested if isinstance(t, str) and t in sources})
        except (ValueError, TypeError, KeyError, AttributeError, IndexError):
            # Malformed model output must not be converted into a guessed answer.
            status, value, cited = "abstain", None, []

        api_usage = getattr(response, "usage", None)
        usage = Usage(
            calls=1,
            input_tokens=getattr(api_usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(api_usage, "completion_tokens", 0) or 0,
        )
        return Answer(
            status=status,
            value=value,
            cited_turn_ids=cited,
            context_turn_ids=context_turn_ids,
            usage=usage,
        )

    def fingerprint(self) -> str:
        """Only the observed turn sequence is mutable in this adapter."""
        turn_ids = list(self._observed)
        return hashlib.sha256(json.dumps(turn_ids).encode()).hexdigest()

    def describe(self) -> dict:
        try:
            sdk_version = version("mem0ai")
        except PackageNotFoundError:
            sdk_version = "injected-test-double"
        return {
            "provider": "mem0-oss",
            "mem0ai_version": sdk_version,
            "memory_model": self.memory_model,
            "answer_model": self.answer_model,
            "embedding_model": self.embedding_model,
            "top_k": self.top_k,
            "infer": True,
            "answer_prompt_sha256": hashlib.sha256(ANSWER_PROMPT.encode()).hexdigest(),
            "store_isolation": "unique user_id and temporary Qdrant/SQLite per scenario",
            "note": "Answer usage excludes Mem0's extraction, embedding and search calls",
        }


def make_mem0(meta: ScenarioMeta, gold: Any = None) -> Mem0System:
    """Factory for the benchmark registry; gold is intentionally never read."""
    if gold is not None:
        raise ValueError("Mem0 baseline must not receive the gold timeline")
    return Mem0System(meta, top_k=int(os.getenv("MEM0_TOP_K", "10")))
