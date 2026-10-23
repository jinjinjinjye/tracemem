"""Pinned, gold-candidate adapter around the genuine Mem0 classic update engine.

The SDK owns update prompting, UUID mapping, mutation and SQLite history. Only
extraction, matching and provider transport are controlled for this experiment.
No default SDK clients, embeddings, external stores or telemetry are constructed.
"""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
import hashlib
from importlib import metadata
import json
import os
import re
import sqlite3
from tempfile import TemporaryDirectory
from threading import RLock
from types import SimpleNamespace

from tracemem.resolver import (
    CompletionClient, FatalModelError, ResolverConfig, ResolverConfigError,
    ResolverError, ResolverInputError, RetryableModelError,
)
from tracemem.schema import Candidate, Record, ScenarioMeta, TURN_ID, Usage


MEM0_VERSION = "1.0.11"
MEM0_COMMIT = "144627c4ce5bc4db6acac17cbd158065f2b27a8d"
EXTRACTION_PROMPT = "Return the supplied TraceMem candidate unchanged as a JSON fact."
_SDK_LOCK = RLock()


def _load_sdk(directory: str):
    try:
        installed = metadata.version("mem0ai")
    except metadata.PackageNotFoundError:
        raise ResolverConfigError('Install the optional baseline with pip install -e ".[mem0]"') from None
    if installed != MEM0_VERSION:
        raise ResolverConfigError(f"This baseline requires mem0ai=={MEM0_VERSION}")
    # SDK imports create a setup file. Isolate it even when no Memory.__init__ is
    # used, and restore the caller's environment after the lazy import.
    with _SDK_LOCK:
        previous = {key: os.environ.get(key) for key in ("MEM0_DIR", "MEM0_TELEMETRY")}
        os.environ.update(MEM0_DIR=directory, MEM0_TELEMETRY="false")
        try:
            from mem0.memory import main
            from mem0.configs.base import MemoryConfig
            from mem0.configs.prompts import get_update_memory_messages
            from mem0.memory.storage import SQLiteManager
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    return main, MemoryConfig, SQLiteManager, get_update_memory_messages


@contextmanager
def _no_telemetry(module):
    # Also cover processes that imported Mem0 before this adapter with telemetry
    # enabled. Restore the SDK function, rather than disabling another user's
    # telemetry singleton or changing its configuration permanently.
    with _SDK_LOCK:
        capture = module.capture_event
        module.capture_event = lambda *args, **kwargs: None
        try:
            yield
        finally:
            module.capture_event = capture


class _AllItemStore:
    """Controlled same-item matching; vectors and the SDK's limit=5 are unused."""

    def __init__(self):
        self.data: dict[str, dict] = {}
        self.matched: list[str] = []

    def search(self, *, query, vectors, limit, filters):
        self.matched = [key for key, payload in self.data.items()
                        if all(payload.get(name) == value for name, value in filters.items())]
        return [SimpleNamespace(id=key, payload=deepcopy(self.data[key])) for key in self.matched]

    def insert(self, *, vectors, ids, payloads):
        if len(ids) != len(payloads) or len(ids) != len(vectors):
            raise ValueError("inconsistent local store batch")
        for key, payload in zip(ids, payloads):
            if key in self.data:
                raise ValueError("duplicate native memory id")
            self.data[key] = deepcopy(payload)

    def get(self, vector_id):
        payload = self.data.get(vector_id)
        return SimpleNamespace(id=vector_id, payload=deepcopy(payload)) if payload is not None else None

    def update(self, *, vector_id, vector, payload):
        if vector_id not in self.data:
            raise ValueError("unknown native memory id")
        self.data[vector_id] = deepcopy(payload)

    def delete(self, vector_id):
        del self.data[vector_id]


class _UnusedEmbedding:
    def embed(self, text, memory_action="add"):
        return [0.0]


