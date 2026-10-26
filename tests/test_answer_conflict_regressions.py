"""Replay real reader failures and check the shared status-before-evidence prompt.

Scripted corrections are offline contract checks, not evidence that a live model
will comply. The captured false certainty now triggers a bounded evidence retry;
the reader does not silently override it or fabricate a conflict answer.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest

from support import pilot_timeline
from tracemem.ops import OpLog
from tracemem.resolver import ModelReply, ResolverConfig
from tracemem.schema import Operation, Record, SystemQuestion, Turn
from tracemem.systems import comparison
from tracemem.systems.no_versions import CurrentOnlyStore


CAPTURE = json.loads((Path(__file__).parent / "fixtures" / "answer_conflict_failures.json").read_text(encoding="utf-8"))
CONFIG = ResolverConfig(model="offline-answer-conflict", max_attempts=2)


class ScriptedClient:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def complete(self, **request):
        self.calls.append(copy.deepcopy(request))
        return ModelReply(content=json.dumps(self.reply))


def decision(value=None, sources=(), *, status="answer"):
    return {"status": status, "value": value, "cited_turn_ids": list(sources),
            "text": "Scripted state and evidence selection; no live model is evaluated."}


def record(turn, value, status="active", *, item="choice", sources=None):
    session, number = (int(part[1:]) for part in turn.split("-"))
    return Record(record_id=f"private:{item}:{turn}", project_id="synthetic-project",
                  item=item, value=value, status=status, source_turn_ids=list(sources or [turn]),
                  speakers=["Analyst"], created_turn=turn,
                  created_at=datetime(2026, 1, session, 10, number))


def answer(records, reply, *, asked=None, expected_payload=None, rejected=False):
    asked = asked or {"kind": "current", "text": "Which choice is current?", "session": None}
    question = SystemQuestion(question_id="opaque-question", scenario_id="opaque-scenario", **asked)
    before = [row.model_dump() for row in records]
    client = ScriptedClient(reply)
    reader = comparison.SharedAnswerer(CONFIG, client, 12000)
    result = reader.answer(question, records, {
        "S9-T9": Turn(id="S9-T9", speaker="Analyst", text="RAW_TURN_MUST_NOT_ENTER_CONTEXT"),
    })
    assert result.usage.calls == reader.usage().calls == len(client.calls) == (2 if rejected else 1)
    request = client.calls[0]
    assert request["messages"][0] == {"role": "system", "content": comparison.ANSWER_PROMPT}
    assert comparison.ANSWER_PROMPT.endswith(comparison.ANSWER_EVIDENCE_CHECK)
    assert request["response_format"] == comparison.ANSWER_FORMAT
    assert set(request["response_format"]["json_schema"]["schema"]["properties"]) == {
        "status", "value", "cited_turn_ids", "text",
    }
    context, sources = comparison.answer_context(records, 12000)
    payload = json.loads(request["messages"][1]["content"])
    assert payload == {"question": asked, "context": context, "allowed_source_turn_ids": sources}
    if expected_payload is not None:
        assert payload == expected_payload
    assert "RAW_TURN_MUST_NOT_ENTER_CONTEXT" not in context
    assert "private:" not in context and "supersedes" not in context
    assert result.context_turn_ids == sources
    assert [row.model_dump() for row in records] == before
    if rejected:
        assert result.status == "abstain" and result.value is None and result.cited_turn_ids == []
        assert client.calls[1]["messages"][:2] == request["messages"]
        assert json.loads(client.calls[1]["messages"][-1]["content"])["validation_error"]
    else:
        for field, expected in reply.items():
            assert getattr(result, field) == expected
    return result, payload


@pytest.mark.parametrize("case", CAPTURE["cases"], ids=lambda case: case["id"])
def test_saved_operations_reproduce_the_actual_failed_request_without_gold_records(case):
    store_type = OpLog if case["provenance"]["system"] == "tracemem-controlled" else CurrentOnlyStore
    store = store_type(case["project_id"])
    for observation in case["observations"]:
        store.observe_turn(observation["turn_id"], datetime.fromisoformat(observation["when"]),
                           observation["speaker"])
        for row in case["prefix_operations"]:
            if row["turn_id"] == observation["turn_id"]:
                store.apply(Operation.model_validate(row))
    assert [row.model_dump(mode="json") for row in store.records()] == case["records"]
    context, sources = comparison.answer_context(store.records(), 12000)
    assert context == case["request"]["context"]
    assert sources == case["request"]["allowed_source_turn_ids"]
    state = store.item_state("dataset.train")
    assert state.active.value == "IMDB" and state.flagged
    assert [claim.value for claim in state.contested] == ["SST-2"]
    assert case["provenance"]["split"] == "dev"
    assert case["provenance"]["run"] == "20261019T033733Z-evidence-precision-rerun"


@pytest.mark.parametrize("case", CAPTURE["cases"], ids=lambda case: case["id"])
def test_real_active_overrides_dispute_answer_is_rejected_after_bounded_attempts(case):
    result, _ = answer([Record.model_validate(row) for row in case["records"]],
                       case["observed_decision"], asked=case["request"]["question"],
                       expected_payload=case["request"], rejected=True)
    expected = pilot_timeline(case["scenario_id"]).expected[case["question_id"]]
    assert result.status == "abstain" and result.value is None
    assert case["observed_decision"]["status"] == "answer" and case["observed_decision"]["value"] == "IMDB"
    assert expected.expected_status == "conflict" and expected.expected_value is None
    assert set(expected.required_support) - set(case["observed_decision"]["cited_turn_ids"]) == {"S2-T1"}
    # S2-T1 ('I thought we agreed on SST-2 ... not IMDB') is visible and contested.


@pytest.mark.parametrize("case", CAPTURE["cases"], ids=lambda case: case["id"])
def test_scripted_conflict_uses_both_visible_claims_and_ignores_other_item_sources(case):
    result, payload = answer([Record.model_validate(row) for row in case["records"]],
                             case["corrected_decision"], asked=case["request"]["question"],
                             expected_payload=case["request"])
    expected = pilot_timeline(case["scenario_id"]).expected[case["question_id"]]
    assert result.status == expected.expected_status == "conflict" and result.value is None
    assert set(result.cited_turn_ids) == set(expected.required_support)
    assert "S2-T3" in payload["allowed_source_turn_ids"] and "S2-T3" not in result.cited_turn_ids
    # S2-T3 ('label audit is blocked') concerns the task, not the dataset dispute.


@pytest.mark.parametrize(("records", "reply"), [
    ([record("S1-T1", "X"), record("S2-T1", "Y", "proposed")],
     decision("X", ["S1-T1"])),
    ([record("S1-T1", "X"), record("S2-T1", "Y", "proposed"),
      record("S2-T2", "Y", "contested")],
     decision(sources=["S1-T1", "S2-T2"], status="conflict")),
    ([record("S2-T1", "Y", "contested")],
     decision(sources=["S2-T1"], status="conflict")),
    ([record("S1-T1", "X"), record("S2-T1", "Y", "contested", item="other-choice")],
     decision("X", ["S1-T1"])),
    ([record("S1-T1", "X"), record("S2-T1", "Y", "declined")],
     decision("X", ["S1-T1"])),
    ([record("S1-T1", "Y", "superseded"), record("S2-T1", "X")],
     decision("X", ["S2-T1"])),
    ([record("S1-T1", "cancelled"), record("S2-T1", "open", "proposed")],
     decision("cancelled", ["S1-T1"])),
    ([record("S1-T1", "completed"), record("S2-T1", "open", "proposed")],
     decision("completed", ["S1-T1"])),
    ([record("S1-T1", "cancelled", "superseded"), record("S2-T1", "open")],
     decision("open", ["S2-T1"])),
], ids=["proposal", "same-value-proposal-and-claim", "claim-without-visible-active",
        "other-item", "declined-claim", "old-version", "restart-proposal",
        "completed-restart-proposal", "adopted-reopening"])
def test_explicit_state_boundaries_are_scripted_contracts_not_hidden_answer_overrides(records, reply):
    answer(records, reply)


@pytest.mark.parametrize(("kind", "session", "reply"), [
    ("current", None, decision(sources=["S1-T1", "S2-T1"], status="conflict")),
    ("as_of", "S1", decision("X", ["S1-T1"])),
    ("as_of", "S2", decision(sources=["S1-T1", "S2-T1"], status="conflict")),
])
def test_requested_time_controls_whether_visible_claim_is_part_of_the_dispute(kind, session, reply):
    answer([record("S1-T1", "X"), record("S2-T1", "Y", "contested")], reply,
           asked={"kind": kind, "text": "What was the choice at the requested time?", "session": session})


def test_closed_claim_without_resolution_time_does_not_supply_a_past_dispute_timeline():
    records = [record("S1-T1", "X", sources=["S1-T1", "S3-T1"]),
               record("S2-T1", "Y", "declined")]
    result, _ = answer(records, decision(status="abstain"),
                       asked={"kind": "as_of", "text": "What was the choice in S2?", "session": "S2"})
    assert result.status == "abstain"


@pytest.mark.parametrize(("later_text", "reply"), [
    ("The team disagrees about the current choice: one recalls X, another says Y was agreed. "
     "The disagreement is unresolved.", decision(sources=["S1-T1", "S2-T1"], status="conflict")),
    ("Could we consider Y instead? No decision to change X has been made.",
     decision("X", ["S1-T1"])),
    ("We decided to replace X with Y from now on.", decision("Y", ["S2-T1"])),
])
def test_native_storage_event_names_do_not_replace_textual_intent(later_text, reply):
    records = [record("S1-T1", json.dumps({"mem0_history": "ADD", "before": None,
                                          "after": "The team decided to use X."}), None),
               record("S2-T1", json.dumps({"mem0_history": "UPDATE", "before": "The team decided to use X.",
                                          "after": later_text}), None)]
    _, payload = answer(records, reply)
    assert "[active]" not in payload["context"] and "[contested]" not in payload["context"]


@pytest.mark.parametrize(("kind", "session", "reply"), [
    ("current", None, decision("X", ["S3-T1"])),
    ("as_of", "S2", decision(sources=["S1-T1", "S2-T1"], status="conflict")),
])
def test_native_explicit_resolution_can_close_current_dispute_without_erasing_past(kind, session, reply):
    records = [record("S1-T1", "The team decided to use X.", None),
               record("S2-T1", "At S2 the choice is disputed: some recall X, others Y; no resolution yet.", None),
               record("S3-T1", "At S3 we checked the notes and resolved the earlier X/Y disagreement: X is confirmed.", None)]
    answer(records, reply, asked={"kind": kind, "text": "What was the choice at the requested time?",
                                 "session": session})


def test_final_check_requires_status_before_settled_citation_pruning_for_all_formats():
    check = " ".join(comparison.ANSWER_EVIDENCE_CHECK.split())
    assert check.index("0. Decide the requested item's state") < check.index("1. PREVIOUS")
    assert "CURRENT with status=answer needs the settled decision" in check
    assert "Do not apply the settled-value citation rules below until status=answer is justified" in check
    assert "For conflict, retain the competing evidence." in check
    assert "An explicit, unresolved disagreement in retained text takes precedence" in comparison.ANSWER_STATE_GUIDE
    assert "do not reconstruct disagreement that native storage did not preserve" in comparison.ANSWER_STATE_GUIDE
