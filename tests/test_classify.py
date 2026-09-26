"""classify(): every answer gets exactly one of ten outcomes, and each branch is reached here.

Some cases use hand-built expected answers; the named cases from the task use
real expected answers replayed from the pilots, so they also check that the
replay puts each spelling in the right set.
"""

from __future__ import annotations

import pytest

from support import pilot_timeline
from tracemem.eval.classify import OUTCOMES, classify
from tracemem.schema import Answer, ExpectedAnswer


def expected(status="answer", value="BERT", *, accepted=("bert", "bert-base"), stale=(), unconfirmed=(),
             confusable=(), current=(), kind="current") -> ExpectedAnswer:
    return ExpectedAnswer(
        question_id="q", scenario_id="s", kind=kind, item="model.x", after="S1",
        expected_status=status, expected_value=value if status == "answer" else None,
        accepted_values=list(accepted) if status == "answer" else [],
        stale_values=list(stale), unconfirmed_values=list(unconfirmed), confusable_values=list(confusable),
        current_values=list(current),
    )


def says(value: str) -> Answer:
    return Answer(status="answer", value=value)


NONE, CONFLICT, ABSTAIN = Answer(status="none"), Answer(status="conflict"), Answer(status="abstain")

SETTLED = expected(stale=("distilbert",), unconfirmed=("roberta",), confusable=("spacy",))
DISPUTED = expected("conflict", unconfirmed=("sst-2",))
UNDECIDED = expected("none", unconfirmed=("roberta",), confusable=("spacy",))
HISTORY = expected(value="BERT", kind="previous", current=("distilbert",))

CASES = [
    # (description, answer, expected answer, outcome)
    ("settled value given", says("BERT"), SETTLED, "correct"),
    ("alias of the settled value", says("bert-base"), SETTLED, "correct"),
    ("replaced value given", says("DistilBERT"), SETTLED, "stale"),
    ("suggestion given as settled", says("RoBERTa"), SETTLED, "unconfirmed_as_current"),
    ("another item's value", says("spaCy"), SETTLED, "confusable_as_current"),
    ("unrelated value", says("GPT-2"), SETTLED, "wrong_other"),
    ("'none' where a value is settled", NONE, SETTLED, "missed"),
    ("conflict where a value is settled", CONFLICT, SETTLED, "false_conflict"),
    ("abstain where a value is settled", ABSTAIN, SETTLED, "abstained"),
    ("conflict reported where there is one", CONFLICT, DISPUTED, "correct"),
    ("one side picked in a dispute", says("SST-2"), DISPUTED, "false_certainty"),
    ("the other side picked in a dispute", says("BERT"), DISPUTED, "false_certainty"),
    ("'none' in a dispute", NONE, DISPUTED, "missed"),
    ("abstain in a dispute", ABSTAIN, DISPUTED, "abstained"),
    ("'none' where nothing is decided", NONE, UNDECIDED, "correct"),
    ("suggestion given where nothing is decided", says("RoBERTa"), UNDECIDED, "unconfirmed_as_current"),
    ("another item's value where nothing is decided", says("spaCy"), UNDECIDED, "confusable_as_current"),
    ("unrelated value where nothing is decided", says("GPT-2"), UNDECIDED, "wrong_other"),
    ("conflict where nothing is decided", CONFLICT, UNDECIDED, "false_conflict"),
    ("earlier value given to a history question", says("BERT"), HISTORY, "correct"),
    ("today's value given to a history question", says("DistilBERT"), HISTORY, "current_as_historical"),
]


@pytest.mark.parametrize("description, answer, gold, outcome", CASES, ids=[c[0] for c in CASES])
def test_classify_branches(description, answer, gold, outcome):
    assert classify(answer, gold) == outcome


def test_every_outcome_is_reached():
    """The cases above cover all ten outcome classes."""
    assert {c[3] for c in CASES} == set(OUTCOMES)
    assert len(OUTCOMES) == 10


def test_answers_are_normalised_before_comparison():
    """Case, spacing and outer punctuation do not change the outcome."""
    assert classify(says("  Bert-BASE. "), SETTLED) == "correct"
    assert classify(says('"distilbert"!'), SETTLED) == "stale"


