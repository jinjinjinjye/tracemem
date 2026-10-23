"""Actual pinned Mem0 SDK execution with scripted model replies and no network."""

from copy import deepcopy
from datetime import datetime, timedelta
from importlib import metadata
import json
import os
import socket
import tempfile

import pytest

from tracemem.resolver import FatalModelError, ModelReply, ResolverConfig, ResolverConfigError, ResolverError, RetryableModelError
from tracemem.schema import Candidate, ScenarioMeta, Usage
from tracemem.systems import mem0_baseline
from tracemem.systems.mem0_baseline import Mem0Backend


class Client:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append({**kwargs, "messages": deepcopy(kwargs["messages"])})
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def response(event="ADD", text="BERT is confirmed", key="0", old=None, tokens=(7, 3)):
    action = {"id": key, "text": text, "event": event}
    if old is not None:
        action["old_memory"] = old
    return ModelReply(json.dumps({"memory": [action]}), input_tokens=tokens[0], output_tokens=tokens[1])


def candidate(number=1, *, item="model.main", value="BERT", text=None):
    turn = f"S1-T{number}"
    return Candidate(candidate_id=f"{item}@{turn}", project_id="synthetic-project", item=item, value=value,
                     source_turn_ids=[turn], speaker="Speaker", text=text or f"We confirm {value}.")


def time(number):
    return datetime(2026, 1, 5, 10) + timedelta(minutes=number)


@pytest.fixture(autouse=True)
def no_network(monkeypatch, tmp_path):
    def blocked(*args, **kwargs):
        raise AssertionError("Mem0 offline tests must not open network connections")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    # Windows sandbox's default OS temp directory is not writable by Python.
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))


@pytest.fixture
def make_backend():
    try:
        version = metadata.version("mem0ai")
    except metadata.PackageNotFoundError:
        pytest.skip("optional mem0ai SDK not installed")
    if version != mem0_baseline.MEM0_VERSION:
        pytest.skip("offline native SDK tests require the pinned Mem0 version")
    opened = []

    def create(*replies, max_attempts=2, meta=None):
        client = Client(*replies)
        config = ResolverConfig(model="offline-shared-model", timeout_seconds=12.0, max_attempts=max_attempts,
                                max_completion_tokens=678, temperature=0.3)
        backend = Mem0Backend(meta or ScenarioMeta(scenario_id="fixture", project_id="synthetic-project"), config, client)
        opened.append(backend)
        return backend, client
    yield create
    for backend in opened:
        backend.close()


def add(backend, number=1, **kwargs):
    backend.add(candidate(number, **kwargs), time(number))


def test_native_add_update_none_delete_keep_full_history(make_backend):
    backend, client = make_backend(response(), response("UPDATE", "DistilBERT is confirmed", old="BERT is confirmed"),
                                   response("NONE", "DistilBERT is confirmed"), response("DELETE", "DistilBERT is confirmed"))
    add(backend)
    native_id = next(iter(backend._store.data))
    add(backend, 2, value="DistilBERT")
    add(backend, 3, value="DistilBERT")
    add(backend, 4, value="DistilBERT")
    assert backend._store.data == {}
    history = backend._memory.history(native_id)
    assert {row["event"] for row in history} == {"ADD", "UPDATE", "DELETE"}
    records = backend.records()
    assert len(records) == 3
    assert {json.loads(record.value)["mem0_history"] for record in records} == {"ADD", "UPDATE", "DELETE"}
    assert any(json.loads(record.value)["before"] == "BERT is confirmed" for record in records)
    assert {record.created_turn for record in records} == {"S1-T1", "S1-T2", "S1-T4"}
    assert all(record.status is None and record.supersedes == [] for record in records)
    assert [event["status"] for event in backend.events()] == ["applied", "applied", "no_change", "applied"]
    assert backend.usage() == Usage(calls=4, input_tokens=28, output_tokens=12)
    assert len(client.calls) == 4  # identity extraction never invokes the model


