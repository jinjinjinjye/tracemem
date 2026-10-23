"""Candidate-local source repair must not change a validated adoption structure."""

import copy
import json

import pytest

import tracemem.resolver as resolver_module
from test_resolver import candidate, decision, log_with, operation, reply, resolver, rid
from tracemem.resolver import ModelReply, ResolverError, RetryableModelError


ADOPTIONS = [("ADD", "proposed"), ("SUPERSEDE", "proposed"), ("SUPERSEDE", "contested")]


def adoption(op="SUPERSEDE", status="proposed"):
    log = log_with()
    if op == "SUPERSEDE":
        log.apply(operation("ADD", "S1-T1", "A", add_as="active"))
    log.apply(operation("FLAG" if status == "contested" else "ADD", "S1-T2", "B",
                        add_as="proposed" if status == "proposed" else None,
                        targets=[rid("S1-T1")] if status == "contested" else [],
                        sources=["S1-T2", "S1-T1"]))
    log.apply(operation("ADD", "S1-T3", "B", add_as="proposed"))
    targets = ([rid("S1-T1")] if op == "SUPERSEDE" else []) + [rid("S1-T2")]
    good = decision(op, add_as="active" if op == "ADD" else None,
                    targets=targets, sources=["S1-T4", "S1-T2"])
    return log, good


def feedback(client, call=1):
    return json.loads(client.calls[call]["messages"][2]["content"])


def expected_repair(good):
    return {"op": good["op"], "add_as": good["add_as"], "targets": sorted(good["targets"]),
            "source_turn_ids": sorted(good["source_turn_ids"]), "truncated": False}


def drop_adopted_target(good):
    return {**good, "targets": [rid("S1-T1")] if good["op"] == "SUPERSEDE" else [],
            "source_turn_ids": ["S1-T4"]}


@pytest.mark.parametrize("op,status", ADOPTIONS)
@pytest.mark.parametrize("sources", [
    ["S1-T4", "S1-T2", "S1-T2"],
    ["S1-T2"],
    ["S1-T4", "S1-T2", "S1-T99"],
    ["S1-T4"],
    ["S1-T4", "S1-T2", "S1-T1"],
], ids=["duplicate", "missing-candidate", "unseen", "missing-origin", "old-source"])
def test_every_source_error_on_a_legal_adoption_requires_preserving_its_targets(op, status, sources):
    log, good = adoption(op, status)
    before_records, before_ops = log.records(), list(log.ops)
    real, client = resolver(reply({**good, "source_turn_ids": sources}), reply(drop_adopted_target(good)))

    with pytest.raises(ResolverError, match="source repair must preserve"):
        real.resolve(candidate(), log.records())

    assert len(client.calls) == 2
    assert feedback(client)["source_repair_constraints"] == expected_repair(good)
    assert feedback(client)["instruction"] == resolver_module.SOURCE_REPAIR_INSTRUCTION
    assert log.records() == before_records and log.ops == before_ops


@pytest.mark.parametrize("op,status", ADOPTIONS)
@pytest.mark.parametrize("mutation", ["add-target", "replace-target", "operation", "add-as"])
def test_source_repair_rejects_adding_or_substituting_targets_and_changing_operation_or_status(op, status, mutation):
    log, good = adoption(op, status)
    changed = copy.deepcopy(good)
    if mutation == "add-target":
        changed["targets"].append(rid("S1-T3"))
        changed["source_turn_ids"].append("S1-T3")
    elif mutation == "replace-target":
        changed["targets"][-1] = rid("S1-T3")
        changed["source_turn_ids"] = ["S1-T4", "S1-T3"]
    elif mutation == "operation":
        changed.update(op="SUPERSEDE" if op == "ADD" else "FLAG", add_as=None)
        changed["targets"] = [rid("S1-T2")] if op == "ADD" else [rid("S1-T1")]
    else:
        changed["add_as"] = "proposed" if op == "ADD" else "active"
    real, client = resolver(reply({**good, "source_turn_ids": ["S1-T4"]}), reply(changed), reply(good),
                            max_attempts=3)

    resolved = real.resolve(candidate(), log.records())

    assert len(client.calls) == 3
    first, second = feedback(client), feedback(client, 2)
    assert "source repair must preserve" in second["error"]
    assert first["source_repair_constraints"] == second["source_repair_constraints"] == expected_repair(good)
    assert resolved.targets == good["targets"]
    log.apply(resolved)
    assert log.item_state(candidate().item).active.source_turn_ids == good["source_turn_ids"]


