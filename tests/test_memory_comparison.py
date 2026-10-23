"""Offline integration of the controlled TraceMem, ablation and native Mem0 arms."""

from __future__ import annotations

import ast
from copy import deepcopy
from datetime import datetime, timedelta
from importlib.metadata import PackageNotFoundError, version
import json
import tempfile

import pytest

from support import pilot, pilot_timeline
from tracemem import cli
from tracemem.eval import harness
from tracemem.eval.report import comparison_table
from tracemem.resolver import ModelReply, ResolverConfig, ResolverInputError
from tracemem.schema import Candidate, Record, SystemQuestion, Turn
from tracemem.systems import REGISTRY
from tracemem.systems import comparison


NAMES = ("tracemem-controlled", "tracemem-no-versions", "mem0-classic")
try:
    version("mem0ai")
    HAS_MEM0 = True
except PackageNotFoundError:
    HAS_MEM0 = False
needs_mem0 = pytest.mark.skipif(not HAS_MEM0, reason="install the optional mem0 extra to run the native SDK")
ARM_CASES = [pytest.param(name, marks=needs_mem0 if name == "mem0-classic" else ()) for name in NAMES]
GROUP_CASES = [pytest.param(NAMES[:2]), pytest.param(NAMES, marks=needs_mem0)]


@pytest.fixture(autouse=True)
def native_temp_within_test_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))


class OfflineComparisonClient:
    """Deterministic decisions from visible input, including Mem0's native update prompt."""

    def __init__(self, answer=None):
        self.calls = []
        self.answer_decision = answer or {"status": "abstain", "value": None, "cited_turn_ids": [], "text": ""}
        self.native_facts = []

    def complete(self, *, config, messages, response_format):
        self.calls.append({"config": config.model_dump(), "messages": deepcopy(messages),
                           "response_format": deepcopy(response_format)})
        if response_format["type"] == "json_object":
            # Mem0's pinned stock updater embeds the new facts as a Python list in
            # its final fenced block. Preserve each fact exactly; do not read gold.
            prompt = messages[-1]["content"]
            suffix = prompt.rsplit("The new retrieved facts are mentioned in the triple backticks.", 1)[1]
            facts = ast.literal_eval(suffix.split("```")[1].strip())
            self.native_facts.extend(facts)
            content = {"memory": [{"id": str(index), "event": "ADD", "text": fact}
                                  for index, fact in enumerate(facts)]}
        elif response_format["json_schema"]["name"] == "memory_answer":
            content = self.answer_decision
        else:
            evidence = json.loads(messages[1]["content"])
            candidate = evidence["candidate"]
            active = next((record for record in evidence["related"] if record["status"] == "active"), None)
            op = "ADD" if active is None else "KEEP" if active["value"] == candidate["value"] else "SUPERSEDE"
            content = {
                "op": op, "add_as": "active" if op == "ADD" else None,
                "targets": [] if active is None else [active["record_id"]],
                "source_turn_ids": candidate["source_turn_ids"], "reason": None,
                "rationale": "Offline visible-state fixture, not a semantic evaluation.",
            }
        return ModelReply(json.dumps(content), input_tokens=5, output_tokens=2)

    def answer_calls(self):
        return [call for call in self.calls
                if call["response_format"].get("json_schema", {}).get("name") == "memory_answer"]


@pytest.fixture
def offline_comparisons(monkeypatch):
    clients = []
    config = ResolverConfig(model="offline-comparison", max_attempts=2)

    def make_client():
        client = OfflineComparisonClient()
        clients.append(client)
        return client

    monkeypatch.setattr(ResolverConfig, "from_env", classmethod(lambda cls: config))
    monkeypatch.setattr(comparison, "make_client", make_client)
    monkeypatch.delenv("TRACEMEM_CONTEXT_BUDGET_BYTES", raising=False)
    return config, clients