class _UpdateBridge:
    def __init__(self, backend):
        self.backend = backend
        self.candidate = None
        self.error = None
        self.actions = None
        self.extracted = False

    def reset(self, candidate):
        self.candidate, self.error, self.actions, self.extracted = candidate, None, None, False

    def _validate(self, content):
        try:
            data = json.loads(content)
        except (ValueError, TypeError):
            raise ValueError("update response must be JSON") from None
        if not isinstance(data, dict) or set(data) != {"memory"} or not isinstance(data["memory"], list):
            raise ValueError("update response must contain a memory action list")
        known = {str(index) for index in range(len(self.backend._store.matched))}
        targeted = set()
        for action in data["memory"]:
            if not isinstance(action, dict) or set(action) - {"id", "text", "event", "old_memory"}:
                raise ValueError("invalid memory action fields")
            if not isinstance(action.get("text"), str) or not action["text"].strip():
                raise ValueError("memory action text must be nonempty")
            event, key = action.get("event"), action.get("id")
            if event not in ("ADD", "UPDATE", "DELETE", "NONE") or not isinstance(key, str):
                raise ValueError("memory action requires a known event and string id")
            if event != "ADD":
                if key not in known or key in targeted:
                    raise ValueError("memory actions must target distinct supplied memory ids")
                targeted.add(key)
            if event == "UPDATE" and not isinstance(action.get("old_memory"), str):
                raise ValueError("UPDATE requires old_memory text")
            if "old_memory" in action and not isinstance(action["old_memory"], str):
                raise ValueError("old_memory must be text")
        return data["memory"]

    def generate_response(self, *, messages, response_format):
        if not self.extracted:
            if len(messages) != 2 or messages[0].get("content") != EXTRACTION_PROMPT:
                self.error = FatalModelError("Unexpected pinned Mem0 extraction protocol")
                raise self.error
            self.extracted = True
            # Preserve the quote and speaker: a suggestion must not be flattened
            # into an assertion merely by supplying the gold candidate's value.
            return json.dumps({"facts": [json.dumps(self.candidate.model_dump(), ensure_ascii=False, sort_keys=True)]})
        if len(messages) != 1 or messages[0].get("role") != "user" or self.actions is not None:
            self.error = FatalModelError("Unexpected pinned Mem0 update protocol")
            raise self.error
        original = deepcopy(messages)
        request = deepcopy(original)
        detail = "no valid update decision"
        for attempt in range(1, self.backend.config.max_attempts + 1):
            usage = self.backend._usage
            self.backend._usage = usage.model_copy(update={"calls": usage.calls + 1})
            try:
                reply = self.backend.client.complete(config=self.backend.config, messages=request,
                                                     response_format=deepcopy(response_format))
            except (RetryableModelError, TimeoutError):
                detail = "transient model failure"
                continue
            except (FatalModelError, ResolverConfigError, ResolverInputError) as error:
                self.error = error
                raise
            except Exception:
                self.error = FatalModelError("Mem0 update client failed unexpectedly")
                raise self.error from None
            usage = self.backend._usage
            self.backend._usage = usage.model_copy(update={
                "input_tokens": usage.input_tokens + reply.input_tokens,
                "output_tokens": usage.output_tokens + reply.output_tokens,
            })
            if reply.refused or reply.finish_reason != "stop":
                detail = "model refused or did not finish the update response"
                continue
            try:
                self.actions = self._validate(reply.content)
                return json.dumps({"memory": self.actions})
            except ValueError as error:
                detail = str(error)
                request = original + [{"role": "user", "content":
                    f"The previous JSON was invalid: {detail}. Return a complete corrected memory action list."}]
        self.error = ResolverError(self.candidate.candidate_id, self.backend.config.max_attempts, detail)
        raise self.error


