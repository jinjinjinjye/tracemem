"""Historical citation regressions, without a provider or a semantic auto-fix.

Captured wrong replies remain structurally valid. Scripted replies check the
shared prompt, visible evidence and answer contract; they do not demonstrate
that a live model will select the right sources.
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
from tracemem.systems.comparison import (
    ANSWER_CITATION_GUIDE, ANSWER_FORMAT, ANSWER_PROMPT, ANSWER_STATE_GUIDE, HISTORY_LEFT_OUT_RULE,
    SharedAnswerer, _selected_context, answer_context, comparison_settings,
)


FIXTURES = Path(__file__).parent / "fixtures"
CAPTURE = json.loads((FIXTURES / "historical_citation_failures.json").read_text(encoding="utf-8"))
CONFIG = ResolverConfig(model="offline-historical-citations", max_attempts=2)
ANSWER_FIELDS = {"status", "value", "cited_turn_ids", "text"}


class ScriptedClient:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def complete(self, **request):
        self.calls.append(copy.deepcopy(request))
        return ModelReply(content=json.dumps(self.reply))


def question(kind="previous", *, text=None, session=None):
    return SystemQuestion(
        question_id="opaque-question", scenario_id="opaque-scenario", kind=kind,
        text=text or CAPTURE["request"]["question"]["text"], session=session,
    )


def response(value, sources):
    return {"status": "answer", "value": value, "cited_turn_ids": sources,
            "text": "Scripted answer exercising the evidence contract."}


def check_answer(records, decision, *, asked=None, budget=12000, expected_payload=None):
    asked = asked or question()
    before = [record.model_dump() for record in records]
    client = ScriptedClient(decision)
    answerer = SharedAnswerer(CONFIG, client, budget)
    raw_turns = {"S3-T1": Turn(id="S3-T1", speaker="Kai", text="RAW_DIALOGUE_MUST_STAY_HIDDEN")}

    answer = answerer.answer(asked, records, raw_turns)

    assert len(client.calls) == answerer.usage().calls == answer.usage.calls == 1
    request = client.calls[0]
    assert request["config"] == CONFIG
    assert len(request["messages"]) == 2
    assert request["messages"][0] == {"role": "system", "content": ANSWER_PROMPT}
    assert ANSWER_STATE_GUIDE in ANSWER_PROMPT and ANSWER_CITATION_GUIDE in ANSWER_PROMPT
    context, sources = answer_context(records, budget)
    payload = json.loads(request["messages"][1]["content"])
    expected = {
        "question": {"text": asked.text, "kind": asked.kind, "session": asked.session},
        "context": context, "allowed_source_turn_ids": sources,
    }
    shown = len(_selected_context(records, budget)[2])
    if asked.kind in ("previous", "as_of") and shown < len(records):
        # Decision record 0016: a history question is told how many records the budget left out.
        line = f"{shown} of {len(records)} records shown; {len(records) - shown} left out to fit the context budget."
        expected["context"] = context + "\n" + line if context else line
        expected["history_rule"] = HISTORY_LEFT_OUT_RULE
    assert payload == expected
    if expected_payload is not None:
        assert payload == expected_payload
    assert "RAW_DIALOGUE_MUST_STAY_HIDDEN" not in payload["context"]
    assert "supersedes" not in payload["context"]
    assert "record_id" not in payload["context"]
    schema = request["response_format"]["json_schema"]["schema"]
    assert request["response_format"] == ANSWER_FORMAT
    assert set(schema["properties"]) == set(schema["required"]) == ANSWER_FIELDS
    assert answer.context_turn_ids == sources
    assert [record.model_dump() for record in records] == before
    for field, value in decision.items():
        assert getattr(answer, field) == value
    return answer, payload


def baseline_records():
    return copy.deepcopy(pilot_timeline("pilot-05").log_after_session["S3"].records())


def test_captured_incomplete_history_citation_is_not_silently_repaired():
    assert CAPTURE["provenance"]["split"] == "dev"
    answer, _ = check_answer(
        baseline_records(), CAPTURE["observed_decision"], expected_payload=CAPTURE["request"],
    )
    timeline = pilot_timeline("pilot-05")
    previous = next(q for q in timeline.questions if q.kind == "previous")
    expected = timeline.expected[previous.question_id]
    assert answer.value == expected.expected_value == "logistic regression"
    assert answer.cited_turn_ids == ["S1-T1"]  # Initial logistic regression decision.
    assert set(expected.required_support) - set(answer.cited_turn_ids) == {"S3-T1"}  # SVM replacement.


def test_scripted_previous_answer_cites_origin_and_replacement_not_proposal_or_keep():
    timeline = pilot_timeline("pilot-05")
    previous = next(q for q in timeline.questions if q.kind == "previous")
    expected = timeline.expected[previous.question_id]
    answer, payload = check_answer(
        baseline_records(), response(expected.expected_value, expected.required_support),
        expected_payload=CAPTURE["request"],
    )
    assert answer.cited_turn_ids == ["S1-T1", "S3-T1"]  # Logistic regression, then SVM adoption.
    assert {"S1-T2", "S3-T2"}.issubset(payload["allowed_source_turn_ids"])
    assert not {"S1-T2", "S3-T2"}.intersection(answer.cited_turn_ids)  # Naive Bayes suggestion and SVM KEEP.
    assert "naive Bayes [proposed]" in payload["context"]


def test_scripted_as_of_uses_earlier_decision_without_backdating_later_replacement():
    answer, payload = check_answer(
        baseline_records(), response("logistic regression", ["S1-T1"]),
        asked=question("as_of", text="Which baseline classifier were we using in session S1?", session="S1"),
    )
    assert "linear SVM [active]" in payload["context"]
    assert answer.value == "logistic regression"
    assert not {"S1-T2", "S3-T1", "S3-T2"}.intersection(answer.cited_turn_ids)


def test_missing_history_does_not_become_available_through_an_unrelated_items_source():
    records = [record.model_copy(update={"supersedes": []}) for record in baseline_records()
               if record.status in {"active", "proposed", "contested"}]
    answer, payload = check_answer(records, {
        "status": "abstain", "value": None, "cited_turn_ids": [],
        "text": "The retained current memories do not establish the previous classifier.",
    })
    assert "logistic regression" not in payload["context"]
    assert "S1-T1" in payload["allowed_source_turn_ids"]  # Still visible for the unrelated TF-IDF feature.
    assert "features.text = TF-IDF" in payload["context"]
    assert answer.status == "abstain" and answer.cited_turn_ids == []


def native_record(turn, value, sources):
    session = int(turn.split("-")[0][1:])
    return Record(
        record_id=f"native-history:{turn}", project_id="synthetic-project", item="model.baseline",
        value=json.dumps(value), status=None, source_turn_ids=sources, speakers=["Kai"] * len(sources),
        created_turn=turn, created_at=datetime(2026, 1, session, 10), supersedes=[],
    )


def test_scripted_previous_answer_uses_native_before_after_history_under_the_same_prompt():
    records = [
        native_record("S1-T1", {"mem0_history": "ADD", "before": None,
                               "after": "We decided to use logistic regression."}, ["S1-T1"]),
        native_record("S3-T1", {"mem0_history": "UPDATE", "before": "We decided to use logistic regression.",
                               "after": "We replaced logistic regression with linear SVM."}, ["S3-T1", "S1-T1"]),
    ]
    answer, payload = check_answer(records, response("logistic regression", ["S1-T1", "S3-T1"]))
    assert answer.cited_turn_ids == ["S1-T1", "S3-T1"]
    assert '"mem0_history": "UPDATE"' in payload["context"]
    assert "[active]" not in payload["context"] and "[superseded]" not in payload["context"]


def test_budget_omitted_history_produces_no_fabricated_support():
    old = native_record("S1-T1", {"mem0_history": "ADD", "after": "old classifier " * 40}, ["S1-T1"])
    current = native_record("S3-T1", {"after": "linear SVM is the chosen classifier"}, ["S3-T1"])
    answer, payload = check_answer([old, current], {
        "status": "abstain", "value": None, "cited_turn_ids": [],
        "text": "The earlier decision is absent from the retained context.",
    }, budget=256)
    assert payload["allowed_source_turn_ids"] == ["S3-T1"]
    assert "old classifier" not in payload["context"]
    assert payload["context"].endswith("\n1 of 2 records shown; 1 left out to fit the context budget.")
    assert answer.cited_turn_ids == []


@pytest.mark.parametrize(("scenario", "item", "value", "source"), [
    ("pilot-01", "model.ner", "spaCy", "S2-T5"),  # Formal NER choice.
    ("pilot-05", "model.baseline", "linear SVM", "S3-T1"),  # Formal baseline replacement.
])
def test_current_decisions_do_not_require_citing_the_previous_value(scenario, item, value, source):
    records = copy.deepcopy(pilot_timeline(scenario).log_after_session["S3"].records())
    answer, _ = check_answer(records, response(value, [source]), asked=question(
        "current", text=f"What is the current value for {item}?",
    ))
    assert answer.value == value and answer.cited_turn_ids == [source]


def test_cancelled_plus_reopening_proposal_keeps_cancellation_citation():
    fixture = json.loads((FIXTURES / "task_reopening_failures.json").read_text(encoding="utf-8"))
    case = fixture["answer_failure"]
    records = [Record.model_validate(record) for record in case["records"]]
    asked = SystemQuestion(question_id="opaque-question", scenario_id="opaque-scenario", **case["request"]["question"])
    answer, payload = check_answer(records, case["corrected_decision"], asked=asked, expected_payload=case["request"])
    assert "cancelled [active]" in payload["context"] and "open [proposed]" in payload["context"]
    assert answer.value == "cancelled" and answer.cited_turn_ids == ["S3-T2"]  # Adopted cancellation.
    assert "S4-T2" not in answer.cited_turn_ids  # Asking whether to reopen is not a conflict or adoption.


def test_citation_guide_changes_prompt_fingerprint_without_changing_schema_or_reader_settings(monkeypatch):
    from tracemem.systems import comparison

    current = comparison_settings(CONFIG, 12000, ScriptedClient({}))
    monkeypatch.setattr(comparison, "ANSWER_PROMPT", ANSWER_PROMPT.replace("\n" + ANSWER_CITATION_GUIDE, ""))
    previous = comparison_settings(CONFIG, 12000, ScriptedClient({}))
    assert {key for key in current if current[key] != previous[key]} == {"answer_prompt_hash"}
    assert current["context_budget_bytes"] == 12000