def run_arm(name, scenario_ids=("pilot-01",)):
    return harness.run(REGISTRY[name], [pilot(sid) for sid in scenario_ids], "dev", condition="gold_candidates")


def question(kind="current", session=None):
    return SystemQuestion(question_id="opaque-question", scenario_id="pilot-01", kind=kind,
                          text="Which sentiment model was selected?", session=session)


def observe_candidate(system, turn_id, value, *, raw_suffix=""):
    turn = Turn(id=turn_id, speaker="Planner", text=f"We confirm {value}. {raw_suffix}")
    candidate = Candidate(candidate_id=f"model.sentiment@{turn_id}", project_id=system.meta.project_id,
                          item="model.sentiment", value=value, source_turn_ids=[turn_id],
                          speaker=turn.speaker, text=turn.text)
    index = int(turn_id.split("-T")[1])
    system.observe(turn, datetime(2026, 1, 1) + timedelta(minutes=index), gold_candidates=[candidate])
    return candidate


def close(system):
    cleanup = getattr(system, "close", None)
    if callable(cleanup):
        cleanup()


@pytest.mark.parametrize("names", GROUP_CASES)
def test_all_arms_share_candidates_model_and_comparison_protocol(names, offline_comparisons, tmp_path):
    config, clients = offline_comparisons
    results = [run_arm(name) for name in names]
    manifests = []
    for result, client in zip(results, clients):
        assert result.status == "completed" and result.uses_gold is False
        expected = [candidate.model_dump() for candidates in pilot_timeline("pilot-01").candidates_by_turn.values()
                    for candidate in candidates]
        assert [candidate.model_dump() for candidate in result.candidates["pilot-01"]] == expected
        folder = harness.write_run(result, tmp_path)
        manifests.append(json.loads((folder / "manifest.json").read_text(encoding="utf-8")))
        usage = json.loads((folder / "usage.json").read_text(encoding="utf-8"))
        calls = usage["resolver"]["total"]["calls"] + usage["answer"]["total"]["calls"]
        assert calls == len(client.calls)
        assert sum(usage[stage]["total"]["input_tokens"] for stage in ("resolver", "answer")) == calls * 5
        assert sum(usage[stage]["total"]["output_tokens"] for stage in ("resolver", "answer")) == calls * 2
    assert len(clients) == len(names)
    assert all(client.calls for client in clients)
    assert all(call["config"] == config.model_dump() for client in clients for call in client.calls)
    settings = [manifest["comparison"] for manifest in manifests]
    assert all(setting == settings[0] for setting in settings)
    assert settings[0]["model_config"] == config.model_dump()
    assert settings[0]["input_policy"] == "gold_candidates_only"
    assert settings[0]["context_budget_bytes"] == 12000
    assert settings[0]["candidate_hashes"]["pilot-01"]
    answer_calls = [call for client in clients for call in client.answer_calls()]
    assert answer_calls
    assert len({call["messages"][0]["content"] for call in answer_calls}) == 1
    assert all(call["response_format"] == answer_calls[0]["response_format"] for call in answer_calls)
    for call in answer_calls:
        payload = json.loads(call["messages"][1]["content"])
        assert set(payload) == {"question", "context", "allowed_source_turn_ids"}
        assert "item" not in payload["question"]
        assert len(payload["context"].encode("utf-8")) <= 12000


@pytest.mark.parametrize("name", ARM_CASES)
def test_each_scenario_receives_fresh_memory_and_model_client(name, offline_comparisons):
    _, clients = offline_comparisons
    result = run_arm(name, ("pilot-01", "pilot-02"))
    assert len(clients) == 2 and clients[0] is not clients[1]
    assert {candidate.project_id for candidate in result.candidates["pilot-01"]} == {pilot("pilot-01").project_id}
    for client in clients:
        first = next(call for call in client.calls if call not in client.answer_calls())
        if name == "mem0-classic":
            assert "Current memory is empty." in first["messages"][-1]["content"]
        else:
            assert json.loads(first["messages"][1]["content"])["related"] == []


