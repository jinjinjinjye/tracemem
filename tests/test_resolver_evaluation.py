"""Resolver scoring integration, using public development fixtures and offline models."""

from __future__ import annotations

import json
import socket
import sys

import pytest

from support import DEV, PILOT_IDS, pilot, pilot_timeline
from tracemem import cli, systems
from tracemem.eval import harness
from tracemem.resolver import FatalModelError, LLMResolver, ModelReply, ResolverConfig
from tracemem.schema import Answer
from tracemem.systems.base import SystemSpec


ARTIFACTS = {"resolver_scores.jsonl", "resolver_metrics.json", "resolver_analysis.jsonl"}
SYSTEM = "pipeline-resolver-dev"


def json_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def gold_count(scenario_id):
    return sum(len(ops) for ops in pilot_timeline(scenario_id).ops_by_turn.values())


def gold_run(scenario_ids=("pilot-01",), condition="gold_candidates"):
    return harness.run(systems.REGISTRY["pipeline-gold"], [pilot(sid) for sid in scenario_ids], "dev",
                       condition=condition)


class ProposalsClient:
    """Deliberately imperfect decisions, with optional malformed/fatal numbered calls."""

    def __init__(self, actions=None):
        self.actions = actions or {}
        self.calls = 0
        self.payloads = []

    def complete(self, *, config, messages, response_format):
        self.calls += 1
        payload = json.loads(messages[1]["content"])
        self.payloads.append(payload)
        action = self.actions.get(self.calls)
        if isinstance(action, Exception):
            raise action
        if isinstance(action, ModelReply):
            return action
        candidate = payload["candidate"]
        return ModelReply(json.dumps({
            "op": "ADD", "add_as": "proposed", "targets": [],
            "source_turn_ids": candidate["source_turn_ids"], "reason": None,
            "rationale": "Offline fixture always proposes the extracted value.",
        }), input_tokens=7, output_tokens=3)


def install_clients(monkeypatch, client_factory=ProposalsClient):
    clients = []

    def from_env(cls):
        client = client_factory()
        clients.append(client)
        return cls(ResolverConfig(model="offline-evaluation-fixture", max_attempts=2), client)

    monkeypatch.setattr(LLMResolver, "from_env", classmethod(from_env))
    return clients


def test_gold_pipeline_has_perfect_resolver_scores_on_all_development_pilots(tmp_path):
    result = gold_run(PILOT_IDS)
    assert len(result.resolver_scores) == sum(gold_count(sid) for sid in PILOT_IDS)
    assert {row["scenario_id"] for row in result.resolver_scores} == set(PILOT_IDS)
    folder = harness.write_run(result, tmp_path)
    summary = json.loads((folder / "resolver_metrics.json").read_text(encoding="utf-8"))
    assert summary["schema_version"] == 1 and summary["condition"] == "gold_candidates"
    count = summary["counts"]["gold_candidates"]
    assert count == summary["counts"]["emitted_operations"] == summary["counts"]["applied_operations"]
    assert count == len(result.resolver_scores)
    assert all(summary["counts"][key] == 0 for key in (
        "rejected_operations", "generation_failures", "missing_operations", "extra_predictions",
    ))
    for name in ("label_accuracy", "exact_operation_accuracy", "state_accuracy", "targets_accuracy",
                 "sources_accuracy", "targeted_targets_accuracy"):
        metric = summary["metrics"][name]
        assert metric["value"] == 1.0 and metric["n"] > 0, name
        assert metric["numerator"] == metric["n"], name
    for name in ("generation_failure_rate", "missing_operation_rate", "invalid_operation_rate"):
        assert summary["metrics"][name]["value"] == 0.0, name
    assert summary["macro_f1"]["value"] == summary["micro_f1"]["value"] == 1.0
    assert set(summary["labels"]) == {"ADD-active", "ADD-proposed", "KEEP", "SUPERSEDE", "FLAG"}
    for label in summary["labels"].values():
        assert label["support"] > 0
        assert label["precision"]["value"] == label["recall"]["value"] == label["f1"]["value"] == 1.0
    assert not any(summary["error_counts"].values())
    assert json_lines(folder / "resolver_scores.jsonl") == result.resolver_scores
    assert json_lines(folder / "resolver_analysis.jsonl") == []