def test_precedence_when_a_spelling_is_in_several_sets():
    """The checks run accepted > stale > unconfirmed > confusable > current, so the first set wins."""
    overlapping = expected(stale=("x",), unconfirmed=("x", "y"), confusable=("x", "y", "z"), current=("x", "y", "z", "w"))
    assert classify(says("x"), overlapping) == "stale"
    assert classify(says("y"), overlapping) == "unconfirmed_as_current"
    assert classify(says("z"), overlapping) == "confusable_as_current"
    assert classify(says("w"), overlapping) == "current_as_historical"


# -- the named cases, on replayed pilot answers ---------------------------------------------------


def test_alias_of_a_stale_value_is_stale():
    """pilot-01 after S3: 'bert-base-uncased' is an alias of BERT, which DistilBERT replaced."""
    gold = pilot_timeline("pilot-01").expected["model.sentiment@S3"]
    assert classify(says("bert-base-uncased"), gold) == "stale"
    assert classify(says("BERT"), gold) == "stale"
    assert classify(says("distil-bert"), gold) == "correct"


def test_declined_contested_value_is_unconfirmed_as_current():
    """pilot-02 after S3: SST-2 was disputed (S2-T1) and then declined when IMDB was restated (S3-T1)."""
    gold = pilot_timeline("pilot-02").expected["dataset.train@S3"]
    assert classify(says("SST-2"), gold) == "unconfirmed_as_current"
    assert classify(says("stanford sentiment treebank"), gold) == "unconfirmed_as_current"
    assert classify(says("IMDB"), gold) == "correct"


def test_current_value_given_to_a_previous_question_is_current_as_historical():
    """pilot-01 'which model did we use before?': answering today's DistilBERT is current_as_historical."""
    gold = pilot_timeline("pilot-01").expected["model.sentiment@S3-previous"]
    assert classify(says("DistilBERT"), gold) == "current_as_historical"
    assert classify(says("distilbert-base-uncased"), gold) == "current_as_historical"
    assert classify(says("BERT"), gold) == "correct"


def test_current_value_given_to_an_as_of_question_is_current_as_historical():
    """pilot-01 'what was our metric after the first meeting?': today's macro-F1 is current_as_historical."""
    gold = pilot_timeline("pilot-01").expected["metric.primary@S4-asof-S1"]
    assert classify(says("macro F1"), gold) == "current_as_historical"
    assert classify(says("acc"), gold) == "correct"


def test_none_while_a_conflict_is_open_is_missed():
    """pilot-02 after S2: the dataset is disputed; saying nothing is settled misses the dispute."""
    gold = pilot_timeline("pilot-02").expected["dataset.train@S2"]
    assert gold.expected_status == "conflict"
    assert classify(NONE, gold) == "missed"
    assert classify(CONFLICT, gold) == "correct"
    assert classify(says("IMDB"), gold) == "false_certainty"


def test_conflict_on_a_settled_item_is_false_conflict():
    """pilot-02 after S3: the dispute was settled by the restatement, so reporting a conflict is over-cautious."""
    gold = pilot_timeline("pilot-02").expected["dataset.train@S3"]
    assert classify(CONFLICT, gold) == "false_conflict"


def test_previous_question_with_no_earlier_value():
    """pilot-02 'did we use a different dataset before?': nothing was replaced, so 'none' is right."""
    gold = pilot_timeline("pilot-02").expected["dataset.train@S4-previous"]
    assert classify(NONE, gold) == "correct"
    assert classify(says("IMDB"), gold) == "current_as_historical"
    assert classify(says("SST-2"), gold) == "wrong_other"


def test_reopening_suggestion_that_repeats_an_old_value_is_stale():
    """pilot-04 after S4: the error analysis is cancelled; the suggestion to reopen it is also an old value, so 'open' is stale."""
    gold = pilot_timeline("pilot-04").expected["task.error_analysis@S4"]
    assert classify(says("in progress"), gold) == "stale"
    assert classify(says("dropped"), gold) == "correct"