def test_source_repair_accepts_target_set_reordering_and_normalizes_candidate_sources_first():
    log, good = adoption()
    reordered = {**good, "targets": list(reversed(good["targets"])),
                 "source_turn_ids": list(reversed(good["source_turn_ids"]))}
    real, client = resolver(reply({**good, "source_turn_ids": ["S1-T4"]}), reply(reordered))

    resolved = real.resolve(candidate(), log.records())

    assert len(client.calls) == 2
    assert resolved.targets == reordered["targets"] and resolved.source_turn_ids == good["source_turn_ids"]
    log.apply(resolved)
    assert log.item_state(candidate().item).previous_active.value == "A"


@pytest.mark.parametrize("illegal", ["add-with-active", "missing-active-target", "unknown-target",
                                     "duplicate-target", "different-value-target", "non-null-add-as"])
def test_source_errors_on_illegal_structure_do_not_lock_an_incorrect_adoption(illegal):
    log, good = adoption()
    bad = {**good, "targets": list(good["targets"]), "source_turn_ids": ["S1-T4", "S1-T4"]}
    if illegal == "add-with-active":
        bad.update(op="ADD", add_as="active", targets=[rid("S1-T2")])
    elif illegal == "missing-active-target":
        bad["targets"] = [rid("S1-T2")]
    elif illegal == "unknown-target":
        bad["targets"].append("missing-record")
    elif illegal == "duplicate-target":
        bad["targets"].append(rid("S1-T2"))
    elif illegal == "different-value-target":
        log = log_with(operation("ADD", "S1-T1", "A", add_as="active"),
                       operation("ADD", "S1-T2", "B", add_as="proposed"),
                       operation("ADD", "S1-T3", "C", add_as="proposed"))
        bad["targets"].append(rid("S1-T3"))
    else:
        bad["add_as"] = "active"
    corrected = decision(add_as="proposed")
    real, client = resolver(reply(bad), reply(corrected))

    resolved = real.resolve(candidate(), log.records())

    assert len(client.calls) == 2
    assert "source_repair_constraints" not in feedback(client)
    assert feedback(client)["instruction"] == resolver_module.RETRY_INSTRUCTION
    assert resolved.op == "ADD" and resolved.add_as == "proposed" and resolved.targets == []
    log.apply(resolved)
    assert log.item_state(candidate().item).active.value == "A"


@pytest.mark.parametrize("kind", ["add-proposed", "unselected-add-active", "keep", "flag", "active-only-supersede"])
def test_nonadoption_source_errors_still_allow_reconsidering_the_whole_decision(kind):
    log, good = adoption("ADD" if kind == "unselected-add-active" else "SUPERSEDE")
    cand = candidate(value="A" if kind == "keep" else "B")
    if kind in ("add-proposed", "unselected-add-active"):
        bad = decision(add_as="active" if kind == "unselected-add-active" else "proposed")
    else:
        op = {"keep": "KEEP", "flag": "FLAG", "active-only-supersede": "SUPERSEDE"}[kind]
        bad = decision(op, add_as=None, targets=[rid("S1-T1")])
    bad["source_turn_ids"] = ["S1-T4", "S1-T4"]
    corrected = good if kind in ("add-proposed", "flag") else decision(add_as="proposed")
    real, client = resolver(reply(bad), reply(corrected))

    resolved = real.resolve(cand, log.records())

    assert len(client.calls) == 2 and "source_repair_constraints" not in feedback(client)
    assert resolved.op == corrected["op"] and resolved.targets == corrected["targets"]
    log.apply(resolved)


@pytest.mark.parametrize("interruption", [
    ModelReply(content="not JSON"), ModelReply(content="", refused=True),
    ModelReply(content="partial", finish_reason="length"), RetryableModelError("private provider details"),
], ids=["malformed", "refusal", "unfinished", "transient"])
def test_source_repair_survives_interruption_and_rejects_a_subsequent_dropped_target(interruption):
    log, good = adoption()
    real, client = resolver(reply({**good, "source_turn_ids": ["S1-T4"]}), interruption,
                            reply(drop_adopted_target(good)), reply(good), max_attempts=5)

    resolved = real.resolve(candidate(), log.records())

    assert len(client.calls) == 4
    for index in range(1, 4):
        assert feedback(client, index)["source_repair_constraints"] == expected_repair(good)
    assert "source repair must preserve" in feedback(client, 3)["error"]
    assert "private provider details" not in json.dumps(client.calls, default=str)
    assert resolved.targets == good["targets"]
    log.apply(resolved)


