"""Replay all eight real development write failures without a model or network.

The fixture preserves the actual visible state, including earlier bad choices.
Corrected replies are deliberately scripted: these tests establish feedback and
contract behavior, not that a live model will choose the correction on a rerun.
"""

from __future__ import annotations

import copy
import json
from datetime import timedelta
from pathlib import Path

import pytest

from tracemem.ops import OpLog
from tracemem.resolver import LLMResolver, ModelReply, ResolverConfig, ResolverError
from tracemem.schema import Candidate, Operation, Record


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "resolver_failures.json").read_text(encoding="utf-8")
)
CASES = FIXTURE["cases"]
ATTEMPTS = [
    pytest.param(case, attempt, id=f"{case['case_id']}:attempt-{index}")
    for case in CASES
    for index, attempt in enumerate(case["invalid_attempts"], start=1)
]


def seeded_log(case: dict) -> tuple[Candidate, OpLog]:
    """Build the saved state through public operations, never mutable internals."""
    candidate = Candidate.model_validate(case["candidate"])
    records = [Record.model_validate(raw) for raw in case["related"]]
    log = OpLog(candidate.project_id)
    for rec in records:
        for index, turn in enumerate(rec.source_turn_ids):
            log.observe_turn(turn, rec.created_at, rec.speakers[index])
        assert rec.status in {"active", "proposed", "contested"}
        log.apply(Operation(
            op_id=f"fixture:{rec.record_id}",
            op="FLAG" if rec.status == "contested" else "ADD",
            turn_id=rec.created_turn,
            item=rec.item,
            value=rec.value,
            add_as=None if rec.status == "contested" else rec.status,
            targets=rec.supersedes,
            source_turn_ids=rec.source_turn_ids,
            reason=rec.reason,
        ))
    assert [r.model_dump(mode="json") for r in log.records()] == case["related"]
    for turn in candidate.source_turn_ids:
        log.observe_turn(turn, max(r.created_at for r in records) + timedelta(days=1), candidate.speaker)
    return candidate, log


def assert_constraints(case: dict, constraints: dict) -> None:
    """Check the choices that matter in the saved failures against fixed states."""
    active_id = case["expected_previous_active"]
    assert constraints["active_record_id"] == active_id
    options = {(option["op"], option["add_as"]): option for option in constraints["options"]}
    assert len(options) == len(constraints["options"])
    assert options[("ADD", "proposed")]["required_targets"] == []
    assert options[("ADD", "proposed")]["optional_targets"] == []
    if active_id is None:
        assert set(options) == {("ADD", "active"), ("ADD", "proposed")}
        assert options[("ADD", "active")]["required_targets"] == []
        # Only the restarted-audit case has an existing proposal for its value.
        expected_optional = (
            ["task.label_audit@S1-T3"]
            if case["candidate"]["candidate_id"] == "task.label_audit@S3-T2"
            else []
        )
        assert options[("ADD", "active")]["optional_targets"] == expected_optional
    else:
        assert set(options) == {("ADD", "proposed"), ("SUPERSEDE", None), ("FLAG", None)}
        for op in ("SUPERSEDE", "FLAG"):
            assert options[(op, None)]["required_targets"] == ["model.baseline@S1-T1"]
            # The naive Bayes dispute has a different value from linear SVM.
            assert options[(op, None)]["optional_targets"] == []


class RegressionClient:
    def __init__(self, case: dict, replies: list[str], first_error: str):
        self.case = case
        self.replies = replies
        self.first_error = first_error
        self.calls: list[dict] = []

    def complete(self, **kwargs) -> ModelReply:
        self.calls.append(copy.deepcopy(kwargs))
        messages = kwargs["messages"]
        initial = json.loads(messages[1]["content"])
        assert initial["candidate"] == self.case["candidate"]
        assert initial["related"] == self.case["related"]
        assert_constraints(self.case, initial["target_constraints"])
        if len(self.calls) == 2:
            assert len(messages) == 3
            assert messages[:2] == self.calls[0]["messages"]
            assert messages[2]["role"] == "user"
            feedback = json.loads(messages[2]["content"])
            assert feedback["type"] == "resolver_validation_feedback"
            assert feedback["error"] == self.first_error
            assert feedback["target_constraints"] == initial["target_constraints"]
            rejected = json.loads(self.replies[0])
            assert feedback["rejected_decision"] == {
                field: rejected[field] for field in ("op", "add_as", "targets", "source_turn_ids")
            }
            assert feedback["instruction"]
        return ModelReply(content=self.replies[len(self.calls) - 1])


def test_fixture_covers_every_final_development_write_failure():
    assert FIXTURE["provenance"]["split"] == "dev"
    assert len(CASES) == 8
    assert len({case["case_id"] for case in CASES}) == 8
    assert sum(case["system"] == "tracemem-controlled" for case in CASES) == 5
    assert sum(case["system"] == "tracemem-no-versions" for case in CASES) == 3
    assert all(len(case["invalid_attempts"]) == 2 for case in CASES)


@pytest.mark.parametrize("case,attempt", ATTEMPTS)
def test_observed_invalid_reply_gets_actionable_feedback_and_scripted_correction(case, attempt):
    candidate, log = seeded_log(case)
    before = [r.model_dump() for r in log.records()]
    before_count = len(log.ops)
    client = RegressionClient(case, [attempt["response"], json.dumps(case["corrected_decision"])],
                              attempt["error"])
    resolver = LLMResolver(ResolverConfig(model="offline-regression", max_attempts=2), client)

    operation = resolver.resolve(candidate, log.records())

    # Resolution cannot silently rewrite the store or coerce the invalid choice.
    assert len(client.calls) == resolver.usage().calls == 2
    assert len(log.ops) == before_count
    assert [r.model_dump() for r in log.records()] == before
    for field in ("op", "add_as", "targets", "source_turn_ids", "reason", "rationale"):
        assert getattr(operation, field) == case["corrected_decision"][field]

    log.apply(operation)
    state = log.item_state(candidate.item)
    assert state.active is not None
    assert state.active.value == candidate.value
    assert state.active.record_id == candidate.candidate_id
    assert state.active.source_turn_ids == case["corrected_decision"]["source_turn_ids"]
    assert state.active.supersedes == case["corrected_decision"]["targets"]
    assert not state.flagged
    assert (state.previous_active.record_id if state.previous_active else None) == case["expected_previous_active"]
    actual_existing = {
        record.record_id: record.status for record in log.records()
        if record.record_id != candidate.candidate_id
    }
    assert actual_existing == case["expected_existing_statuses"]
    assert {record.record_id for record in state.history} == {
        record_id for record_id, status in case["expected_existing_statuses"].items()
        if status in {"superseded", "declined"}
    }


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_original_two_bad_attempts_still_fail_without_fallback_or_store_mutation(case):
    candidate, log = seeded_log(case)
    before = [r.model_dump() for r in log.records()]
    before_ops = list(log.ops)
    attempts = case["invalid_attempts"]
    client = RegressionClient(case, [attempt["response"] for attempt in attempts], attempts[0]["error"])
    resolver = LLMResolver(ResolverConfig(model="offline-regression", max_attempts=2), client)

    with pytest.raises(ResolverError) as caught:
        resolver.resolve(candidate, log.records())

    assert caught.value.candidate_id == candidate.candidate_id
    assert caught.value.attempts == 2
    assert caught.value.detail == attempts[-1]["error"]
    assert len(client.calls) == resolver.usage().calls == 2
    assert log.ops == before_ops
    assert [r.model_dump() for r in log.records()] == before