def test_recoverable_model_failure_and_wrong_labels_remain_in_scoring_denominators(monkeypatch, tmp_path):
    bad = ModelReply("invalid JSON", input_tokens=11, output_tokens=2)
    clients = install_clients(monkeypatch, lambda: ProposalsClient({1: bad, 2: bad}))
    result = harness.run(systems.REGISTRY[SYSTEM], [pilot("pilot-01")], "dev", condition="gold_candidates")
    count = gold_count("pilot-01")
    assert result.status == "completed" and len(result.resolver_scores) == count
    folder = harness.write_run(result, tmp_path)
    summary = json.loads((folder / "resolver_metrics.json").read_text(encoding="utf-8"))
    assert summary["counts"]["gold_candidates"] == count
    assert summary["counts"]["generation_failures"] == 1
    assert summary["counts"]["missing_operations"] == 1
    assert summary["counts"]["emitted_operations"] == count - 1
    assert summary["counts"]["applied_operations"] == count - 1
    assert summary["counts"]["rejected_operations"] == 0
    expected_correct_labels = sum(op.op == "ADD" and op.add_as == "proposed"
                                  for ops in pilot_timeline("pilot-01").ops_by_turn.values() for op in ops)
    assert summary["metrics"]["label_accuracy"] == {
        "value": expected_correct_labels / count, "n": count, "numerator": expected_correct_labels,
    }
    assert summary["metrics"]["generation_failure_rate"] == {"value": 1 / count, "n": count, "numerator": 1}
    assert summary["metrics"]["invalid_operation_rate"] == {"value": 0.0, "n": count - 1, "numerator": 0}
    assert summary["metrics"]["state_accuracy"]["value"] < 1.0
    rows = json_lines(folder / "resolver_scores.jsonl")
    assert rows == result.resolver_scores
    assert len({row["candidate_id"] for row in rows}) == count
    assert rows[0]["status"] == "generation_failed"
    assert rows[0]["predicted"] is None
    assert rows[0]["errors"]
    assert json_lines(folder / "resolver_analysis.jsonl") == [row for row in rows if row["errors"]]
    assert 0 < len(json_lines(folder / "resolver_analysis.jsonl")) <= count
    # Scoring is post-run: model input still contains only candidates and visible records.
    assert len(clients) == 1 and clients[0].calls == count + 1
    assert all(set(payload) == {"candidate", "related"} for payload in clients[0].payloads)
    assert all("act" not in payload["candidate"] and "expected" not in payload for payload in clients[0].payloads)


def test_end_to_end_runs_do_not_emit_gold_candidate_evaluation_artifacts(tmp_path):
    result = gold_run(condition="end_to_end")
    assert result.resolver_scores is None
    folder = harness.write_run(result, tmp_path)
    assert not ARTIFACTS.intersection(p.name for p in folder.iterdir())
    assert {p.name for p in folder.iterdir()} == {
        "manifest.json", "answers.jsonl", "ops.jsonl", "candidates.jsonl", "metrics.json",
    }


def test_aborted_run_keeps_earlier_scores_in_memory_but_does_not_publish_complete_evaluation(monkeypatch, tmp_path):
    constructed = 0

    def factory():
        nonlocal constructed
        constructed += 1
        return ProposalsClient({1: FatalModelError("offline provider denial")} if constructed == 2 else None)

    install_clients(monkeypatch, factory)
    with pytest.raises(harness.RunAborted) as caught:
        harness.run(systems.REGISTRY[SYSTEM], [pilot("pilot-01"), pilot("pilot-02")], "dev",
                    condition="gold_candidates")
    result = caught.value.result
    assert result.status == "failed"
    assert len(result.resolver_scores) == gold_count("pilot-01")
    assert {row["scenario_id"] for row in result.resolver_scores} == {"pilot-01"}
    folder = harness.write_run(result, tmp_path)
    assert not ARTIFACTS.intersection(p.name for p in folder.iterdir())
    assert (folder / "resolver_events.jsonl").is_file()
    assert (folder / "resolver_errors.jsonl").is_file()


def test_scoring_does_not_pass_gold_timeline_to_a_non_gold_system(tmp_path):
    instances = []

    class NoOperationSystem:
        accepts_gold_candidates = True

        def __init__(self, meta, gold):
            assert gold is None
            self.candidates_seen = []
            instances.append(self)

        def observe(self, turn, when, gold_candidates=None):
            assert gold_candidates is not None
            self.candidates_seen.extend(gold_candidates)

        def answer(self, question):
            return Answer(status="abstain")

        def operations(self):
            return []

    spec = SystemSpec("offline-no-operations", NoOperationSystem, False, "offline scorer boundary fixture")
    result = harness.run(spec, [pilot("pilot-01")], "dev", condition="gold_candidates")
    count = gold_count("pilot-01")
    assert len(instances[0].candidates_seen) == len(result.resolver_scores) == count
    folder = harness.write_run(result, tmp_path)
    summary = json.loads((folder / "resolver_metrics.json").read_text(encoding="utf-8"))
    assert summary["counts"]["missing_operations"] == count
    assert summary["counts"]["emitted_operations"] == 0
    assert summary["metrics"]["label_accuracy"]["value"] == 0.0
    assert summary["metrics"]["label_accuracy"]["n"] == count
    assert summary["metrics"]["invalid_operation_rate"]["value"] is None


