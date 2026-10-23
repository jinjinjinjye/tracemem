"""Reject captured adoption over-citation without rewriting model decisions.

All responses are scripted offline. Corrections come from development replay;
these tests measure executable validation and storage, not live model accuracy.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest

from support import pilot_timeline
from test_resolver import candidate, decision, log_with, operation, reply, resolver, rid, seeded_log
from tracemem.ops import OpLog
from tracemem.resolver import LLMResolver, ModelReply, ResolverConfig, ResolverError
from tracemem.schema import Candidate, Operation
from tracemem.systems.no_versions import CurrentOnlyStore


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "adoption_source_precision_failures.json").read_text(encoding="utf-8")
)
CASES = FIXTURE["resolver_captures"]
STORES = {"tracemem-controlled": OpLog, "tracemem-no-versions": CurrentOnlyStore}
DECISION_FIELDS = {"op", "add_as", "targets", "source_turn_ids", "reason", "rationale"}
CONFIG = ResolverConfig(model="offline-adoption-precision", max_attempts=2)


class ScriptedClient:
    def __init__(self, *replies):
        self.replies = replies
        self.calls = []

    def complete(self, **request):
        self.calls.append(copy.deepcopy(request))
        return ModelReply(content=json.dumps(self.replies[len(self.calls) - 1]))


def scripted_gold(case):
    candidate_id = case["request"]["candidate"]["candidate_id"]
    gold = pilot_timeline(case["scenario_id"]).gold_op_for(candidate_id)
    assert gold is not None
    result = gold.model_dump(include=DECISION_FIELDS)
    result["rationale"] = "Scripted development replay correction; not a live prediction."
    return result


def seeded_store(case):
    """Recreate the captured actual prefix, including previous source accumulation."""
    cand = Candidate.model_validate(case["request"]["candidate"])
    timeline = pilot_timeline(case["scenario_id"])
    speakers = {turn.id: turn.speaker for turn in timeline.scenario.turns()}
    store = STORES[case["system"]](cand.project_id)
    for turn in timeline.turn_order:
        store.observe_turn(turn, timeline.turn_times[turn], speakers[turn])
        if turn == case["observation"]["turn_id"]:
            break
    for raw in case["prefix_operations"]:
        store.apply(Operation.model_validate(raw))
    assert [record.model_dump(mode="json") for record in store.records()] == case["request"]["related"]
    return cand, store


def assert_rejection_feedback(client, case):
    first, second = client.calls
    assert first["config"] == CONFIG
    assert json.loads(first["messages"][1]["content"]) == case["request"]
    schema = first["response_format"]["json_schema"]["schema"]
    assert set(schema["properties"]) == set(schema["required"]) == DECISION_FIELDS
    assert second["messages"][:2] == first["messages"]
    assert len(second["messages"]) == 3
    feedback = json.loads(second["messages"][2]["content"])
    assert feedback["type"] == "resolver_validation_feedback"
    assert "extra sources" in feedback["error"]
    extra = set(case["observed_decision"]["source_turn_ids"]) - set(scripted_gold(case)["source_turn_ids"])
    assert extra and all(turn in feedback["error"] for turn in extra)
    assert feedback["rejected_decision"] == {
        field: case["observed_decision"][field]
        for field in ("op", "add_as", "targets", "source_turn_ids")
    }
    assert feedback["target_constraints"] == case["request"]["target_constraints"]
    assert not feedback["rejected_decision_truncated"]


def test_fixture_keeps_four_real_adoption_overcitations_with_actual_requests_and_turn_glosses():
    assert FIXTURE["provenance"]["split"] == "dev"
    assert len(CASES) == len({case["case_id"] for case in CASES}) == 4
    assert {case["system"] for case in CASES} == set(STORES)
    for case in CASES:
        assert json.loads(case["raw_reply"]) == case["observed_decision"]
        assert set(case["observed_decision"]) == DECISION_FIELDS
        timeline = pilot_timeline(case["scenario_id"])
        turns = {turn.id: turn for turn in timeline.scenario.turns()}
        turn = case["observation"]["turn_id"]
        cand = case["request"]["candidate"]
        expected_candidate = next(c for c in timeline.candidates_by_turn[turn]
                                  if c.candidate_id == cand["candidate_id"])
        assert cand == expected_candidate.model_dump(mode="json")
        assert datetime.fromisoformat(case["observation"]["when"]) == timeline.turn_times[turn]
        assert case["observation"]["speaker"] == turns[turn].speaker
        assert case["turn_glosses"][turn] == cand["text"]
        assert all(turns[tid].text == gloss for tid, gloss in case["turn_glosses"].items())
        assert set(case["observed_decision"]["source_turn_ids"]) <= set(case["turn_glosses"])
        assert case["observed_errors"] == ["wrong_sources"]
        gold = scripted_gold(case)
        assert set(gold["source_turn_ids"]) < set(case["observed_decision"]["source_turn_ids"])
        assert all(gold[field] == case["observed_decision"][field] for field in ("op", "add_as", "targets"))


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_captured_extra_sources_retry_preserves_targets_and_applies_only_precise_evidence(case):
    cand, store = seeded_store(case)
    before_records, before_ops = store.records(), list(store.ops)
    corrected = scripted_gold(case)
    client = ScriptedClient(case["observed_decision"], corrected)
    real = LLMResolver(CONFIG, client)

    resolved = real.resolve(cand, store.records())

    assert len(client.calls) == real.usage().calls == 2
    assert_rejection_feedback(client, case)
    assert store.records() == before_records and store.ops == before_ops
    for field, value in corrected.items():
        assert getattr(resolved, field) == value
    assert resolved.targets == case["observed_decision"]["targets"]
    predecessor = next(record for record in before_records if record.status == "active")
    adopted = next(record for record in before_records if record.status == "proposed"
                   and record.record_id in resolved.targets)

    store.apply(resolved)

    state = store.item_state(cand.item)
    assert state.active.record_id == cand.candidate_id and state.active.value == cand.value
    assert state.active.source_turn_ids == corrected["source_turn_ids"]
    assert adopted.created_turn in state.active.source_turn_ids
    assert predecessor.created_turn not in state.active.source_turn_ids
    assert not state.proposed and not state.contested and not state.flagged
    assert len(store.ops) == len(before_ops) + 1
    if case["system"] == "tracemem-controlled":
        assert state.active.supersedes == resolved.targets
        assert state.previous_active.record_id == predecessor.record_id
        assert state.previous_active.source_turn_ids == predecessor.source_turn_ids
        assert next(record for record in store.records()
                    if record.record_id == adopted.record_id).status == "superseded"
    else:
        assert state.active.supersedes == []
        assert state.history == [] and state.previous_active is None
        assert store.records() == [state.active]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_repeated_captured_extra_sources_exhausts_without_silent_trimming_or_partial_write(case):
    cand, store = seeded_store(case)
    before_records, before_ops = store.records(), list(store.ops)
    client = ScriptedClient(case["observed_decision"], case["observed_decision"])
    real = LLMResolver(CONFIG, client)

    with pytest.raises(ResolverError) as caught:
        real.resolve(cand, store.records())

    assert caught.value.candidate_id == cand.candidate_id
    assert caught.value.attempts == len(client.calls) == real.usage().calls == 2
    assert "extra sources" in caught.value.detail
    assert_rejection_feedback(client, case)
    assert store.records() == before_records and store.ops == before_ops


@pytest.mark.parametrize("op,status", [("ADD", "proposed"), ("SUPERSEDE", "proposed"),
                                      ("SUPERSEDE", "contested")])
def test_candidate_supplied_support_remains_required_even_if_it_also_belongs_to_old_records(op, status):
    log = log_with()
    if op == "SUPERSEDE":
        log.apply(operation("ADD", "S1-T1", "A", add_as="active"))
    log.apply(operation("FLAG" if status == "contested" else "ADD", "S1-T3", "B",
                        add_as="proposed" if status == "proposed" else None,
                        targets=[rid("S1-T1")] if status == "contested" else [],
                        sources=["S1-T3", "S1-T2"]))
    log.apply(operation("ADD", "S1-T4", "C", add_as="proposed"))
    targets = ([rid("S1-T1")] if op == "SUPERSEDE" else []) + [rid("S1-T3")]
    # Old active, accumulated proposal support, and an unselected proposal source
    # remain legitimate when extraction explicitly includes them in this candidate.
    cand = candidate(turn="S1-T6", source_turn_ids=["S1-T6", "S1-T1", "S1-T2", "S1-T4"])
    expected = cand.source_turn_ids + ["S1-T3"]
    output = decision(op, add_as="active" if op == "ADD" else None,
                      targets=targets, sources=list(reversed(expected)))
    real, client = resolver(reply(output))

    resolved = real.resolve(cand, log.records())

    assert len(client.calls) == 1 and resolved.source_turn_ids == expected
    assert resolved.targets == targets
    log.apply(resolved)
    state = log.item_state(cand.item)
    assert state.active.value == "B" and state.active.source_turn_ids == expected
    assert [record.value for record in state.proposed] == ["C"]


@pytest.mark.parametrize("op,add_as,value", [
    ("SUPERSEDE", None, "B"), ("KEEP", None, "A"), ("FLAG", None, "B"),
    ("ADD", "proposed", "B"), ("ADD", "active", "B"),
])
def test_precision_rule_does_not_expand_to_operations_without_selected_adoption(op, add_as, value):
    log = (log_with(operation("ADD", "S1-T2", "B", add_as="proposed"))
           if op == "ADD" and add_as == "active" else seeded_log())
    targets = [] if op == "ADD" else [rid("S1-T1")]
    old_source = "S1-T2" if op == "ADD" and add_as == "active" else "S1-T1"
    output = decision(op, add_as=add_as, targets=targets, sources=["S1-T4", old_source])
    real, client = resolver(reply(output))

    resolved = real.resolve(candidate(value=value), log.records())

    assert len(client.calls) == 1
    assert resolved.source_turn_ids == ["S1-T4", old_source]
    log.apply(resolved)
    # Choosing whether an open proposal was adopted is still the model's task.
    assert rid("S1-T2") in {record.record_id for record in log.item_state(candidate().item).proposed}
