"""The second score of decision record 0015: a value that contains an accepted value.

The strict scorer (eval/classify.py) stays the reported number. These tests pin
the second score's rule: an answer scored `wrong_other` counts as correct when
its value contains an accepted value as whole words and names no wrong value.
Every other outcome is left as the strict scorer set it.
"""

from __future__ import annotations

import json

from tracemem.eval.contains import contains_outcome, rescore, score_table
from tracemem.eval.metrics import ScoredAnswer
from tracemem.schema import Answer, ExpectedAnswer, Question


def _row(value: str | None, outcome: str, *, status: str = "answer", expected_status: str = "answer",
         kind: str = "current", accepted=("lightgbm",), stale=(), unconfirmed=(), confusable=(), current=(),
         scenario: str = "s1", qid: str = "q1") -> ScoredAnswer:
    question = Question(question_id=qid, scenario_id=scenario, after="S1", kind=kind, item="model.demand",
                        text="Which model do we use?")
    expected = ExpectedAnswer(question_id=qid, scenario_id=scenario, kind=kind, item="model.demand", after="S1",
                              expected_status=expected_status, accepted_values=list(accepted),
                              stale_values=list(stale), unconfirmed_values=list(unconfirmed),
                              confusable_values=list(confusable), current_values=list(current))
    answer = Answer(status=status, value=value if status == "answer" else None)
    return ScoredAnswer(question=question, expected=expected, answer=answer, outcome=outcome,
                        visible_turns=frozenset({"S1-T1"}))


# Breaks if the rule stops accepting an accepted value with extra words around it.
def test_extra_words_around_an_accepted_value_count_as_correct():
    assert contains_outcome(_row("LightGBM on lag features", "wrong_other")) == "correct"


# Breaks if the guard against a second, wrong value is dropped.
def test_a_value_that_also_names_a_replaced_value_stays_wrong():
    row = _row("LightGBM instead of Prophet", "wrong_other", stale=("prophet",))
    assert contains_outcome(row) == "wrong_other"


# Breaks if any of the four wrong-value lists is left out of the guard.
def test_every_kind_of_wrong_value_blocks_the_match():
    for field in ("unconfirmed", "confusable", "current"):
        row = _row("LightGBM or XGBoost", "wrong_other", **{field: ("xgboost",)})
        assert contains_outcome(row) == "wrong_other", field


# Breaks if matching becomes a plain substring test: "distilbert" is not BERT.
def test_an_accepted_value_inside_another_word_does_not_match():
    assert contains_outcome(_row("DistilBERT", "wrong_other", accepted=("bert",))) == "wrong_other"


# Breaks if the rule is applied where the gold is "nothing settled" or a dispute.
def test_questions_without_a_settled_value_are_left_alone():
    assert contains_outcome(_row("LightGBM on lag features", "wrong_other", expected_status="none")) == "wrong_other"


# Breaks if the rule rewrites outcomes other than wrong_other.
def test_other_outcomes_are_unchanged():
    assert contains_outcome(_row("Prophet on lags", "stale", stale=("prophet on lags",))) == "stale"
    assert contains_outcome(_row("LightGBM", "correct")) == "correct"
    assert contains_outcome(_row(None, "missed", status="none")) == "missed"
    # Only wrong_other is re-labelled, even when the value would pass the rule.
    assert contains_outcome(_row("LightGBM on lag features", "unconfirmed_as_current")) == "unconfirmed_as_current"


# Breaks if rescore changes rows it should keep, or loses rows.
def test_rescore_changes_only_the_matching_rows():
    rows = [_row("LightGBM on lag features", "wrong_other", qid="a"),
            _row("Random forest", "wrong_other", qid="b"),
            _row("LightGBM", "correct", qid="c")]
    assert [r.outcome for r in rescore(rows)] == ["correct", "wrong_other", "correct"]


def _write_run(folder, system: str, rows: list[ScoredAnswer]) -> None:
    folder.mkdir()
    (folder / "manifest.json").write_text(json.dumps({"system": system, "status": "completed"}), encoding="utf-8")
    with open(folder / "answers.jsonl", "w", encoding="utf-8") as handle:
        for r in rows:
            handle.write(json.dumps({"scenario_id": r.scenario_id, "category": "", "question": r.question.model_dump(),
                                     "expected": r.expected.model_dump(), "answer": r.answer.model_dump(),
                                     "outcome": r.outcome, "visible_turns": sorted(r.visible_turns)}) + "\n")


# Breaks if the table stops showing both scores, or counts the wrong rows.
def test_the_table_shows_the_strict_and_the_contains_score(tmp_path):
    rows = [_row("LightGBM on lag features", "wrong_other", scenario=f"s{i}", qid=f"q{i}") for i in range(2)]
    rows += [_row("LightGBM", "correct", scenario=f"s{i}", qid=f"r{i}") for i in range(2)]
    _write_run(tmp_path / "run1", "mem0-classic", rows)
    table = score_table([tmp_path / "run1"], n=50)
    line = next(line for line in table.splitlines() if line.startswith("| mem0-classic"))
    cells = [c.strip() for c in line.strip("|").split("|")]
    assert cells[1].startswith("0.500")  # strict: 2 of 4 present questions
    assert cells[2].startswith("1.000")  # contains: all 4
    assert cells[-1] == "2"  # answers the second score re-scored
