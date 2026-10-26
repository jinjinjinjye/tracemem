"""Offline coverage of the real resolver's registry, harness and saved-run boundary.

The fake provider always proposes the extracted value. It tests integration and
accounting, not whether an LLM understands the pilot dialogue correctly.
"""

from __future__ import annotations

import json
import sys

import pytest
import yaml

from support import DEV, pilot, pilot_path, pilot_timeline, raw_yaml
from tracemem import cli, systems
from tracemem.eval import harness
from tracemem.eval.report import comparison_table, load_run
from tracemem.ops import InvalidOperation
from tracemem.resolver import (
    FatalModelError,
    LLMResolver,
    ModelReply,
    ResolverConfig,
    ResolverConfigError,
    ResolverInputError,
)
from tracemem.systems.base import SystemSpec


SYSTEM = "pipeline-resolver-dev"


class ScriptedClient:
    """Use numbered responses/exceptions, followed by valid ADD-proposed outputs."""

    def __init__(self, actions=None):
        self.actions = actions or {}
        self.calls = 0

    def complete(self, *, config, messages, response_format):
        self.calls += 1
        action = self.actions.get(self.calls)
        if isinstance(action, Exception):
            raise action
        if isinstance(action, ModelReply):
            return action
        candidate = json.loads(messages[1]["content"])["candidate"]
        return ModelReply(json.dumps({
            "op": "ADD", "add_as": "proposed", "targets": [],
            "source_turn_ids": candidate["source_turn_ids"], "reason": None,
            "rationale": "Offline integration fixture proposes the candidate.",
        }), input_tokens=7, output_tokens=3)


@pytest.fixture
def install_resolvers(monkeypatch):
    """Patch only model construction; exercise the registered factory and real resolver."""
    instances = []

    def install(client_factory=ScriptedClient):
        def from_env(cls):
            resolver = cls(ResolverConfig(model="offline-fixture", max_attempts=2), client_factory())
            instances.append(resolver)
            return resolver

        monkeypatch.setattr(LLMResolver, "from_env", classmethod(from_env))
        return instances

    return install


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def candidate_count(scenario_id):
    return sum(len(candidates) for candidates in pilot_timeline(scenario_id).candidates_by_turn.values())


