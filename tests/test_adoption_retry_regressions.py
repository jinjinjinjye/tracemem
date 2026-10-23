"""Replay real source-repair target loss without a model or provider connection.

Captured replies reproduce the failure sequence. Successful replies are scripted
from development replay and establish validation/storage behavior, not model quality.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest

from support import pilot_timeline
from test_resolver_pipeline import EmptyExtractor, EmptyRetriever
from tracemem.components import GoldMatcher, RuleAnswerer
from tracemem.ops import OpLog
from tracemem.pipeline import TraceMemPipeline
from tracemem.resolver import LLMResolver, ModelReply, ResolverConfig, ResolverError
from tracemem.schema import Candidate, Operation, Usage
from tracemem.systems.no_versions import CurrentOnlyStore


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "adoption_retry_failures.json").read_text(encoding="utf-8")
)
CASES = FIXTURE["resolver_captures"]
STORES = {"tracemem-controlled": OpLog, "tracemem-no-versions": CurrentOnlyStore}
DECISION_FIELDS = {"op", "add_as", "targets", "source_turn_ids", "reason", "rationale"}


class ScriptedClient:
    def __init__(self, *replies):
        self.replies = replies
        self.calls = []

    def complete(self, **request):
        self.calls.append(copy.deepcopy(request))
        return self.replies[len(self.calls) - 1]


def captured_replies(case):
    return [ModelReply(content=attempt["raw_reply"], input_tokens=attempt["input_tokens"],
                       output_tokens=attempt["output_tokens"])
            for attempt in case["attempts"]]


def corrected_decision(case):
    gold = pilot_timeline(case["scenario_id"]).gold_op_for(case["request"]["candidate"]["candidate_id"])
    assert gold is not None
    decision = gold.model_dump(include=DECISION_FIELDS)
    decision["rationale"] = "Offline development replay correction preserving the selected adoption."
    return decision


def seeded_store(case):
    """Preserve actual preceding operations, including earlier source accumulation."""
    cand = Candidate.model_validate(case["request"]["candidate"])
    timeline = pilot_timeline(case["scenario_id"])
    turns = {turn.id: turn for turn in timeline.scenario.turns()}
    store = STORES[case["system"]](cand.project_id)
    for turn_id in timeline.turn_order:
        store.observe_turn(turn_id, timeline.turn_times[turn_id], turns[turn_id].speaker)
        if turn_id == case["observation"]["turn_id"]:
            break
    for raw in case["prefix_operations"]:
        store.apply(Operation.model_validate(raw))
    assert [record.model_dump(mode="json") for record in store.records()] == case["request"]["related"]
    return cand, store


def source_repair_resolver(case, *, corrected=False):
    replies = captured_replies(case)
    if corrected:
        replies.append(ModelReply(content=json.dumps(corrected_decision(case))))
    client = ScriptedClient(*replies)
    real = LLMResolver(ResolverConfig(model="offline-adoption-retry", max_attempts=len(replies)), client)
    return real, client


def assert_request_and_usage(case, real, client, *, corrected=False):
    assert len(client.calls) == (3 if corrected else 2)
    first = client.calls[0]
    assert json.loads(first["messages"][1]["content"]) == case["request"]
    schema = first["response_format"]["json_schema"]["schema"]
    assert set(schema["properties"]) == set(schema["required"]) == DECISION_FIELDS
    for call in client.calls[1:]:
        assert call["messages"][:2] == first["messages"]
        assert call["response_format"] == first["response_format"]
        assert len(call["messages"]) == 3
    first_feedback = json.loads(client.calls[1]["messages"][2]["content"])
    assert first_feedback["type"] == "resolver_validation_feedback"
    assert "extra sources" in first_feedback["error"]
    assert first_feedback["rejected_decision"] == {
        key: case["attempts"][0]["observed_decision"][key]
        for key in ("op", "add_as", "targets", "source_turn_ids")
    }
    gold = corrected_decision(case)
    repair = {"op": gold["op"], "add_as": gold["add_as"], "targets": sorted(gold["targets"]),
              "source_turn_ids": sorted(gold["source_turn_ids"]), "truncated": False}
    assert first_feedback["source_repair_constraints"] == repair
    if corrected:
        second_feedback = json.loads(client.calls[2]["messages"][2]["content"])
        assert "repair" in second_feedback["error"].lower()
        assert "targets" in second_feedback["error"].lower()
        assert second_feedback["source_repair_constraints"] == repair
        assert second_feedback["instruction"] == first_feedback["instruction"]
        assert second_feedback["rejected_decision"] == {
            key: case["attempts"][1]["observed_decision"][key]
            for key in ("op", "add_as", "targets", "source_turn_ids")
        }
    assert real.usage() == Usage(calls=len(client.calls),
                                input_tokens=sum(a["input_tokens"] for a in case["attempts"]),
                                output_tokens=sum(a["output_tokens"] for a in case["attempts"]))


def assert_completed_adoption(case, cand, store, before_records, before_ops):
    expected = corrected_decision(case)
    state = store.item_state(cand.item)
    predecessor = next(record for record in before_records if record.status == "active")
    adopted = next(record for record in before_records if record.status == "proposed"
                   and record.record_id in expected["targets"])
    assert state.summary() == (cand.value, False, (), ())
    assert state.active.record_id == cand.candidate_id
    assert state.active.source_turn_ids == expected["source_turn_ids"]
    assert adopted.created_turn in state.active.source_turn_ids
    assert predecessor.created_turn not in state.active.source_turn_ids
    assert len(store.ops) == len(before_ops) + 1
    assert store.ops[:-1] == before_ops
    if case["system"] == "tracemem-controlled":
        assert state.active.supersedes == expected["targets"]
        assert state.previous_active.record_id == predecessor.record_id
        assert state.previous_active.source_turn_ids == predecessor.source_turn_ids
        assert next(record for record in store.records()
                    if record.record_id == adopted.record_id).status == "superseded"
    else:
        assert state.active.supersedes == []
        assert state.previous_active is None and state.history == []
        assert store.records() == [state.active]


def test_fixture_preserves_four_real_source_then_target_failures_with_original_feedback():
    assert FIXTURE["provenance"]["split"] == "dev"
    assert FIXTURE["provenance"]["run_id"] == "20261019T033733Z-evidence-precision-rerun"
    assert len(CASES) == len({case["case_id"] for case in CASES}) == 4
    assert {case["system"] for case in CASES} == set(STORES)
    for case in CASES:
        assert case["observed_errors"] == ["wrong_targets", "wrong_sources", "wrong_state"]
        timeline = pilot_timeline(case["scenario_id"])
        turns = {turn.id: turn for turn in timeline.scenario.turns()}
        turn_id = case["observation"]["turn_id"]
        assert datetime.fromisoformat(case["observation"]["when"]) == timeline.turn_times[turn_id]
        assert case["observation"]["speaker"] == turns[turn_id].speaker
        assert all(turns[tid].text == gloss for tid, gloss in case["turn_glosses"].items())
        cand = case["request"]["candidate"]
        scripted = next(c for c in timeline.candidates_by_turn[turn_id]
                        if c.candidate_id == cand["candidate_id"])
        assert cand == scripted.model_dump(mode="json")
        first, second = case["attempts"]
        assert second["call_sequence"] == first["call_sequence"] + 1
        assert first["feedback"] is None
        assert "extra sources" in second["feedback"]["error"]
        for attempt in case["attempts"]:
            assert json.loads(attempt["raw_reply"]) == attempt["observed_decision"]
            assert set(attempt["observed_decision"]) == DECISION_FIELDS
            assert set(attempt["observed_decision"]["source_turn_ids"]) <= set(case["turn_glosses"])
        original, evasion = first["observed_decision"], second["observed_decision"]
        gold = corrected_decision(case)
        assert set(original["targets"]) == set(gold["targets"])
        assert set(original["source_turn_ids"]) > set(gold["source_turn_ids"])
        assert set(evasion["targets"]) < set(original["targets"])
        assert not set(gold["source_turn_ids"]).issubset(evasion["source_turn_ids"])
        assert {key: case["observed_applied_operation"][key] for key in DECISION_FIELDS} == evasion


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_captured_source_error_then_target_loss_exhausts_without_applying_either_reply(case):
    cand, store = seeded_store(case)
    before_records, before_ops = store.records(), list(store.ops)
    real, client = source_repair_resolver(case)

    with pytest.raises(ResolverError) as caught:
        real.resolve(cand, store.records())

    assert caught.value.candidate_id == cand.candidate_id and caught.value.attempts == 2
    assert "repair" in caught.value.detail.lower() and "targets" in caught.value.detail.lower()
    assert_request_and_usage(case, real, client)
    assert store.records() == before_records and store.ops == before_ops


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_third_reply_can_repair_sources_and_preserve_selected_adoption_and_history(case):
    cand, store = seeded_store(case)
    before_records, before_ops = store.records(), list(store.ops)
    real, client = source_repair_resolver(case, corrected=True)

    resolved = real.resolve(cand, store.records())

    assert_request_and_usage(case, real, client, corrected=True)
    assert store.records() == before_records and store.ops == before_ops
    assert resolved.model_dump(include=DECISION_FIELDS) == corrected_decision(case)
    store.apply(resolved)
    assert_completed_adoption(case, cand, store, before_records, before_ops)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
@pytest.mark.parametrize("corrected", [False, True], ids=["exhausted", "corrected"])
def test_actual_failed_sequence_crosses_pipeline_without_leaving_an_unclosed_adoption(case, corrected):
    cand, store = seeded_store(case)
    before_records, before_ops = store.records(), list(store.ops)
    real, client = source_repair_resolver(case, corrected=corrected)
    timeline = pilot_timeline(case["scenario_id"])
    system = TraceMemPipeline(timeline.scenario.meta(), EmptyExtractor(), GoldMatcher(), real,
                              EmptyRetriever(), RuleAnswerer())
    system.log = store
    turn_id = case["observation"]["turn_id"]
    turn = next(turn for turn in timeline.scenario.turns() if turn.id == turn_id)

    system.observe(turn, timeline.turn_times[turn_id], gold_candidates=[cand])

    assert_request_and_usage(case, real, client, corrected=corrected)
    assert system.rejected_operations() == [] and system.candidates() == [cand]
    event, = system.resolver_events()
    assert event["candidate_id"] == cand.candidate_id
    assert event["attempts"] == (3 if corrected else 2)
    assert event["usage"] == real.usage().model_dump()
    if corrected:
        assert event["status"] == "applied" and event["error_type"] is None
        assert event["operation_id"] == f"op:{cand.candidate_id}"
        assert_completed_adoption(case, cand, store, before_records, before_ops)
    else:
        assert event["status"] == "generation_failed" and event["operation_id"] is None
        assert event["error_type"] == "ResolverError" and "repair" in event["error_detail"].lower()
        assert store.records() == before_records and store.ops == before_ops