def test_actual_sdk_add_is_used_with_infer_enabled(make_backend, monkeypatch):
    backend, _ = make_backend(response())
    original = backend._sdk.Memory.add
    calls = []
    def spy(self, *args, **kwargs):
        calls.append(kwargs)
        return original(self, *args, **kwargs)
    monkeypatch.setattr(backend._sdk.Memory, "add", spy)
    add(backend)
    assert calls[0]["infer"] is True
    assert calls[0]["run_id"] == "model.main"


def test_native_prompt_receives_same_candidate_quote_and_exact_model_config(make_backend):
    backend, client = make_backend(response())
    add(backend, text="Maybe we could try BERT?")
    request, = client.calls
    assert request["config"] is backend.config
    assert request["response_format"] == {"type": "json_object"}
    prompt = request["messages"][0]["content"]
    assert "Maybe we could try BERT?" in prompt
    assert "source_turn_ids" in prompt and "Speaker" in prompt
    assert "UPDATE" in prompt and "DELETE" in prompt
    assert backend.describe()["model_config"] == backend.config.model_dump()
    assert len(backend.describe()["update_prompt_hash"]) == 64


def test_same_item_matching_is_explicitly_not_limited_to_five(make_backend):
    backend, client = make_backend(*(response(text=f"memory-{n}") for n in range(8)))
    for index in range(1, 9):
        add(backend, index)
    prompt = client.calls[-1]["messages"][0]["content"]
    assert all(f"memory-{n}" in prompt for n in range(7))
    assert len(backend._store.matched) == 7
    assert "top-five" in backend.describe()["matching"]


def test_matching_is_scoped_to_item_and_new_backend_has_no_prior_state(make_backend):
    backend, client = make_backend(response(text="main choice"), response(text="other choice"),
                                   response("UPDATE", "main revision", old="main choice"))
    add(backend)
    add(backend, 2, item="model.other")
    add(backend, 3)
    prompt = client.calls[-1]["messages"][0]["content"]
    assert "main choice" in prompt and "other choice" not in prompt
    assert {entry["data"] for entry in backend._store.data.values()} == {"main revision", "other choice"}
    fresh, _ = make_backend()
    assert fresh.records() == [] and fresh.usage() == Usage()


@pytest.mark.parametrize("failure", [TimeoutError(), RetryableModelError("offline transient"), ModelReply("broken", 11, 2)])
def test_retries_count_calls_and_reported_tokens_without_repeating_writes(make_backend, failure):
    backend, _ = make_backend(failure, response())
    add(backend)
    assert len(backend._store.data) == 1
    expected = Usage(calls=2, input_tokens=18, output_tokens=5) if isinstance(failure, ModelReply) else Usage(calls=2, input_tokens=7, output_tokens=3)
    assert backend.usage() == expected
    assert backend.events()[0]["attempts"] == 2


def test_whole_action_batch_validates_before_any_mutation(make_backend):
    invalid = ModelReply(json.dumps({"memory": [
        {"id": "0", "text": "must not be stored", "event": "ADD"},
        {"id": "missing", "text": "unknown target", "event": "DELETE"},
    ]}))
    backend, _ = make_backend(invalid, invalid)
    before = backend.fingerprint()
    with pytest.raises(ResolverError):
        add(backend)
    assert backend.fingerprint() == before and backend.records() == []
    assert backend.events()[0]["status"] == "generation_failed"


def test_native_swallowing_does_not_hide_fatal_provider_error(make_backend):
    backend, _ = make_backend(FatalModelError("offline authentication failure"))
    before = backend.fingerprint()
    with pytest.raises(FatalModelError, match="authentication"):
        add(backend)
    assert backend.fingerprint() == before
    assert backend.events()[0]["status"] == "aborted"
    assert backend.usage().calls == 1


