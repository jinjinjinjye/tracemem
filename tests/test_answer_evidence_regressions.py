"""Offline evidence-selection regressions from the provenance development run.

Current linked-origin omissions now trigger bounded validation retries. Historical
replacement selection still relies on the shared prompt. Scripted corrections
exercise the visible context and contract, not live-model accuracy.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest

from support import pilot_timeline
from tracemem.resolver import ModelReply, ResolverConfig
from tracemem.schema import Record, SystemQuestion, Turn
from tracemem.systems import comparison


CAPTURE = json.loads((Path(__file__).parent / "fixtures" / "answer_evidence_failures.json").read_text(encoding="utf-8"))
CONFIG = ResolverConfig(model="offline-answer-evidence", max_attempts=2)


class ScriptedClient:
    def __init__(self, decision):
        self.decision = decision
        self.calls = []

    def complete(self, **request):
        self.calls.append(copy.deepcopy(request))
        return ModelReply(content=json.dumps(self.decision))


def decision(value=None, sources=(), *, status="answer"):
    return {"status": status, "value": value, "cited_turn_ids": list(sources),
            "text": "Scripted evidence selection; no live model is evaluated."}


def question(kind="current", *, text="Which option is current?", session=None):
    return SystemQuestion(question_id="opaque-question", scenario_id="opaque-scenario",
                          kind=kind, text=text, session=session)


def record(turn, value, status="active", *, sources=None, item="selection", supersedes=()):
    session, number = (int(part[1:]) for part in turn.split("-"))
    return Record(
        record_id=f"private:{item}:{turn}", project_id="synthetic-project", item=item,
        value=value, status=status, source_turn_ids=list(sources or [turn]), speakers=["Analyst"],
        created_turn=turn, created_at=datetime(2026, 1, session, 10, number), supersedes=list(supersedes),
    )


def answer(records, reply, *, asked=None, budget=12000, expected_payload=None, rejected=False):
    asked = asked or question()
    before = [row.model_dump() for row in records]
    client = ScriptedClient(reply)
    reader = comparison.SharedAnswerer(CONFIG, client, budget)
    result = reader.answer(asked, records, {
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
    context, sources = comparison.answer_context(records, budget)
    payload = json.loads(request["messages"][1]["content"])
    expected = {
        "question": {"text": asked.text, "kind": asked.kind, "session": asked.session},
        "context": context, "allowed_source_turn_ids": sources,
    }
    shown = len(comparison._selected_context(records, budget)[2])
    if asked.kind in ("previous", "as_of") and shown < len(records):
        # Decision record 0016: a history question is told how many records the budget left out.
        line = f"{shown} of {len(records)} records shown; {len(records) - shown} left out to fit the context budget."
        expected["context"] = context + "\n" + line if context else line
        expected["history_rule"] = comparison.HISTORY_LEFT_OUT_RULE
    assert payload == expected
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
def test_captured_current_omission_is_rejected_without_silent_repair_and_history_stays_a_control(case):
    records = [Record.model_validate(row) for row in case["records"]]
    asked = question(**case["request"]["question"])
    result, _ = answer(records, case["observed_decision"], asked=asked, expected_payload=case["request"],
                       rejected=asked.kind == "current")
    expected = pilot_timeline(case["scenario_id"]).expected[case["question_id"]]
    assert case["provenance"]["split"] == "dev"
    assert case["provenance"]["run"] == "20261019T024350Z-resolver-provenance-rerun"
    assert case["observed_decision"]["value"] == expected.expected_value
    if asked.kind == "previous":
        assert result.value == expected.expected_value
    missing = set(expected.required_support) - set(case["observed_decision"]["cited_turn_ids"])
    assert missing == ({"S3-T1"} if asked.kind == "previous" else {"S2-T3"})
    # Respectively: SVM's formal replacement; the DistilBERT suggestion later adopted.


@pytest.mark.parametrize("case", CAPTURE["cases"], ids=lambda case: case["id"])
def test_scripted_complete_answers_use_the_same_saved_context_and_exact_required_roles(case):
    expected = pilot_timeline(case["scenario_id"]).expected[case["question_id"]]
    assert set(case["corrected_decision"]["cited_turn_ids"]) == set(expected.required_support)
    records = [Record.model_validate(row) for row in case["records"]]
    result, payload = answer(records, case["corrected_decision"],
                             asked=question(**case["request"]["question"]), expected_payload=case["request"])
    assert set(result.cited_turn_ids) == set(expected.required_support)
    assert set(result.cited_turn_ids) < set(payload["allowed_source_turn_ids"])
    if case["id"] == "adopted_origin_omitted":
        assert {"S1-T1", "S4-T1"}.issubset(payload["allowed_source_turn_ids"])
        assert not {"S1-T1", "S4-T1"}.intersection(result.cited_turn_ids)
        # BERT's old decision and the later reaffirmation are not adoption roles.
    else:
        assert "S3-T2" in payload["allowed_source_turn_ids"] and "S3-T2" not in result.cited_turn_ids
        # The later SVM KEEP is not the replacement event.


def linked_history():
    return [
        record("S1-T1", "option X", "superseded"),  # Earlier settled choice.
        record("S2-T1", "option Y", "superseded"),  # Closed origin, formerly a suggestion.
        record("S2-T2", "option Z", "proposed"),  # Alternative never adopted.
        record("S3-T1", "option Y", sources=["S3-T1", "S2-T1", "S1-T1", "S4-T1"],
               supersedes=["private:selection:S1-T1", "private:selection:S2-T1"]),
    ]


@pytest.mark.parametrize(("kind", "session", "reply"), [
    ("current", None, decision("option Y", ["S2-T1", "S3-T1"])),
    ("previous", None, decision("option X", ["S1-T1", "S3-T1"])),
    ("as_of", "S1", decision("option X", ["S1-T1"])),
])
def test_generic_time_roles_do_not_copy_old_sources_proposals_or_later_keep(kind, session, reply):
    result, payload = answer(linked_history(), reply, asked=question(kind, session=session))
    assert "S2-T2" in payload["allowed_source_turn_ids"]  # Unaccepted option Z.
    assert not {"S2-T2", "S4-T1"}.intersection(result.cited_turn_ids)


@pytest.mark.parametrize(("records", "reply"), [
    ([record("S1-T1", "option X"), record("S2-T1", "option Y", "proposed")],
     decision("option X", ["S1-T1"])),
    ([record("S1-T1", "option X"), record("S2-T1", "option X", "proposed")],
     decision("option X", ["S1-T1"])),
    ([record("S3-T1", "cancelled"), record("S4-T1", "open", "proposed")],
     decision("cancelled", ["S3-T1"])),
    ([record("S1-T1", "option X"), record("S2-T1", "option Y", "contested")],
     decision(sources=["S1-T1", "S2-T1"], status="conflict")),
])
def test_open_proposals_are_not_adoption_evidence_and_true_disputes_remain_distinct(records, reply):
    answer(records, reply)


def test_missing_origin_content_does_not_turn_an_older_source_id_into_a_proposal():
    records = [record("S3-T1", "option Y", sources=["S3-T1", "S2-T1"])]
    result, payload = answer(records, decision("option Y", ["S3-T1"]))
    assert "S2-T1" in payload["allowed_source_turn_ids"]  # Role unknown in the retained context.
    assert result.cited_turn_ids == ["S3-T1"]


@pytest.mark.parametrize("budget", [256, 12000])
def test_current_only_or_budget_omitted_history_cannot_support_a_previous_value(budget):
    current = record("S3-T1", "option Y", sources=["S3-T1", "S1-T1"],
                     supersedes=["private:selection:S1-T1"])
    records = [current]
    if budget == 256:
        records.insert(0, record("S1-T1", "omitted old choice " * 60, "superseded"))
    result, payload = answer(records, decision(status="abstain"), asked=question("previous"), budget=budget)
    assert "omitted old choice" not in payload["context"]
    if budget == 256:
        assert payload["context"].endswith("\n1 of 2 records shown; 1 left out to fit the context budget.")
    assert "S1-T1" in payload["allowed_source_turn_ids"]
    assert result.status == "abstain" and result.cited_turn_ids == []


@pytest.mark.parametrize(("kind", "reply"), [
    ("current", decision("option Y", ["S2-T1", "S3-T1"])),
    ("previous", decision("option X", ["S1-T1", "S3-T1"])),
    ("as_of", decision("option X", ["S1-T1"])),
])
def test_native_text_history_obeys_the_same_adoption_and_replacement_roles(kind, reply):
    records = [
        record("S1-T1", json.dumps({"mem0_history": "ADD", "before": None,
                                    "after": "We decided on option X."}), None),
        record("S2-T1", json.dumps({"mem0_history": "ADD", "before": None,
                                    "after": "Could we try option Y instead?"}), None),
        record("S3-T1", json.dumps({"mem0_history": "UPDATE", "before": "We decided on option X.",
                                    "after": "We adopt the earlier option Y suggestion, replacing X."}), None,
               sources=["S3-T1", "S2-T1", "S1-T1"]),
        record("S4-T1", "The team reaffirms option Y.", None),
    ]
    asked = question(kind, session="S1" if kind == "as_of" else None)
    result, payload = answer(records, reply, asked=asked)
    assert "[active]" not in payload["context"] and "[superseded]" not in payload["context"]
    assert "S4-T1" not in result.cited_turn_ids  # Later reaffirmation.


def test_final_evidence_check_changes_only_answer_prompt_fingerprint(monkeypatch):
    current = comparison.comparison_settings(CONFIG, 12000, ScriptedClient({}))
    monkeypatch.setattr(comparison, "ANSWER_PROMPT",
                        comparison.ANSWER_PROMPT.removesuffix("\n" + comparison.ANSWER_EVIDENCE_CHECK))
    without_check = comparison.comparison_settings(CONFIG, 12000, ScriptedClient({}))
    assert {key for key in current if current[key] != without_check[key]} == {"answer_prompt_hash"}
    assert current["context_budget_bytes"] == 12000


def test_source_pruning_rule_preserves_previous_and_conflict_evidence_roles():
    # The scripted previous/conflict cases above are contract tests. This separate
    # prompt guard prevents an unconditional "remove old/different values" rule
    # from contradicting them; it still makes no claim about live compliance.
    pruning = " ".join(comparison.ANSWER_EVIDENCE_CHECK.split("3.", 1)[1].split("4.", 1)[0].split())
    assert "For a settled CURRENT answer" in pruning
    assert "For PREVIOUS, retain the earlier decision AND the different-value replacement." in pruning
    assert "For conflict, retain the competing evidence." in pruning
    assert "An unaccepted proposal can support a claim about that proposal" in pruning
    assert "cannot supply approval or a settled replacement" in pruning