class Mem0Backend:
    """Native classic Mem0 update/storage/history under controlled candidate input.

    Construction intentionally injects dependencies instead of Memory.__init__:
    no unused default providers are instantiated. SDK methods themselves are not
    copied, and an exact package pin plus offline tests guard this internal seam.
    """

    def __init__(self, meta: ScenarioMeta, config: ResolverConfig, client: CompletionClient):
        self.meta, self.config, self.client = meta, config, client
        self._temp = TemporaryDirectory(prefix="tracemem-mem0-")
        try:
            self._sdk, MemoryConfig, SQLiteManager, update_prompt = _load_sdk(self._temp.name)
            self._store = _AllItemStore()
            self._usage = Usage()
            self._bridge = _UpdateBridge(self)
            self._memory = self._sdk.Memory.__new__(self._sdk.Memory)
            self._memory.config = MemoryConfig(history_db_path=":memory:", custom_fact_extraction_prompt=EXTRACTION_PROMPT,
                                               llm={"provider": "openai", "config": {"model": config.model}})
            self._memory.custom_fact_extraction_prompt = EXTRACTION_PROMPT
            self._memory.custom_update_memory_prompt = None
            self._memory.embedding_model = _UnusedEmbedding()
            self._memory.vector_store = self._store
            self._memory.llm = self._bridge
            self._memory.db = SQLiteManager(":memory:")
            self._memory.collection_name = "controlled-candidate-memory"
            self._memory.api_version = self._memory.config.version
            self._memory.reranker, self._memory.graph, self._memory.enable_graph = None, None, False
            self._update_hash = hashlib.sha256(update_prompt([], []).encode()).hexdigest()
        except Exception:
            self._temp.cleanup()
            raise
        self._scope = hashlib.sha256(f"{meta.scenario_id}/{meta.project_id}".encode()).hexdigest()
        self._events: list[dict] = []
        self._provenance: dict[str, dict] = {}
        self._items: dict[str, str] = {}
        self._seen: set[str] = set()
        self._closed = False
        self._last_when = None

    def _history(self, memory_id):
        with _no_telemetry(self._sdk):
            return self._memory.history(memory_id)

    def _validate_candidate(self, candidate, when):
        if self._closed:
            raise ResolverInputError("Mem0 backend is closed")
        sources = candidate.source_turn_ids
        if candidate.project_id != self.meta.project_id or not candidate.item or not candidate.value.strip() or not candidate.text.strip():
            raise ResolverInputError("Mem0 candidate must contain this project's item, value and source text")
        if any(re.fullmatch(TURN_ID, source) is None for source in sources) or len(sources) != len(set(sources)):
            raise ResolverInputError("Mem0 candidate sources must be unique valid turn ids")
        if candidate.candidate_id != f"{candidate.item}@{sources[0]}" or candidate.candidate_id in self._seen:
            raise ResolverInputError("Mem0 candidate id must identify one new item and current turn")
        if not isinstance(when, datetime) or self._last_when is not None and when < self._last_when:
            raise ResolverInputError("Mem0 candidate times must be chronological")

    def add(self, candidate: Candidate, when: datetime) -> None:
        self._validate_candidate(candidate, when)
        self._seen.add(candidate.candidate_id)
        self._last_when = when
        before = self._usage
        saved_store = deepcopy(self._store.data)
        snapshot = sqlite3.connect(":memory:")
        self._memory.db.connection.backup(snapshot)
        self._bridge.reset(candidate)
        status, detail, actions = "applied", None, []
        try:
            with _no_telemetry(self._sdk):
                result = self._memory.add(
                    [{"role": "user", "content": candidate.text}], user_id=self._scope,
                    run_id=candidate.item, metadata={"item": candidate.item, "created_at": when.isoformat()}, infer=True,
                )
            if self._bridge.error is not None:
                raise self._bridge.error
            if self._bridge.actions is None:
                raise FatalModelError("Mem0 did not execute its expected update stage")
            actions = deepcopy(self._bridge.actions)
            returned = result.get("results") if isinstance(result, dict) else None
            mutations = [action for action in actions if action["event"] != "NONE"]
            if not isinstance(returned, list) or len(returned) != len(mutations):
                raise FatalModelError("Mem0 did not apply its complete validated action batch")
            staged = []
            for action, entry in zip(mutations, returned):
                if entry.get("event") != action["event"] or entry.get("memory") != action["text"]:
                    raise FatalModelError("Mem0 mutation results disagree with the validated actions")
                memory_id = entry.get("id")
                if not isinstance(memory_id, str):
                    raise FatalModelError("Mem0 returned an invalid native memory id")
                if action["event"] != "ADD" and memory_id != self._store.matched[int(action["id"])]:
                    raise FatalModelError("Mem0 mutated an unexpected native memory id")
                history = self._history(memory_id)
                fresh = [entry for entry in history if entry["id"] not in self._provenance]
                if len(fresh) != 1 or fresh[0]["event"] != action["event"]:
                    raise FatalModelError("Mem0 history does not confirm the complete action batch")
                history_entry = fresh[0]
                expected_value = None if action["event"] == "DELETE" else action["text"]
                if history_entry["new_memory"] != expected_value:
                    raise FatalModelError("Mem0 history disagrees with the validated memory text")
                current = self._store.data.get(memory_id)
                if (action["event"] == "DELETE" and current is not None) or (
                    action["event"] != "DELETE" and (current is None or current.get("data") != expected_value)
                ):
                    raise FatalModelError("Mem0 current storage disagrees with the action batch")
                prior = [self._provenance[row["id"]] for row in history if row["id"] in self._provenance]
                sources = list(candidate.source_turn_ids)
                source_speakers = {source: "" for source in sources}
                source_speakers[sources[0]] = candidate.speaker
                for provenance in prior:
                    for source, speaker in zip(provenance["sources"], provenance["speakers"]):
                        if source not in sources:
                            sources.append(source)
                        if not source_speakers.get(source):
                            source_speakers[source] = speaker
                staged.append((history_entry["id"], memory_id, {
                    "turn": candidate.source_turn_ids[0], "when": when, "sources": sources,
                    "speakers": [source_speakers[source] for source in sources], "item": candidate.item,
                }))
                entry["history_id"] = history_entry["id"]
            for history_id, memory_id, provenance in staged:
                self._provenance[history_id] = provenance
                self._items[memory_id] = candidate.item
            actions = deepcopy(returned) + [deepcopy(action) for action in actions if action["event"] == "NONE"]
            status = "applied" if mutations else "no_change"
        except Exception as error:
            self._store.data = saved_store
            snapshot.backup(self._memory.db.connection)
            if isinstance(error, (ResolverError, FatalModelError, ResolverInputError, ResolverConfigError)):
                failure = error
            else:
                failure = FatalModelError("Mem0 native update failed unexpectedly")
            status = "generation_failed" if isinstance(failure, ResolverError) else "aborted"
            detail = failure.detail if isinstance(failure, ResolverError) else str(failure)
            raise failure from None
        finally:
            snapshot.close()
            usage = {key: getattr(self._usage, key) - getattr(before, key)
                     for key in ("calls", "input_tokens", "output_tokens")}
            self._events.append({"candidate_id": candidate.candidate_id, "turn_id": candidate.source_turn_ids[0],
                                 "item": candidate.item, "status": status, "actions": actions,
                                 "attempts": usage["calls"], "usage": usage, "detail": detail})

    def records(self) -> list[Record]:
        """Expose current SDK memories plus every native history event, including deletes.

        The sidecar supplies only source/time/item attribution. Text always comes
        from SDK current payloads or Memory.history(), never the candidate audit.
        """
        result = []
        for memory_id, item in self._items.items():
            history = self._history(memory_id)
            ordered = sorted(history, key=lambda row: self._provenance[row["id"]]["when"])
            for entry in ordered:
                provenance = self._provenance[entry["id"]]
                value = json.dumps({"mem0_history": entry["event"], "before": entry["old_memory"],
                                    "after": entry["new_memory"]}, ensure_ascii=False)
                result.append(self._record(f"mem0-history:{entry['id']}", item, value, provenance))
            current = self._store.data.get(memory_id)
            if current is not None:
                provenance = self._provenance[ordered[-1]["id"]]
                result.append(self._record(f"mem0-current:{memory_id}", item,
                                           f"Current Mem0 memory: {current['data']}", provenance))
        return sorted(result, key=lambda record: (record.created_at, record.record_id))

    def _record(self, record_id, item, value, provenance):
        return Record(record_id=record_id, project_id=self.meta.project_id, item=item, value=value,
                      status=None, source_turn_ids=list(provenance["sources"]), speakers=list(provenance["speakers"]),
                      created_turn=provenance["turn"], created_at=provenance["when"], supersedes=[])

    def events(self) -> list[dict]:
        return deepcopy(self._events)

    def usage(self) -> Usage:
        return self._usage

    def describe(self) -> dict:
        return {"backend": "Mem0 classic OSS", "sdk_version": MEM0_VERSION, "sdk_commit": MEM0_COMMIT,
                "model_config": self.config.model_dump(), "client": type(self.client).__name__,
                "update_prompt_hash": self._update_hash,
                "extraction_prompt_hash": hashlib.sha256(EXTRACTION_PROMPT.encode()).hexdigest(),
                "infer": True, "extraction": "identity over supplied candidates; no extraction model call",
                "matching": "all current memories of same item; SDK top-five/vector ranking bypassed",
                "history": "all native Memory.history events, including UPDATE and DELETE, plus current memories",
                "storage": "isolated in-memory controlled vector store and native SQLite history",
                "initialization": "native Memory methods with injected dependencies; no default SDK clients",
                "telemetry": False}

    def fingerprint(self) -> str:
        data = {"current": self._store.data,
                "history": {key: self._history(key) for key in sorted(self._items)}}
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()

    def close(self):
        if not self._closed:
            self._memory.close()
            self._closed = True
            self._temp.cleanup()