def test_malformed_refusal_and_transient_combination_never_clears_repair_within_five_attempts():
    log, good = adoption()
    before = log.records()
    real, client = resolver(reply({**good, "source_turn_ids": ["S1-T4"]}),
                            ModelReply(content="malformed"), ModelReply(content="", refused=True),
                            RetryableModelError("private provider details"), reply(drop_adopted_target(good)),
                            max_attempts=5)

    with pytest.raises(ResolverError, match="source repair must preserve"):
        real.resolve(candidate(), log.records())

    assert len(client.calls) == real.usage().calls == 5
    assert client.calls[4]["messages"] == client.calls[3]["messages"]
    assert all(feedback(client, index)["source_repair_constraints"] == expected_repair(good)
               for index in range(1, 5))
    assert log.records() == before


@pytest.mark.parametrize("exhausted", [False, True], ids=["successful", "exhausted"])
def test_repair_constraints_reset_before_the_next_candidate_after_success_or_exhaustion(exhausted):
    log, good = adoption()
    next_candidate = candidate(turn="S1-T5", value="C")
    next_reply = decision(add_as="proposed", sources=["S1-T5"])
    real, client = resolver(reply({**good, "source_turn_ids": ["S1-T4"]}),
                            reply(drop_adopted_target(good) if exhausted else good), reply(next_reply))
    if exhausted:
        with pytest.raises(ResolverError):
            real.resolve(candidate(), log.records())
    else:
        log.apply(real.resolve(candidate(), log.records()))

    resolved = real.resolve(next_candidate, log.records())

    assert len(client.calls) == real.usage().calls == 3
    assert len(client.calls[-1]["messages"]) == 2
    assert json.loads(client.calls[-1]["messages"][1]["content"])["candidate"]["candidate_id"] == next_candidate.candidate_id
    assert resolved.op == "ADD" and resolved.add_as == "proposed" and resolved.targets == []
    log.apply(resolved)
    assert any(record.value == "C" for record in log.item_state(candidate().item).proposed)


def test_bounded_feedback_does_not_truncate_enforced_target_or_source_sets(monkeypatch):
    log, good = adoption()
    good["targets"].append(rid("S1-T3"))
    good["source_turn_ids"].append("S1-T3")
    monkeypatch.setattr(resolver_module, "FEEDBACK_MAX_IDS", 1)
    monkeypatch.setattr(resolver_module, "FEEDBACK_MAX_ID_CHARS", 6)
    dropped = {**good, "targets": good["targets"][:-1], "source_turn_ids": ["S1-T4", "S1-T2"]}
    missing_source = {**good, "source_turn_ids": ["S1-T4", "S1-T2"]}
    real, client = resolver(reply({**good, "source_turn_ids": ["S1-T4"]}), reply(dropped),
                            reply(missing_source), reply(good), max_attempts=4)

    resolved = real.resolve(candidate(), log.records())

    assert len(client.calls) == 4
    for index in (1, 2, 3):
        repair = feedback(client, index)["source_repair_constraints"]
        assert repair["truncated"] is True
        assert len(repair["targets"]) == len(repair["source_turn_ids"]) == 1
        assert all(len(identifier) <= 6 for field in ("targets", "source_turn_ids") for identifier in repair[field])
    assert "source repair must preserve" in feedback(client, 2)["error"]
    assert "creating turns in sources: S1-T3" in feedback(client, 3)["error"]
    original = json.loads(client.calls[0]["messages"][1]["content"])
    assert {record["record_id"] for record in original["related"]} == set(good["targets"])
    assert resolved.targets == good["targets"] and resolved.source_turn_ids == good["source_turn_ids"]
    log.apply(resolved)
    state = log.item_state(candidate().item)
    assert state.active.supersedes == good["targets"] and not state.proposed


@pytest.mark.parametrize("name", ["SOURCE_RETRY_POLICY_VERSION", "SOURCE_REPAIR_INSTRUCTION"])
def test_source_retry_policy_and_instruction_are_part_of_reproducible_policy_hash(monkeypatch, name):
    real, _ = resolver()
    before = real.describe()
    monkeypatch.setattr(resolver_module, name, getattr(resolver_module, name) + " changed")

    after = real.describe()

    assert after["decision_policy_hash"] != before["decision_policy_hash"]
    assert after["output_schema_hash"] == before["output_schema_hash"]
    assert after["prompt_hash"] == before["prompt_hash"]
    assert {key: value for key, value in after.items() if key != "decision_policy_hash"} == {
        key: value for key, value in before.items() if key != "decision_policy_hash"
    }