@pytest.mark.parametrize("name", ARM_CASES)
def test_controlled_arms_refuse_end_to_end_without_calling_the_model(name, offline_comparisons):
    _, clients = offline_comparisons
    with pytest.raises(harness.RunAborted) as caught:
        harness.run(REGISTRY[name], [pilot("pilot-01")], "dev")
    assert caught.value.result.failure["error_type"] == "ResolverConfigError"
    assert "gold_candidates" in caught.value.result.failure["message"]
    assert all(not client.calls for client in clients)


@pytest.mark.parametrize("name", NAMES)
def test_factory_rejects_gold_timeline_instead_of_leaking_labels(name):
    with pytest.raises(ResolverInputError, match="gold"):
        comparison.factory(name)(pilot("pilot-01").meta(), pilot_timeline("pilot-01"))


@needs_mem0
def test_native_mem0_emits_native_events_without_forcing_resolver_labels(offline_comparisons, tmp_path):
    _, clients = offline_comparisons
    result = run_arm("mem0-classic")
    folder = harness.write_run(result, tmp_path)
    assert result.resolver_scores is None
    assert "pilot-01" not in result.operations
    assert not (folder / "resolver_scores.jsonl").exists()
    assert not (folder / "resolver_metrics.json").exists()
    assert clients[0].native_facts
    events = [json.loads(line) for line in (folder / "memory_events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(events) == len(result.candidates["pilot-01"])
    assert all(event["scenario_id"] == "pilot-01" for event in events)
    assert result.system_config["memory_policy"] == "mem0_classic_with_native_history"


def test_no_versions_discards_old_records_from_both_resolver_and_answer_context():
    config = ResolverConfig(model="offline-comparison")
    payloads = {}
    for name in ("tracemem-controlled", "tracemem-no-versions"):
        client = OfflineComparisonClient()
        system = comparison.make_system(name, pilot("pilot-01").meta(), config=config, client=client)
        try:
            observe_candidate(system, "S1-T1", "BERT")
            observe_candidate(system, "S1-T2", "DistilBERT")
            observe_candidate(system, "S1-T3", "RoBERTa")
            third_write = json.loads(client.calls[2]["messages"][1]["content"])
            system.answer(question("as_of", "S1"))
            answer_input = json.loads(client.answer_calls()[-1]["messages"][1]["content"])
            payloads[name] = third_write, answer_input, system.log.records()
        finally:
            close(system)
    versioned_write, versioned_answer, versioned_records = payloads["tracemem-controlled"]
    flat_write, flat_answer, flat_records = payloads["tracemem-no-versions"]
    assert {record["value"] for record in versioned_write["related"]} == {"BERT", "DistilBERT"}
    assert [record["value"] for record in flat_write["related"]] == ["DistilBERT"]
    assert "S1-T1" in versioned_answer["allowed_source_turn_ids"]
    assert flat_answer["allowed_source_turn_ids"] == ["S1-T3"]
    assert {record.value for record in versioned_records} == {"BERT", "DistilBERT", "RoBERTa"}
    assert [record.value for record in flat_records] == ["RoBERTa"]
    assert flat_records[0].supersedes == []


@pytest.mark.parametrize("name", ARM_CASES)
def test_answer_context_uses_same_byte_budget_and_never_raw_turn_audit(name):
    client = OfflineComparisonClient()
    system = comparison.make_system(name, pilot("pilot-01").meta(),
                                    config=ResolverConfig(model="offline-comparison"), client=client, budget_bytes=600)
    try:
        observe_candidate(system, "S1-T1", "BERT")
        # An observed turn without a candidate is audit text, not stored memory.
        system.observe(Turn(id="S1-T2", speaker="Planner", text="UNRETRIEVED_RAW_TURN_SENTINEL"),
                       datetime(2026, 1, 1, 0, 2), gold_candidates=[])
        answer = system.answer(question())
        payload = json.loads(client.answer_calls()[-1]["messages"][1]["content"])
        assert len(payload["context"].encode("utf-8")) <= 600
        assert "UNRETRIEVED_RAW_TURN_SENTINEL" not in json.dumps(payload)
        assert "S1-T2" not in payload["allowed_source_turn_ids"]
        assert answer.context_turn_ids == payload["allowed_source_turn_ids"]
        assert system.describe()["comparison"]["context_budget_bytes"] == 600
    finally:
        close(system)


def test_shared_answerer_rejects_citations_not_in_rendered_context():
    client = OfflineComparisonClient(answer={"status": "answer", "value": "BERT",
                                             "cited_turn_ids": ["S9-T9"], "text": ""})
    config = ResolverConfig(model="offline-comparison", max_attempts=2)
    record = Record(record_id="model.sentiment@S1-T1", project_id="p", item="model.sentiment", value="BERT",
                    status="active", source_turn_ids=["S1-T1"], speakers=["Planner"],
                    created_turn="S1-T1", created_at=datetime(2026, 1, 1))
    answer = comparison.SharedAnswerer(config, client).answer(question(), [record], {})
    assert answer.status == "abstain" and answer.cited_turn_ids == []
    assert answer.context_turn_ids == ["S1-T1"]
    assert answer.usage.calls == 2


def test_shared_context_budget_counts_utf8_bytes_and_omits_whole_oversized_entries():
    def record(turn, value):
        return Record(record_id=f"model.sentiment@{turn}", project_id="p", item="model.sentiment", value=value,
                      status="active", source_turn_ids=[turn], speakers=["Planner"],
                      created_turn=turn, created_at=datetime(2026, 1, 1))

    context, sources = comparison.answer_context([record("S1-T1", "BERT"), record("S1-T2", "汉" * 200)], 600)
    assert "BERT" in context and "汉" not in context
    assert len(context.encode("utf-8")) <= 600
    assert sources == ["S1-T1"]


def test_controlled_system_listing_does_not_initialize_models(monkeypatch, capsys):
    monkeypatch.delenv("TRACEMEM_RESOLVER_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def forbidden(*args, **kwargs):
        raise AssertionError("Listing systems must not initialize models or read model configuration")

    monkeypatch.setattr(comparison, "make_client", forbidden)
    monkeypatch.setattr(ResolverConfig, "from_env", forbidden)
    assert cli.main(["systems"]) == 0
    output = capsys.readouterr().out
    assert all(name in output for name in NAMES)
    assert all(REGISTRY[name].uses_gold is False for name in NAMES)


@pytest.mark.parametrize("allow_mixed", [False, True])
@pytest.mark.parametrize("change", ["model_config", "context_budget_bytes", "answer_prompt_hash", "candidate_hashes",
                                    "answer_validation_policy_hash", "reader", "temporal_read_policy"])
def test_comparison_refuses_runs_with_different_controlled_settings(change, allow_mixed, offline_comparisons, tmp_path):
    folders = [harness.write_run(run_arm(name), tmp_path) for name in NAMES[:2]]
    manifest_path = folders[1] / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if change == "model_config":
        manifest["comparison"][change]["model"] = "different-model"
    elif change == "context_budget_bytes":
        manifest["comparison"][change] = 1000
    elif change == "candidate_hashes":
        manifest["comparison"][change]["pilot-01"] = "different-candidate-sequence"
    else:
        manifest["comparison"][change] = "different-answer-prompt"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="comparison|differ|candidate"):
        comparison_table(folders, n=10, allow_mixed=allow_mixed)


@pytest.mark.parametrize("names", GROUP_CASES)
def test_matched_controlled_arms_can_be_compared(names, offline_comparisons, tmp_path):
    folders = [harness.write_run(run_arm(name), tmp_path) for name in names]
    output = comparison_table(folders, n=10)
    assert all(name in output for name in names)
    assert "uses gold labels" not in output