def test_native_partial_storage_failure_rolls_back_all_mutations_and_history(make_backend, monkeypatch):
    batch = ModelReply(json.dumps({"memory": [
        {"id": "0", "text": "first", "event": "ADD"},
        {"id": "1", "text": "second", "event": "ADD"},
    ]}))
    backend, _ = make_backend(batch)
    original = backend._store.insert
    calls = 0
    def insert(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("offline insertion defect")
        return original(**kwargs)
    monkeypatch.setattr(backend._store, "insert", insert)
    before = backend.fingerprint()
    with pytest.raises(FatalModelError, match="complete validated action batch"):
        add(backend)
    assert backend.fingerprint() == before and backend.records() == []
    assert backend._memory.db.connection.execute("select count(*) from history").fetchone()[0] == 0


def test_no_mutation_if_existing_memories_receive_invalid_batch(make_backend):
    invalid = ModelReply(json.dumps({"memory": [
        {"id": "0", "text": "changed", "event": "UPDATE", "old_memory": "BERT is confirmed"},
        {"id": "0", "text": "BERT is confirmed", "event": "DELETE"},
    ]}))
    backend, _ = make_backend(response(), invalid, invalid)
    add(backend)
    before = backend.fingerprint()
    with pytest.raises(ResolverError):
        add(backend, 2)
    assert backend.fingerprint() == before
    assert len(backend._store.data) == 1


def test_records_use_sdk_text_and_history_not_candidate_audit(make_backend):
    backend, _ = make_backend(response(text="native memory summary"))
    add(backend, text="private audit quote which must not appear in returned records")
    records = backend.records()
    assert len(records) == 2
    assert all("native memory summary" in record.value for record in records)
    assert all("private audit quote" not in record.value for record in records)
    before = backend.fingerprint()
    records[0].source_turn_ids.append("S1-T99")
    assert "S1-T99" not in backend.records()[0].source_turn_ids
    assert backend.fingerprint() == before


def test_updated_memory_provenance_keeps_source_speakers_in_turn_order(make_backend):
    backend, _ = make_backend(response(), response("UPDATE", "revised memory", old="BERT is confirmed"))
    backend.add(candidate(1).model_copy(update={"speaker": "First"}), time(1))
    backend.add(candidate(2).model_copy(update={"speaker": "Second"}), time(2))
    current = next(record for record in backend.records() if record.record_id.startswith("mem0-current:"))
    assert current.source_turn_ids == ["S1-T2", "S1-T1"]
    assert current.speakers == ["Second", "First"]


def test_event_snapshots_and_reading_do_not_change_memory(make_backend):
    backend, _ = make_backend(response())
    add(backend)
    before = backend.fingerprint()
    events = backend.events()
    events[0]["actions"][0]["memory"] = "tampered"
    events[0]["usage"]["calls"] = 999
    assert backend.events()[0]["usage"]["calls"] == 1
    assert backend.events()[0]["actions"][0]["memory"] == "BERT is confirmed"
    backend.records()
    assert backend.fingerprint() == before


def test_import_environment_is_restored_and_existing_telemetry_function_is_not_called(make_backend, monkeypatch):
    monkeypatch.setenv("MEM0_DIR", "caller-setting")
    monkeypatch.setenv("MEM0_TELEMETRY", "true")
    backend, _ = make_backend(response())
    assert os.environ["MEM0_DIR"] == "caller-setting"
    assert os.environ["MEM0_TELEMETRY"] == "true"
    def forbidden(*args, **kwargs):
        raise AssertionError("already-imported SDK telemetry must not run")
    monkeypatch.setattr(backend._sdk, "capture_event", forbidden)
    add(backend)
    backend.records()
    backend.fingerprint()
    assert backend._sdk.capture_event is forbidden


def test_wrong_sdk_version_fails_before_import_or_model_call(monkeypatch):
    monkeypatch.setattr(mem0_baseline.metadata, "version", lambda name: "2.2.1")
    with pytest.raises(ResolverConfigError, match="1.0.11"):
        Mem0Backend(ScenarioMeta(scenario_id="test", project_id="synthetic-project"), ResolverConfig(model="offline"), Client())


def test_close_releases_native_sqlite_and_is_idempotent(make_backend):
    backend, _ = make_backend()
    path = backend._temp.name
    backend.close()
    backend.close()
    assert backend._memory.db.connection is None
    assert not os.path.exists(path)
