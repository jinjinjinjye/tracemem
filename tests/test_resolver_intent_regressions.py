"""Replay accepted-but-wrong development decisions with an offline scripted client.

The original replies satisfied validation when captured. The reopening reply also
omits an adopted proposal's source and is now rejected by the provenance guard.
Tests preserve the captured state effects and verify the instructions and effects
of scripted corrections. They do not measure a live model's intent recognition.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tracemem.ops import OpLog
from tracemem.resolver import INTENT_GUIDE, LLMResolver, ModelReply, ResolverConfig, ResolverError
from tracemem.schema import Candidate, Operation, Record


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "resolver_intent_failures.json").read_text(encoding="utf-8")
)
CASES = FIXTURE["cases"]
BY_ID = {case["case_id"]: case for case in CASES}
DECISION_FIELDS = {"op", "add_as", "targets", "source_turn_ids", "reason", "rationale"}


def seeded_log(case: dict) -> tuple[Candidate, OpLog]:
    """Recreate the captured visible state with public operations, including errors."""
    candidate = Candidate.model_validate(case["candidate"])
    log = OpLog(candidate.project_id)
    records = [Record.model_validate(raw) for raw in case["related"]]
    for record in records:
        assert record.status in {"active", "proposed"}
        for index, turn in enumerate(record.source_turn_ids):
            log.observe_turn(turn, record.created_at, record.speakers[index])
        log.apply(Operation(
            op_id=f"fixture:{record.record_id}", op="ADD", turn_id=record.created_turn,
            item=record.item, value=record.value, add_as=record.status,
            targets=record.supersedes, source_turn_ids=record.source_turn_ids,
            reason=record.reason,
        ))
    assert [record.model_dump(mode="json") for record in log.records()] == case["related"]
    when = max((record.created_at for record in records), default=datetime(2026, 10, 1))
    for turn in candidate.source_turn_ids:
        log.observe_turn(turn, when + timedelta(days=1), candidate.speaker)
    return candidate, log


class ScriptedClient:
    def __init__(self, candidate: Candidate, records: list[Record], decision: dict):
        self.candidate = candidate.model_dump(mode="json")
        self.records = [record.model_dump(mode="json") for record in records]
        self.decision = decision
        self.calls: list[dict] = []

    def complete(self, **request):
        self.calls.append(copy.deepcopy(request))
        messages = request["messages"]
        if len(self.calls) == 1:
            assert len(messages) == 2
        else:
            assert len(messages) == 3
            assert messages[:2] == self.calls[0]["messages"]
            feedback = json.loads(messages[2]["content"])
            assert feedback["type"] == "resolver_validation_feedback"
            assert "creating turns in sources" in feedback["error"]
            assert feedback["rejected_decision"] == {
                field: self.decision[field] for field in ("op", "add_as", "targets", "source_turn_ids")
            }
        assert messages[0]["role"] == "system"
        prompt = messages[0]["content"]
        assert INTENT_GUIDE in prompt
        assert prompt.index(INTENT_GUIDE) < prompt.index("target_constraints lists")
        assert messages[1]["role"] == "user"
        payload = json.loads(messages[1]["content"])
        # Test expectations and development outcome labels must not reach the model.
        assert set(payload) == {"candidate", "related", "target_constraints"}
        assert payload["candidate"] == self.candidate
        assert payload["related"] == self.records
        assert payload["target_constraints"]["active_record_id"] == next(
            (record["record_id"] for record in self.records if record["status"] == "active"), None
        )
        schema = request["response_format"]["json_schema"]["schema"]
        assert set(schema["properties"]) == DECISION_FIELDS
        assert set(schema["required"]) == DECISION_FIELDS
        return ModelReply(content=json.dumps(self.decision))


def resolve_scripted(candidate: Candidate, log: OpLog, decision: dict) -> Operation:
    before_records = [record.model_dump() for record in log.records()]
    before_ops = list(log.ops)
    client = ScriptedClient(candidate, log.records(), decision)
    resolver = LLMResolver(ResolverConfig(model="offline-intent-regression", max_attempts=2), client)

    operation = resolver.resolve(candidate, log.records())

    # Semantic failures can be structurally legal: no validation retry is triggered.
    assert len(client.calls) == resolver.usage().calls == 1
    assert [record.model_dump() for record in log.records()] == before_records
    assert log.ops == before_ops
    for field in DECISION_FIELDS:
        assert getattr(operation, field) == decision[field]
    assert operation.candidate_id == candidate.candidate_id
    assert operation.value == candidate.value
    return operation


def assert_state(log: OpLog, candidate: Candidate, case: dict, prefix: str) -> None:
    state = log.item_state(candidate.item)
    assert (state.active.record_id if state.active else None) == case[f"{prefix}_active_id"]
    assert state.flagged is case[f"{prefix}_flagged"]
    assert {record.record_id: record.status for record in log.records()} == case[f"{prefix}_record_statuses"]
    newest = next(record for record in log.records() if record.record_id == candidate.candidate_id)
    assert newest.source_turn_ids == candidate.source_turn_ids
    assert newest.value == candidate.value


def test_fixture_preserves_eight_originally_accepted_semantic_failures_and_a_real_dispute_control():
    assert FIXTURE["provenance"]["split"] == "dev"
    assert len(CASES) == len(BY_ID) == 9
    assert sum(case["observed_is_semantic_failure"] for case in CASES) == 8
    assert {case["expected_intent"] for case in CASES} == {"settled", "suggestion", "dispute"}
    assert {case["system"] for case in CASES} == {"tracemem-controlled", "tracemem-no-versions"}
    for case in CASES:
        assert set(case["observed_decision"]) == set(case["corrected_decision"]) == DECISION_FIELDS


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_observed_reply_preserves_captured_state_effects_and_current_validation(case):
    candidate, log = seeded_log(case)
    if case["case_id"] == "reopening_question_is_unconfirmed":
        before_records, before_ops = log.records(), list(log.ops)
        client = ScriptedClient(candidate, log.records(), case["observed_decision"])
        real = LLMResolver(ResolverConfig(model="offline-intent-regression", max_attempts=2), client)
        with pytest.raises(ResolverError, match="creating turns in sources") as caught:
            real.resolve(candidate, log.records())
        assert len(client.calls) == real.usage().calls == caught.value.attempts == 2
        assert log.records() == before_records and log.ops == before_ops
        adopted = next(record for record in before_records if record.status == "proposed")
        assert adopted.record_id in case["observed_decision"]["targets"]
        assert adopted.created_turn not in case["observed_decision"]["source_turn_ids"]
        assert adopted.created_turn in caught.value.detail
        # Replay the previously accepted public operation solely to preserve the
        # original semantic failure evidence, not as a Resolver failure fallback.
        operation = Operation(op_id=f"captured:{candidate.candidate_id}",
                              candidate_id=candidate.candidate_id, item=candidate.item,
                              value=candidate.value, turn_id=candidate.source_turn_ids[0],
                              **case["observed_decision"])
    else:
        operation = resolve_scripted(candidate, log, case["observed_decision"])

    log.apply(operation)

    assert_state(log, candidate, case, "observed")
    observed = (case["observed_active_id"], case["observed_flagged"], case["observed_record_statuses"])
    corrected = (case["expected_active_id"], case["expected_flagged"], case["expected_record_statuses"])
    assert (observed != corrected) is case["observed_is_semantic_failure"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_scripted_correction_keeps_suggestions_separate_and_commits_real_task_status(case):
    candidate, log = seeded_log(case)
    operation = resolve_scripted(candidate, log, case["corrected_decision"])

    log.apply(operation)

    assert_state(log, candidate, case, "expected")


def test_scripted_task_commitment_cancellation_and_reopening_proposal_lifecycle():
    lifecycle = FIXTURE["task_lifecycle"]
    commitment = BY_ID[lifecycle["commitment_case_id"]]
    candidate, log = seeded_log(commitment)
    log.apply(resolve_scripted(candidate, log, commitment["corrected_decision"]))
    assert log.item_state(candidate.item).active.value == "open"
    assert not log.item_state(candidate.item).proposed

    cancellation = lifecycle["cancellation"]
    cancel_candidate = Candidate.model_validate(cancellation["candidate"])
    for turn in cancel_candidate.source_turn_ids:
        log.observe_turn(turn, datetime(2026, 10, 20), cancel_candidate.speaker)
    log.apply(resolve_scripted(cancel_candidate, log, cancellation["corrected_decision"]))
    state = log.item_state(candidate.item)
    assert state.active.value == "cancelled"
    assert state.previous_active.record_id == candidate.candidate_id
    assert state.previous_active.status == "superseded"
    assert not state.proposed

    reopening = BY_ID[lifecycle["reopening_case_id"]]
    reopen_candidate = Candidate.model_validate(reopening["candidate"])
    for turn in reopen_candidate.source_turn_ids:
        log.observe_turn(turn, datetime(2026, 10, 21), reopen_candidate.speaker)
    log.apply(resolve_scripted(reopen_candidate, log, reopening["corrected_decision"]))

    state = log.item_state(candidate.item)
    assert state.active.record_id == cancel_candidate.candidate_id
    assert state.active.value == "cancelled"
    assert state.active.reason == "the report deadline moved up"
    assert state.previous_active.record_id == candidate.candidate_id
    assert [(record.record_id, record.value) for record in state.proposed] == [
        (reopen_candidate.candidate_id, "open")
    ]
    assert not state.flagged
    assert [operation.op for operation in log.ops] == ["ADD", "SUPERSEDE", "ADD"]
    assert [record.record_id for record in state.history] == [candidate.candidate_id]