def test_mixed_operation_hook_availability_does_not_publish_partial_scores(tmp_path):
    class WithoutOperations:
        accepts_gold_candidates = True

        def __init__(self, system):
            self.system = system

        def observe(self, *args, **kwargs):
            return self.system.observe(*args, **kwargs)

        def answer(self, question):
            return self.system.answer(question)

    def factory(meta, timeline):
        system = systems.REGISTRY["pipeline-gold"].factory(meta, timeline)
        return system if meta.scenario_id == "pilot-01" else WithoutOperations(system)

    spec = SystemSpec("offline-mixed-hooks", factory, True, "offline partial instrumentation fixture")
    result = harness.run(spec, [pilot("pilot-01"), pilot("pilot-02")], "dev", condition="gold_candidates")
    assert result.status == "completed" and result.resolver_scores is None
    assert {row.scenario_id for row in result.rows} == {"pilot-01", "pilot-02"}
    folder = harness.write_run(result, tmp_path)
    assert not ARTIFACTS.intersection(path.name for path in folder.iterdir())


def test_resolver_report_reads_only_saved_rows_without_models_or_scenarios(monkeypatch, tmp_path, capsys):
    folder = harness.write_run(gold_run(), tmp_path / "runs")

    def forbidden(*args, **kwargs):
        raise AssertionError("A saved resolver report must not need scenarios, models or network")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "load_scenario", forbidden)
    monkeypatch.setattr(cli, "scenario_paths", forbidden)
    monkeypatch.setattr(cli, "replay", forbidden)
    monkeypatch.setattr(harness, "replay", forbidden)
    monkeypatch.setattr(LLMResolver, "from_env", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setitem(sys.modules, "openai", None)
    assert cli.main(["resolver-report", str(folder)]) == 0
    output = capsys.readouterr().out
    assert "label_accuracy" in output and "state_accuracy" in output
    assert "ADD-active" in output and "SUPERSEDE" in output
    assert "gold" in output.lower()


def test_resolver_report_rejects_a_cached_summary_inconsistent_with_saved_rows(tmp_path, capsys):
    folder = harness.write_run(gold_run(), tmp_path)
    path = folder / "resolver_metrics.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    summary["metrics"]["label_accuracy"]["value"] = 0.0
    path.write_text(json.dumps(summary), encoding="utf-8")
    assert cli.main(["resolver-report", str(folder)]) == 2
    assert "do not match" in capsys.readouterr().out


@pytest.mark.parametrize("invalid", ["condition", "failed", "missing_scores", "schema_version"])
def test_resolver_report_refuses_ineligible_or_incomplete_saved_runs(tmp_path, capsys, invalid):
    folder = harness.write_run(gold_run(), tmp_path)
    manifest_path = folder / "manifest.json"
    info = json.loads(manifest_path.read_text(encoding="utf-8"))
    if invalid == "condition":
        info["condition"] = "end_to_end"
    elif invalid == "failed":
        info["status"] = "failed"
    elif invalid == "missing_scores":
        (folder / "resolver_scores.jsonl").unlink()
    else:
        path = folder / "resolver_metrics.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["schema_version"] = 99
        path.write_text(json.dumps(summary), encoding="utf-8")
    manifest_path.write_text(json.dumps(info), encoding="utf-8")
    assert cli.main(["resolver-report", str(folder)]) == 2
    output = capsys.readouterr().out.lower()
    assert any(word in output for word in ("cannot", "failed", "missing", "requires", "unsupported"))


def test_cli_run_writes_resolver_artifacts_for_gold_candidate_condition(tmp_path, capsys):
    assert cli.main(["run", "--system", "pipeline-gold", "--condition", "gold_candidates",
                     "--root", str(DEV.parent), "--out", str(tmp_path)]) == 0
    (folder,) = tmp_path.iterdir()
    assert ARTIFACTS.issubset(p.name for p in folder.iterdir())
    info = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert info["condition"] == "gold_candidates" and info["uses_gold_labels"] is True
    summary = json.loads((folder / "resolver_metrics.json").read_text(encoding="utf-8"))
    assert summary["counts"]["gold_candidates"] == sum(gold_count(sid) for sid in PILOT_IDS)
    capsys.readouterr()
    assert cli.main(["resolver-report", str(folder)]) == 0
    assert "1.000" in capsys.readouterr().out