def test_system_listing_is_lazy_without_model_credentials_or_sdk(monkeypatch, capsys):
    monkeypatch.delenv("TRACEMEM_RESOLVER_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "openai", None)

    def must_not_construct(cls):
        raise AssertionError("Listing systems must not construct a model client")

    monkeypatch.setattr(LLMResolver, "from_env", classmethod(must_not_construct))
    assert cli.main(["systems"]) == 0
    assert SYSTEM in capsys.readouterr().out
    assert systems.REGISTRY[SYSTEM].uses_gold is True


def test_registered_factory_creates_a_fresh_resolver_for_every_scenario(install_resolvers):
    instances = install_resolvers()
    scenario_ids = ["pilot-01", "pilot-02"]
    result = harness.run(systems.REGISTRY[SYSTEM], [pilot(sid) for sid in scenario_ids], "dev")
    assert len(instances) == 2 and instances[0] is not instances[1]
    assert instances[0].client is not instances[1].client
    for sid, resolver in zip(scenario_ids, instances):
        assert resolver.usage().calls == candidate_count(sid)
        assert result.resolver_usage[sid].calls == candidate_count(sid)
        assert len(result.resolver_events[sid]) == candidate_count(sid)
    assert result.status == "completed" and result.failure is None
    assert result.uses_gold is True


def test_run_saves_per_candidate_events_configuration_and_usage(install_resolvers, tmp_path):
    install_resolvers()
    result = harness.run(systems.REGISTRY[SYSTEM], [pilot("pilot-01")], "dev")
    folder = harness.write_run(result, tmp_path)
    info, rows = load_run(folder)
    events = lines(folder / "resolver_events.jsonl")
    candidates = lines(folder / "candidates.jsonl")
    ops = lines(folder / "ops.jsonl")
    assert info["status"] == "completed"
    assert info["uses_gold_labels"] is True
    config = info["system_config"]["resolver_config"]
    assert config["model"] == "offline-fixture"
    assert len(config["prompt_hash"]) == len(config["output_schema_hash"]) == 64
    assert len(rows) == len(pilot_timeline("pilot-01").questions)
    assert [event["candidate_id"] for event in events] == [candidate["candidate_id"] for candidate in candidates]
    assert [event["operation_id"] for event in events] == [op["op_id"] for op in ops]
    for event, candidate in zip(events, candidates):
        assert event["scenario_id"] == "pilot-01"
        assert event["turn_id"] == candidate["source_turn_ids"][0]
        assert event["item"] == candidate["item"]
        assert event["status"] == "applied" and event["attempts"] == 1
        assert event["usage"] == {"calls": 1, "input_tokens": 7, "output_tokens": 3}
    assert lines(folder / "resolver_errors.jsonl") == []
    assert not (folder / "rejected_ops.jsonl").exists()


def test_usage_sums_scenarios_once_and_includes_invalid_completions(install_resolvers, tmp_path):
    bad = ModelReply("invalid JSON", input_tokens=11, output_tokens=2)
    install_resolvers(lambda: ScriptedClient({1: bad}))
    scenario_ids = ["pilot-01", "pilot-02"]
    result = harness.run(systems.REGISTRY[SYSTEM], [pilot(sid) for sid in scenario_ids], "dev")
    folder = harness.write_run(result, tmp_path)
    usage = json.loads((folder / "usage.json").read_text(encoding="utf-8"))["resolver"]
    assert usage["tokens_are_provider_reported"] is True
    for sid in scenario_ids:
        count = candidate_count(sid)
        assert usage["by_scenario"][sid] == {
            "calls": count + 1, "input_tokens": count * 7 + 11, "output_tokens": count * 3 + 2,
        }
        assert result.resolver_events[sid][0]["attempts"] == 2
        assert result.resolver_events[sid][1]["attempts"] == 1
    assert usage["total"] == {
        key: sum(usage["by_scenario"][sid][key] for sid in scenario_ids)
        for key in ("calls", "input_tokens", "output_tokens")
    }


def test_exhausted_generation_is_retained_without_inventing_an_operation(install_resolvers, tmp_path):
    bad = ModelReply("invalid JSON", input_tokens=11, output_tokens=2)
    install_resolvers(lambda: ScriptedClient({1: bad, 2: bad}))
    result = harness.run(systems.REGISTRY[SYSTEM], [pilot("pilot-01")], "dev")
    folder = harness.write_run(result, tmp_path)
    events = lines(folder / "resolver_events.jsonl")
    errors = lines(folder / "resolver_errors.jsonl")
    candidates = lines(folder / "candidates.jsonl")
    ops = lines(folder / "ops.jsonl")
    assert result.status == "completed"
    assert len(events) == len(candidates) == candidate_count("pilot-01")
    assert len(ops) == len(candidates) - 1
    assert errors == [events[0]]
    failure = errors[0]
    assert failure["status"] == "generation_failed" and failure["operation_id"] is None
    assert failure["attempts"] == 2 and failure["error_type"] == "ResolverError"
    assert failure["error_detail"]
    assert failure["usage"] == {"calls": 2, "input_tokens": 22, "output_tokens": 4}
    assert all(op["candidate_id"] != failure["candidate_id"] for op in ops)
    assert all(event["status"] == "applied" for event in events[1:])
    assert len(result.rows) == len(pilot_timeline("pilot-01").questions)
    assert not (folder / "rejected_ops.jsonl").exists()


def test_storage_rejection_and_generation_failure_have_distinct_logs(install_resolvers, tmp_path):
    bad = ModelReply("invalid JSON")
    install_resolvers(lambda: ScriptedClient({1: bad, 2: bad}))
    registered = systems.REGISTRY[SYSTEM]

    def factory(meta, gold):
        system = registered.factory(meta, gold)
        apply = system.log.apply
        first = True

        def reject_once(op):
            nonlocal first
            if first:
                first = False
                raise InvalidOperation("offline storage rejection")
            return apply(op)

        system.log.apply = reject_once
        return system

    spec = SystemSpec(SYSTEM, factory, True, "offline storage rejection fixture")
    result = harness.run(spec, [pilot("pilot-01")], "dev")
    folder = harness.write_run(result, tmp_path)
    events = lines(folder / "resolver_events.jsonl")
    errors = lines(folder / "resolver_errors.jsonl")
    rejected = lines(folder / "rejected_ops.jsonl")
    assert [event["status"] for event in events[:3]] == ["generation_failed", "rejected", "applied"]
    assert errors == [events[0]]
    assert len(rejected) == 1
    assert rejected[0]["candidate_id"] == events[1]["candidate_id"]
    assert rejected[0]["op_id"] == events[1]["operation_id"]
    assert events[1]["error_type"] == "InvalidOperation"
    assert len(result.operations["pilot-01"]) == candidate_count("pilot-01") - 2


def test_fatal_provider_error_preserves_partial_answers_events_and_usage(install_resolvers, tmp_path):
    timeline = pilot_timeline("pilot-01")
    first_session_calls = sum(len(cands) for turn, cands in timeline.candidates_by_turn.items()
                              if turn.startswith("S1-"))
    install_resolvers(lambda: ScriptedClient({first_session_calls + 1: FatalModelError("provider denied request")}))
    with pytest.raises(harness.RunAborted) as caught:
        harness.run(systems.REGISTRY[SYSTEM], [pilot("pilot-01"), pilot("pilot-02")], "dev")
    result = caught.value.result
    assert result.status == "failed"
    assert result.failure["scenario_id"] == "pilot-01"
    assert result.failure["error_type"] == "FatalModelError"
    assert len(result.rows) == sum(q.after == "S1" for q in timeline.questions) > 0
    assert len(result.operations["pilot-01"]) == first_session_calls
    assert "pilot-02" not in result.resolver_events
    events = result.resolver_events["pilot-01"]
    assert len(events) == first_session_calls + 1
    assert events[-1]["status"] == "aborted"
    assert events[-1]["operation_id"] is None
    assert events[-1]["usage"] == {"calls": 1, "input_tokens": 0, "output_tokens": 0}
    assert result.resolver_usage["pilot-01"].calls == first_session_calls + 1
    folder = harness.write_run(result, tmp_path)
    assert lines(folder / "resolver_errors.jsonl")[-1]["status"] == "aborted"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "failed" and manifest["failure"] == result.failure
    with pytest.raises(ValueError, match="failed|incomplete"):
        load_run(folder)
    with pytest.raises(ValueError, match="failed|incomplete"):
        comparison_table([folder], allow_mixed=True, n=10)


@pytest.mark.parametrize("error_type", [ResolverConfigError, ResolverInputError, FatalModelError])
def test_factory_failure_becomes_a_failed_run_without_a_successful_system(monkeypatch, tmp_path, error_type):
    def fail(cls):
        raise error_type("offline initialization failure")

    monkeypatch.setattr(LLMResolver, "from_env", classmethod(fail))
    with pytest.raises(harness.RunAborted) as caught:
        harness.run(systems.REGISTRY[SYSTEM], [pilot("pilot-01")], "dev")
    result = caught.value.result
    assert result.status == "failed" and not result.rows
    assert result.failure["error_type"] == error_type.__name__
    assert not result.resolver_events and not result.resolver_usage
    folder = harness.write_run(result, tmp_path)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
    with pytest.raises(ValueError, match="failed|incomplete"):
        load_run(folder)


def test_abort_in_later_scenario_retains_completed_scenario_without_starting_next(install_resolvers):
    constructed = 0

    def clients():
        nonlocal constructed
        constructed += 1
        return ScriptedClient({1: FatalModelError("provider denied request")} if constructed == 2 else None)

    instances = install_resolvers(clients)
    with pytest.raises(harness.RunAborted) as caught:
        harness.run(systems.REGISTRY[SYSTEM], [pilot(sid) for sid in ("pilot-01", "pilot-02", "pilot-03")], "dev")
    result = caught.value.result
    assert len(instances) == 2
    assert result.failure["scenario_id"] == "pilot-02"
    assert len(result.rows) == len(pilot_timeline("pilot-01").questions)
    assert {row.scenario_id for row in result.rows} == {"pilot-01"}
    assert set(result.resolver_events) == set(result.resolver_usage) == {"pilot-01", "pilot-02"}
    assert all(event["status"] == "applied" for event in result.resolver_events["pilot-01"])
    assert result.resolver_events["pilot-02"][0]["status"] == "aborted"
    assert result.resolver_usage["pilot-01"].calls == candidate_count("pilot-01")
    assert result.resolver_usage["pilot-02"].calls == 1


def test_actual_missing_model_configuration_is_saved_as_failure_without_sdk(monkeypatch, tmp_path):
    monkeypatch.delenv("TRACEMEM_RESOLVER_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "openai", None)
    assert cli.main(["run", "--system", SYSTEM, "--root", str(DEV.parent), "--out", str(tmp_path)]) == 2
    (folder,) = tmp_path.iterdir()
    info = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert info["status"] == "failed"
    assert info["failure"]["error_type"] == "ResolverConfigError"
    assert "TRACEMEM_RESOLVER_MODEL" in info["failure"]["message"]


def test_cli_completes_with_visible_recoverable_failure_summary(install_resolvers, tmp_path, capsys):
    bad = ModelReply("invalid JSON")
    install_resolvers(lambda: ScriptedClient({1: bad, 2: bad}))
    assert cli.main(["run", "--system", SYSTEM, "--root", str(DEV.parent), "--out", str(tmp_path)]) == 0
    (folder,) = tmp_path.iterdir()
    output = capsys.readouterr().out.lower()
    assert "generation_failed" in output or "generation failures" in output
    assert "uses gold labels" in output
    assert "saved to" in output
    manifest, rows = load_run(folder)
    assert manifest["status"] == "completed" and rows
    assert len(lines(folder / "resolver_errors.jsonl")) == len(list(DEV.glob("*.yaml")))


@pytest.mark.parametrize("error_type", [ResolverConfigError, FatalModelError])
def test_cli_aborts_with_code_two_and_saves_failed_run(monkeypatch, tmp_path, capsys, error_type):
    def fail(cls):
        raise error_type("offline startup failure")

    monkeypatch.setattr(LLMResolver, "from_env", classmethod(fail))
    assert cli.main(["run", "--system", SYSTEM, "--root", str(DEV.parent), "--out", str(tmp_path)]) == 2
    (folder,) = tmp_path.iterdir()
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
    assert manifest["failure"]["error_type"] == error_type.__name__
    output = capsys.readouterr().out.lower()
    assert "saved to" in output and ("failed" in output or "aborted" in output)
    assert cli.main(["report", str(folder), "--allow-mixed", "--resamples", "10"]) == 2
    assert "cannot compare" in capsys.readouterr().out


def test_aborted_test_run_is_audited_with_partial_diagnostics(install_resolvers, monkeypatch, tmp_path):
    """Copy a public dev fixture into tmp; never read the repository's sealed split."""
    root = tmp_path / "scenarios"
    (root / "test").mkdir(parents=True)
    data = raw_yaml(pilot_path("pilot-01"))
    data["split"] = "test"
    (root / "test" / "copy.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    audit = tmp_path / "audit" / "test-runs.jsonl"
    monkeypatch.setattr(cli, "TEST_LOG", audit)
    monkeypatch.setattr(cli, "_test_split_allowed", lambda args: (True, "freeze-offline-fixture"))

    def offline_git(*args):
        if args[:1] == ("status",):
            return ""
        if args[:1] == ("describe",):
            return "freeze-offline-fixture"
        return "0" * 40

    monkeypatch.setattr(cli, "_git", offline_git)
    monkeypatch.setattr(harness, "_git", offline_git)
    install_resolvers(lambda: ScriptedClient({3: FatalModelError("offline provider denial")}))
    out = tmp_path / "runs"
    assert cli.main(["run", "--system", SYSTEM, "--split", "test", "--root", str(root),
                     "--out", str(out)]) == 2
    (folder,) = out.iterdir()
    info = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert info["status"] == "failed"
    events = lines(folder / "resolver_events.jsonl")
    assert [event["status"] for event in events] == ["applied", "applied", "aborted"]
    assert len(lines(folder / "ops.jsonl")) == 2
    assert lines(folder / "resolver_errors.jsonl") == [events[-1]]
    (entry,) = lines(audit)
    assert entry["run"] == folder.name
    assert entry["status"] == "failed" and entry["current_accuracy"] is None
    assert entry["failure"] == info["failure"]
    assert entry["failure"]["error_type"] == "FatalModelError"
    assert entry["system"] == SYSTEM and entry["condition"] == info["condition"]
    assert entry["system_config"] == info["system_config"]
    assert entry["system_config"]["resolver_config"]["model"] == "offline-fixture"
    assert entry["item_vocabulary_given_to_systems"] == info["item_vocabulary_given_to_systems"]
    assert entry["commit"] == info["git_commit"] == "0" * 40
    assert entry["freeze"] == "freeze-offline-fixture"
    assert entry["utc"]


def test_legacy_gold_run_keeps_its_file_layout_and_requires_no_llm(monkeypatch, tmp_path):
    def fail(cls):
        raise AssertionError("Gold stand-ins must not initialize an LLM")

    monkeypatch.setattr(LLMResolver, "from_env", classmethod(fail))
    result = harness.run(systems.REGISTRY["pipeline-gold"], [pilot("pilot-01")], "dev")
    folder = harness.write_run(result, tmp_path)
    assert {p.name for p in folder.iterdir()} == {
        "manifest.json", "answers.jsonl", "ops.jsonl", "candidates.jsonl", "metrics.json",
    }
    info, rows = load_run(folder)
    assert info["status"] == "completed" and rows
    assert all(row.outcome == "correct" for row in rows)


def test_old_manifest_without_status_still_loads(tmp_path):
    result = harness.run(systems.REGISTRY["oracle"], [pilot("pilot-01")], "dev")
    folder = harness.write_run(result, tmp_path)
    path = folder / "manifest.json"
    info = json.loads(path.read_text(encoding="utf-8"))
    info.pop("status", None)
    info.pop("failure", None)
    path.write_text(json.dumps(info), encoding="utf-8")
    _, rows = load_run(folder)
    assert len(rows) == len(result.rows)
