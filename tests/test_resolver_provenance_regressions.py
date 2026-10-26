"""Captured adoption-source omissions and a suggestion/dispute confusion, offline.

The invalid source replies must now trigger bounded retries. Corrected replies
are scripted from development replay: this tests validation, storage and evidence
flow, not a live model's semantic understanding. The captured macro-F1 FLAG remains
structurally legal, so its semantic correction is deliberately not an auto-rewrite.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest

from support import pilot_timeline
from tracemem.ops import OpLog
from tracemem.resolver import LLMResolver, ModelReply, ResolverConfig, ResolverError
from tracemem.schema import Candidate, Operation
from tracemem.systems.comparison import answer_context
from tracemem.systems.no_versions import CurrentOnlyStore


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "resolver_provenance_failures.json").read_text(encoding="utf-8")
)
CAPTURES = FIXTURE["resolver_captures"]
SOURCE_CASES = [case for case in CAPTURES if case["kind"] == "missing_proposal_source"]
DISPUTES = [case for case in CAPTURES if case["kind"] == "genuine_dispute"]
STORES = {"tracemem-controlled": OpLog, "tracemem-no-versions": CurrentOnlyStore}
DECISION_FIELDS = {"op", "add_as", "targets", "source_turn_ids", "reason", "rationale"}
CONFIG = ResolverConfig(model="offline-provenance", max_attempts=2)
SOURCE_ERROR = "adopting proposals or claims requires their creating turns in sources"


class ScriptedClient:
    def __init__(self, *replies):
        self.replies = replies
        self.calls = []

    def complete(self, **request):
        self.calls.append(copy.deepcopy(request))
        return ModelReply(content=json.dumps(self.replies[len(self.calls) - 1]))


def scripted_gold(scenario_id, candidate_id):
    operation = pilot_timeline(scenario_id).gold_op_for(candidate_id)
    assert operation is not None
    decision = operation.model_dump(include=DECISION_FIELDS)
    decision["rationale"] = "Scripted development replay decision; not a model prediction."
    return decision


def seeded_store(case):
    """Replay the saved actual prefix, including earlier errors, through public APIs."""
    candidate = Candidate.model_validate(case["request"]["candidate"])
    timeline = pilot_timeline(case["scenario_id"])
    speakers = {turn.id: turn.speaker for turn in timeline.scenario.turns()}
    store = STORES[case["system"]](candidate.project_id)
    for turn in timeline.turn_order:
        store.observe_turn(turn, timeline.turn_times[turn], speakers[turn])
        if turn == case["observation"]["turn_id"]:
            break
    for raw in case["prefix_operations"]:
        store.apply(Operation.model_validate(raw))
    assert [record.model_dump(mode="json") for record in store.records()] == case["request"]["related"]
    return candidate, store


def assert_saved_request(client, case):
    initial = client.calls[0]
    assert initial["config"] == CONFIG
    assert len(initial["messages"]) == 2
    assert json.loads(initial["messages"][1]["content"]) == case["request"]
    schema = initial["response_format"]["json_schema"]["schema"]
    assert set(schema["properties"]) == set(schema["required"]) == DECISION_FIELDS


def assert_source_feedback(client, case):
    assert client.calls[1]["messages"][:2] == client.calls[0]["messages"]
    assert len(client.calls[1]["messages"]) == 3
    feedback = json.loads(client.calls[1]["messages"][2]["content"])
    assert feedback["type"] == "resolver_validation_feedback"
    assert feedback["error"].startswith(SOURCE_ERROR)
    missing = {
        record["created_turn"] for record in case["request"]["related"]
        if record["record_id"] in case["observed_decision"]["targets"]
        and record["status"] in {"proposed", "contested"}
    } - set(case["observed_decision"]["source_turn_ids"])
    assert missing
    assert all(turn in feedback["error"] for turn in missing)
    assert feedback["target_constraints"] == case["request"]["target_constraints"]
    assert feedback["rejected_decision"] == {
        field: case["observed_decision"][field]
        for field in ("op", "add_as", "targets", "source_turn_ids")
    }
    assert not feedback["rejected_decision_truncated"]


def test_fixture_keeps_six_actual_source_omissions_and_both_sides_of_dispute_boundary():
    assert FIXTURE["provenance"]["split"] == "dev"
    assert len(CAPTURES) == len({case["case_id"] for case in CAPTURES}) == 9
    assert len(SOURCE_CASES) == 6
    assert len(DISPUTES) == 2
    assert {case["system"] for case in SOURCE_CASES} == set(STORES)
    for case in CAPTURES:
        candidate = case["request"]["candidate"]
        timeline = pilot_timeline(case["scenario_id"])
        turn = case["observation"]["turn_id"]
        expected = next(c for c in timeline.candidates_by_turn[turn]
                        if c.candidate_id == candidate["candidate_id"])
        assert candidate == expected.model_dump(mode="json")
        assert datetime.fromisoformat(case["observation"]["when"]) == timeline.turn_times[turn]
        assert set(case["observed_decision"]) == DECISION_FIELDS
    assert all(case["observed_errors"] == ["wrong_sources"] for case in SOURCE_CASES)


@pytest.mark.parametrize("case", SOURCE_CASES, ids=lambda case: case["case_id"])
def test_captured_adoption_omission_is_rejected_then_scripted_retry_preserves_origin(case):
    candidate, store = seeded_store(case)
    before_records = store.records()
    before_ops = list(store.ops)
    decision = scripted_gold(case["scenario_id"], candidate.candidate_id)
    client = ScriptedClient(case["observed_decision"], decision)
    resolver = LLMResolver(CONFIG, client)

    operation = resolver.resolve(candidate, store.records())

    assert len(client.calls) == resolver.usage().calls == 2
    assert_saved_request(client, case)
    assert_source_feedback(client, case)
    assert store.records() == before_records and store.ops == before_ops
    for field, value in decision.items():
        assert getattr(operation, field) == value

    store.apply(operation)
    state = store.item_state(candidate.item)
    assert state.active.record_id == candidate.candidate_id
    assert state.active.value == candidate.value
    assert state.active.source_turn_ids == decision["source_turn_ids"]
    assert not state.proposed and not state.contested and not state.flagged
    adopted = [record for record in before_records
               if record.record_id in operation.targets and record.status in {"proposed", "contested"}]
    assert len(adopted) == 1
    assert adopted[0].created_turn in state.active.source_turn_ids
    context, allowed_sources = answer_context(store.records(), 12000)
    assert f"{candidate.item} = {candidate.value} [active]" in context
    assert set(decision["source_turn_ids"]).issubset(allowed_sources)
    if case["system"] == "tracemem-controlled":
        assert state.active.supersedes == operation.targets
        previous = next((record for record in before_records if record.status == "active"), None)
        assert (state.previous_active.record_id if state.previous_active else None) == (
            previous.record_id if previous else None
        )
        assert next(record for record in store.records() if record.record_id == adopted[0].record_id).status == "superseded"
    else:
        # The origin must remain readable even though the adopted open record was dropped.
        assert state.history == [] and state.previous_active is None
        assert state.active.supersedes == []
        assert store.records() == [state.active]


@pytest.mark.parametrize("case", SOURCE_CASES, ids=lambda case: case["case_id"])
def test_repeated_captured_omission_fails_without_automatic_sources_or_store_mutation(case):
    candidate, store = seeded_store(case)
    before_records = store.records()
    before_ops = list(store.ops)
    client = ScriptedClient(case["observed_decision"], case["observed_decision"])
    resolver = LLMResolver(CONFIG, client)

    with pytest.raises(ResolverError) as caught:
        resolver.resolve(candidate, store.records())

    assert caught.value.candidate_id == candidate.candidate_id
    assert caught.value.attempts == resolver.usage().calls == len(client.calls) == 2
    assert caught.value.detail.startswith(SOURCE_ERROR)
    assert_saved_request(client, case)
    assert_source_feedback(client, case)
    assert store.records() == before_records and store.ops == before_ops


def test_captured_macro_f1_flag_is_a_semantic_error_and_scripted_proposal_preserves_accuracy():
    case = next(case for case in CAPTURES if case["kind"] == "suggestion_as_dispute")
    candidate, wrong_store = seeded_store(case)
    wrong_client = ScriptedClient(case["observed_decision"])
    wrong = LLMResolver(CONFIG, wrong_client).resolve(candidate, wrong_store.records())
    assert wrong.op == "FLAG" and len(wrong_client.calls) == 1
    wrong_store.apply(wrong)
    assert wrong_store.item_state(candidate.item).flagged

    candidate, corrected = seeded_store(case)
    active_before = corrected.item_state(candidate.item).active
    client = ScriptedClient(scripted_gold(case["scenario_id"], candidate.candidate_id))
    proposal = LLMResolver(CONFIG, client).resolve(candidate, corrected.records())
    assert (proposal.op, proposal.add_as, proposal.targets) == ("ADD", "proposed", [])
    corrected.apply(proposal)
    state = corrected.item_state(candidate.item)
    assert state.active == active_before
    assert state.active.value == "accuracy"
    assert [(record.value, record.status) for record in state.proposed] == [("macro-F1", "proposed")]
    assert not state.flagged and not state.contested
    assert len(client.calls) == 1


@pytest.mark.parametrize("system", STORES)
def test_scripted_metric_suggestion_acceptance_and_replacement_keep_full_source_chain(system):
    timeline = pilot_timeline("pilot-01")
    store = STORES[system](timeline.scenario.project_id)
    speakers = {turn.id: turn.speaker for turn in timeline.scenario.turns()}
    for turn in timeline.turn_order:
        store.observe_turn(turn, timeline.turn_times[turn], speakers[turn])
        for candidate in timeline.candidates_by_turn.get(turn, []):
            if candidate.item != "metric.primary":
                continue
            client = ScriptedClient(scripted_gold("pilot-01", candidate.candidate_id))
            operation = LLMResolver(CONFIG, client).resolve(candidate, store.records(candidate.item))
            assert len(client.calls) == 1
            store.apply(operation)
            state = store.item_state(candidate.item)
            assert not state.flagged and not state.contested
            if turn == "S3-T3":  # "accuracy will flatter us. Should we use macro-F1?"
                assert state.active.value == "accuracy"
                assert state.active.source_turn_ids == ["S1-T3", "S1-T2"]
                assert [record.value for record in state.proposed] == ["macro-F1"]

    state = store.item_state("metric.primary")
    assert state.active.value == "macro-F1"
    assert state.active.source_turn_ids == ["S3-T4", "S3-T3", "S4-T1"]
    assert state.creating_turns[state.active.record_id] == ["S3-T4", "S3-T3"]
    assert state.kept_turns[state.active.record_id] == ["S4-T1"]  # "keeping macro-F1 as primary"
    assert not state.proposed
    expected = timeline.log_after_session["S4"].records("metric.primary")
    if system == "tracemem-controlled":
        assert store.records() == expected
        assert state.previous_active.value == "accuracy"
        assert state.previous_active.source_turn_ids == ["S1-T3", "S1-T2"]
        assert state.active.supersedes == ["metric.primary@S1-T3", "metric.primary@S3-T3"]
        before_switch = store.upto("S3-T3").item_state("metric.primary")
        assert before_switch.active.value == "accuracy" and not before_switch.flagged
        assert [record.value for record in before_switch.proposed] == ["macro-F1"]
    else:
        assert state.history == [] and state.previous_active is None
        assert store.records() == [record.model_copy(update={"supersedes": []})
                                   for record in expected if record.status == "active"]


@pytest.mark.parametrize("case", DISPUTES, ids=lambda case: case["case_id"])
def test_captured_genuine_competing_claim_still_flags_and_does_not_require_active_origin(case):
    candidate, store = seeded_store(case)
    active_before = store.item_state(candidate.item).active
    client = ScriptedClient(case["observed_decision"])
    operation = LLMResolver(CONFIG, client).resolve(candidate, store.records())
    assert_saved_request(client, case)
    assert len(client.calls) == 1
    assert operation.op == scripted_gold(case["scenario_id"], candidate.candidate_id)["op"] == "FLAG"
    assert operation.targets == [active_before.record_id]
    assert operation.source_turn_ids == candidate.source_turn_ids
    store.apply(operation)
    state = store.item_state(candidate.item)
    assert state.active == active_before
    assert state.flagged and not state.proposed
    assert [record.value for record in state.contested] == [candidate.value]
