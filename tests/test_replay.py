"""The replay: script acts -> gold operations -> expected answers, checked against hand-derived tables.

Every table below was worked out by reading the pilot's YAML script by hand and
applying the act rules (schema.py, replay.py), NOT by running the replay and
pasting its output. That is the point: if the replay has a bug, these tables
disagree with it. When a table and the replay disagree, decide which one is
right from the act rules; do not edit the table just to match the replay.

Notation: ("answer", value) means the expected answer is that value;
("conflict", None) means the team disagrees and nothing is settled;
("none", None) means nothing has been decided (or, for a "previous"
question, that there was no earlier value).
"""

from __future__ import annotations

import pytest

from support import PILOT_IDS, pilot, pilot_timeline
from tracemem.bench.load import expand_questions
from tracemem.bench.replay import ScriptError, accepted_forms, replay
from tracemem.ops import record_id
from tracemem.schema import Scenario

# ---------------------------------------------------------------------------
# Hand-derived expected answers, one table per pilot
# ---------------------------------------------------------------------------

EXPECTED = {
    "pilot-01": {
        # model.sentiment: decided BERT (S1-T1); DistilBERT only suggested (S2-T3); revised to DistilBERT (S3-T2).
        "model.sentiment@S1": ("answer", "BERT"),
        "model.sentiment@S2": ("answer", "BERT"),  # the S2-T3 suggestion does not change the decision
        "model.sentiment@S3": ("answer", "DistilBERT"),
        "model.sentiment@S4": ("answer", "DistilBERT"),  # S4-T2 only asks about RoBERTa
        "model.sentiment@S3-previous": ("answer", "BERT"),
        # metric.primary: S1-T2 suggests accuracy; S1-T3 accepts it; S3-T3 suggests macro-F1, S3-T4 accepts it.
        "metric.primary@S1": ("answer", "accuracy"),
        "metric.primary@S2": ("answer", "accuracy"),
        "metric.primary@S3": ("answer", "macro-F1"),
        "metric.primary@S4": ("answer", "macro-F1"),
        "metric.primary@S4-asof-S1": ("answer", "accuracy"),
        # model.ner: first stated in S2 (S2-T5), so it has no S1 question.
        "model.ner@S2": ("answer", "spaCy"),
        "model.ner@S3": ("answer", "spaCy"),
        "model.ner@S4": ("answer", "spaCy"),
    },
    "pilot-02": {
        # dataset.train: IMDB (S1-T1); contested with SST-2 (S2-T1); S2-T2 only recalls IMDB, which settles nothing;
        # IMDB restated (S3-T1, which settles it, and S3-T2); Yelp only suggested (S3-T3); SST-2 only mentioned (S4-T2).
        "dataset.train@S1": ("answer", "IMDB"),
        "dataset.train@S2": ("conflict", None),
        "dataset.train@S3": ("answer", "IMDB"),
        "dataset.train@S4": ("answer", "IMDB"),
        "dataset.train@S4-previous": ("none", None),  # IMDB was never replaced, so there is no earlier value
        "dataset.train@S4-asof-S2": ("conflict", None),
        # task.label_audit: open (S1-T3) -> blocked (S2-T3) -> open (S3-T2) -> completed (S4-T1).
        "task.label_audit@S1": ("answer", "open"),
        "task.label_audit@S2": ("answer", "blocked"),
        "task.label_audit@S3": ("answer", "open"),
        "task.label_audit@S4": ("answer", "completed"),
    },
    "pilot-03": {
        # model.sentiment: DistilBERT (S1-T1), restated at S3-T2; never changes.
        "model.sentiment@S1": ("answer", "DistilBERT"),
        "model.sentiment@S2": ("answer", "DistilBERT"),
        "model.sentiment@S3": ("answer", "DistilBERT"),
        "model.sentiment@S4": ("answer", "DistilBERT"),
        # model.ner: BERT (S2-T1) -> spaCy (S3-T1); Flair only suggested (S4-T1).
        "model.ner@S2": ("answer", "BERT"),
        "model.ner@S3": ("answer", "spaCy"),
        "model.ner@S4": ("answer", "spaCy"),
        "model.ner@S4-previous": ("answer", "BERT"),
    },
    "pilot-04": {
        # compute.gpu: Colab (S1-T1) -> lab server (S2-T2).
        "compute.gpu@S1": ("answer", "Colab"),
        "compute.gpu@S2": ("answer", "lab server"),
        "compute.gpu@S3": ("answer", "lab server"),
        "compute.gpu@S4": ("answer", "lab server"),
        # task.baseline_runs: open (S1-T2) -> blocked (S2-T1) -> open (S3-T1) -> completed (S4-T1).
        "task.baseline_runs@S1": ("answer", "open"),
        "task.baseline_runs@S2": ("answer", "blocked"),
        "task.baseline_runs@S3": ("answer", "open"),
        "task.baseline_runs@S4": ("answer", "completed"),
        # task.error_analysis: open (S1-T3) -> cancelled (S3-T2); reopening only suggested (S4-T2).
        "task.error_analysis@S1": ("answer", "open"),
        "task.error_analysis@S2": ("answer", "open"),
        "task.error_analysis@S3": ("answer", "cancelled"),
        "task.error_analysis@S4": ("answer", "cancelled"),
    },
    "pilot-05": {
        # model.baseline: logistic regression (S1-T1); naive Bayes only suggested (S1-T2);
        # S2 only mentions values; revised to linear SVM (S3-T1), restated (S3-T2); S3-T3 recalls logistic regression.
        "model.baseline@S1": ("answer", "logistic regression"),
        "model.baseline@S2": ("answer", "logistic regression"),
        "model.baseline@S3": ("answer", "linear SVM"),
        "model.baseline@S4": ("answer", "linear SVM"),
        "model.baseline@S3-previous": ("answer", "logistic regression"),
        # features.text: TF-IDF (S1-T1); bag of words only mentioned (S4-T1).
        "features.text@S1": ("answer", "TF-IDF"),
        "features.text@S2": ("answer", "TF-IDF"),
        "features.text@S3": ("answer", "TF-IDF"),
        "features.text@S4": ("answer", "TF-IDF"),
    },
}

# Turns the correct answer must be able to cite (required) and turns that also support it (additional).
SUPPORT = {
    "pilot-01": {
        "model.sentiment@S1": (["S1-T1"], []),
        "model.sentiment@S2": (["S1-T1"], []),
        "model.sentiment@S3": (["S3-T2"], []),
        "model.sentiment@S4": (["S3-T2"], ["S4-T1"]),  # S4-T1 restates DistilBERT
        "model.sentiment@S3-previous": (["S1-T1", "S3-T2"], []),  # where BERT was set, and where it was replaced
        "metric.primary@S1": (["S1-T2", "S1-T3"], []),  # the acceptance cites the suggestion it accepts
        "metric.primary@S3": (["S3-T3", "S3-T4"], []),
        "metric.primary@S4": (["S3-T3", "S3-T4"], ["S4-T1"]),
        "metric.primary@S4-asof-S1": (["S1-T2", "S1-T3"], []),  # the S1-T2 suggestion and its S1-T3 acceptance
        "model.ner@S2": (["S2-T5"], []),
    },
    "pilot-02": {
        "dataset.train@S2": (["S1-T1", "S2-T1"], []),  # a conflict needs both sides
        "dataset.train@S3": (["S1-T1"], ["S3-T1", "S3-T2"]),  # both restatements; S2-T2's recollection is not one
        "dataset.train@S4-previous": ([], []),
        "dataset.train@S4-asof-S2": (["S1-T1", "S2-T1"], []),
        "task.label_audit@S4": (["S4-T1"], []),
    },
    "pilot-03": {
        "model.sentiment@S3": (["S1-T1"], ["S3-T2"]),
        "model.ner@S3": (["S3-T1"], []),
        "model.ner@S4": (["S3-T1"], []),  # the Flair suggestion is not support
        "model.ner@S4-previous": (["S2-T1", "S3-T1"], []),
    },
    "pilot-04": {
        "compute.gpu@S2": (["S2-T2"], []),
        "task.baseline_runs@S3": (["S3-T1"], []),
        "task.error_analysis@S4": (["S3-T2"], []),
    },
    "pilot-05": {
        "model.baseline@S1": (["S1-T1"], []),
        "model.baseline@S3": (["S3-T1"], ["S3-T2"]),
        "model.baseline@S3-previous": (["S1-T1", "S3-T1"], []),
        "features.text@S4": (["S1-T1"], []),
    },
}

# Which questions are traps, and of which kind (see replay.trap_flags):
#   candidate:  the item's newest memory-bearing statement is not the answer;
#   mention:    the newest statement is right, but a later mention names another value;
#   confusable: a similar item was decided or suggested after this item's last statement.
TRAPS = {
    "pilot-01": {
        "candidate": {"model.sentiment@S2"},  # newest statement is the DistilBERT suggestion
        "mention": {"model.sentiment@S3", "model.sentiment@S4"},  # S3-T6 recalls BERT; S4-T2 asks about RoBERTa
        # S2: spaCy decided for NER after the sentiment suggestion; S3/S4: sentiment statements after spaCy.
        "confusable": {"model.sentiment@S2", "model.ner@S3", "model.ner@S4"},
    },
    "pilot-02": {
        # S2: newest statement is the SST-2 claim but the answer is 'conflict'; S3/S4: newest is the Yelp suggestion.
        "candidate": {"dataset.train@S2", "dataset.train@S3", "dataset.train@S4", "dataset.train@S4-asof-S2"},
        "mention": set(),  # the S4-T2 SST-2 mention sits behind a candidate trap, and the flags do not overlap
        "confusable": set(),
    },
    "pilot-03": {
        "candidate": {"model.ner@S4"},  # the Flair suggestion
        "mention": set(),
        # sentiment@S2: BERT decided for NER; sentiment@S4: Flair suggested for NER; ner@S3: sentiment restated.
        "confusable": {"model.sentiment@S2", "model.sentiment@S4", "model.ner@S3"},
    },
    "pilot-04": {
        "candidate": {"task.error_analysis@S4"},  # the suggestion to reopen
        "mention": set(),
        "confusable": set(),
    },
    "pilot-05": {
        "candidate": {"model.baseline@S1", "model.baseline@S2"},  # the naive Bayes suggestion
        "mention": {"model.baseline@S3", "model.baseline@S4", "features.text@S4"},
        "confusable": set(),
    },
}

# Normalised spellings of each value, used below (canonical value plus the item's aliases).
BERT_01 = {"bert", "bert-base", "bert-base-uncased"}
DISTIL_01 = {"distilbert", "distilbert-base-uncased", "distil-bert"}
SPACY_01 = {"spacy", "spacy model", "spacy ner"}
SST2 = {"sst-2", "sst2", "stanford sentiment treebank"}
YELP = {"yelp", "yelp reviews", "yelp polarity"}
IMDB = {"imdb", "imdb reviews", "imdb dataset"}
OPEN = {"open", "in progress", "ongoing", "started", "reopened", "not started", "to do", "todo"}
BLOCKED = {"blocked", "stuck", "on hold", "waiting"}
COMPLETED = {"completed", "done", "finished", "complete"}
BERT_03 = {"bert", "bert-base-cased", "bert ner"}
LOGREG = {"logistic regression", "logreg", "lr"}
NAIVE_BAYES = {"naive bayes", "nb", "multinomial nb"}

# (accepted, stale, unconfirmed, confusable) value sets at the trap checkpoints and a few others.
VALUE_SETS = {
    ("pilot-01", "model.sentiment@S2"): (BERT_01, set(), DISTIL_01, SPACY_01),
    ("pilot-01", "model.sentiment@S3"): (DISTIL_01, BERT_01, set(), SPACY_01),
    ("pilot-01", "model.sentiment@S4"): (DISTIL_01, BERT_01, set(), SPACY_01),
    ("pilot-01", "model.ner@S3"): (SPACY_01, set(), set(), BERT_01 | DISTIL_01),
    ("pilot-01", "metric.primary@S3"): ({"macro-f1", "macro f1", "macro-averaged f1"}, {"accuracy", "acc"}, set(), set()),
    ("pilot-02", "dataset.train@S2"): (set(), set(), SST2, set()),
    ("pilot-02", "dataset.train@S3"): (IMDB, set(), SST2 | YELP, set()),  # SST-2 is declined, Yelp proposed
    ("pilot-02", "dataset.train@S4"): (IMDB, set(), SST2 | YELP, set()),
    ("pilot-02", "task.label_audit@S3"): (OPEN, BLOCKED, set(), set()),
    ("pilot-02", "task.label_audit@S4"): (COMPLETED, OPEN | BLOCKED, set(), set()),
    ("pilot-03", "model.sentiment@S2"): ({"distilbert", "distilbert-base-uncased"}, set(), set(), BERT_03),
    ("pilot-03", "model.ner@S4"): (
        {"spacy", "spacy model", "spacy ner"}, BERT_03, {"flair", "flair ner"}, {"distilbert", "distilbert-base-uncased"}),
    # The reopening suggestion's value (open) is also a replaced value; 'stale' takes precedence over 'unconfirmed'.
    ("pilot-04", "task.error_analysis@S4"): ({"cancelled", "canceled", "dropped", "abandoned"}, OPEN, set(), set()),
    ("pilot-05", "model.baseline@S1"): (LOGREG, set(), NAIVE_BAYES, set()),
    # The naive Bayes suggestion is still open after the revision to linear SVM.
    ("pilot-05", "model.baseline@S3"): ({"linear svm", "svm", "linear svc"}, LOGREG, NAIVE_BAYES, set()),
    ("pilot-05", "features.text@S4"): ({"tf-idf", "tfidf", "tf idf"}, set(), set(), set()),
}

# For history questions: forms of the value that is current when the question is asked (answering these is
# "current_as_historical").
CURRENT_FORMS = {
    ("pilot-01", "model.sentiment@S3-previous"): DISTIL_01,
    ("pilot-01", "metric.primary@S4-asof-S1"): {"macro-f1", "macro f1", "macro-averaged f1"},
    ("pilot-02", "dataset.train@S4-previous"): IMDB,
    ("pilot-02", "dataset.train@S4-asof-S2"): IMDB,
    ("pilot-03", "model.ner@S4-previous"): {"spacy", "spacy model", "spacy ner"},
    ("pilot-05", "model.baseline@S3-previous"): {"linear svm", "svm", "linear svc"},
}


# ---------------------------------------------------------------------------
# Tests against the tables
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_every_question_matches_the_hand_table(scenario_id):
    """The replay asks exactly the questions in the table, with the expected status and value for each."""
    timeline = pilot_timeline(scenario_id)
    table = EXPECTED[scenario_id]
    assert {q.question_id for q in timeline.questions} == set(table)
    for qid, (status, value) in table.items():
        e = timeline.expected[qid]
        assert (e.expected_status, e.expected_value) == (status, value), qid


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_required_and_additional_support(scenario_id):
    """Pins which turns an answer must cite (required) and which also back it (additional), for a few questions."""
    timeline = pilot_timeline(scenario_id)
    for qid, (required, additional) in SUPPORT[scenario_id].items():
        e = timeline.expected[qid]
        assert (e.required_support, e.additional_support) == (required, additional), qid


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_trap_flags_match_the_hand_table(scenario_id):
    """Every question's three trap flags, pinned: a question is flagged exactly when the table lists it."""
    timeline = pilot_timeline(scenario_id)
    traps = TRAPS[scenario_id]
    for question in timeline.questions:
        e = timeline.expected[question.question_id]
        got = (e.trap_candidate, e.trap_mention, e.trap_confusable)
        want = tuple(question.question_id in traps[kind] for kind in ("candidate", "mention", "confusable"))
        assert got == want, question.question_id


def test_pilot_01_trap_checkpoints_in_detail():
    """pilot-01, the proposal's own example: S2 is the suggestion trap, S3 the mention trap, S1 no trap."""
    e = pilot_timeline("pilot-01").expected
    s1, s2, s3 = e["model.sentiment@S1"], e["model.sentiment@S2"], e["model.sentiment@S3"]
    assert (s1.trap_candidate, s1.trap_mention, s1.trap_confusable) == (False, False, False)
    # S2: the newest record is the S2-T3 DistilBERT suggestion (candidate trap); and spaCy was decided for the
    # similar NER item at S2-T5, after the sentiment item's last statement (confusable trap).
    assert (s2.trap_candidate, s2.trap_mention, s2.trap_confusable) == (True, False, True)
    # S3: the newest record (S3-T2 revise) is right, but S3-T6 mentions BERT afterwards (mention trap only).
    assert (s3.trap_candidate, s3.trap_mention, s3.trap_confusable) == (False, True, False)


def test_pilot_02_trap_checkpoints_in_detail():
    """pilot-02: the open dispute at S2 and the Yelp suggestion at S3 are candidate traps; nothing else is."""
    e = pilot_timeline("pilot-02").expected
    for qid in ("dataset.train@S2", "dataset.train@S3", "dataset.train@S4"):
        assert (e[qid].trap_candidate, e[qid].trap_mention, e[qid].trap_confusable) == (True, False, False), qid
    for qid in ("dataset.train@S1", "task.label_audit@S1", "task.label_audit@S2", "task.label_audit@S3",
                "task.label_audit@S4", "dataset.train@S4-previous"):
        assert not (e[qid].trap_candidate or e[qid].trap_mention or e[qid].trap_confusable), qid


@pytest.mark.parametrize("key", list(VALUE_SETS), ids=lambda k: f"{k[0]}:{k[1]}")
def test_value_sets_at_checkpoints(key):
    """Pins accepted, stale, unconfirmed and confusable spellings (normalised, aliases included)."""
    scenario_id, qid = key
    e = pilot_timeline(scenario_id).expected[qid]
    accepted, stale, unconfirmed, confusable = VALUE_SETS[key]
    assert set(e.accepted_values) == accepted
    assert set(e.stale_values) == stale
    assert set(e.unconfirmed_values) == unconfirmed
    assert set(e.confusable_values) == confusable


@pytest.mark.parametrize("key", list(CURRENT_FORMS), ids=lambda k: f"{k[0]}:{k[1]}")
def test_history_questions_list_the_current_value(key):
    """A 'previous' or 'as of' question records today's value, so giving it can be scored as current_as_historical."""
    scenario_id, qid = key
    e = pilot_timeline(scenario_id).expected[qid]
    assert set(e.current_values) == CURRENT_FORMS[key]
    assert not (set(e.current_values) & set(e.accepted_values))
    assert e.stale_values == e.unconfirmed_values == e.confusable_values == []


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_value_sets_never_overlap(scenario_id):
    """Each spelling lands in at most one set, so every answer has one outcome."""
    for e in pilot_timeline(scenario_id).expected.values():
        sets = [set(e.accepted_values), set(e.stale_values), set(e.unconfirmed_values), set(e.confusable_values)]
        for i, a in enumerate(sets):
            for b in sets[i + 1:]:
                assert not a & b, e.question_id


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_mention_trap_never_overlaps_candidate_trap(scenario_id):
    """trap_mention is defined only where the newest record is right, so it never co-occurs with trap_candidate."""
    for e in pilot_timeline(scenario_id).expected.values():
        assert not (e.trap_candidate and e.trap_mention), e.question_id


# ---------------------------------------------------------------------------
# Gold operations and episodes
# ---------------------------------------------------------------------------


def test_pilot_01_gold_operations():
    """Acts become operations: suggest -> ADD proposed, revise -> SUPERSEDE closing the same-value proposal,
    accept -> SUPERSEDE citing the suggestion, restate -> KEEP, mention -> nothing."""
    timeline = pilot_timeline("pilot-01")
    ops = {turn: [(o.op, o.add_as, o.item, o.value, o.targets, o.source_turn_ids) for o in timeline.ops_by_turn[turn]]
           for turn in timeline.turn_order}
    s, m, n = "model.sentiment", "metric.primary", "model.ner"
    assert ops["S1-T1"] == [("ADD", "active", s, "BERT", [], ["S1-T1"])]
    assert ops["S1-T2"] == [("ADD", "proposed", m, "accuracy", [], ["S1-T2"])]  # a suggestion, though phrased as a question
    assert ops["S1-T3"] == [("ADD", "active", m, "accuracy", [record_id(m, "S1-T2")], ["S1-T3", "S1-T2"])]  # accepts it
    assert ops["S2-T3"] == [("ADD", "proposed", s, "DistilBERT", [], ["S2-T3"])]
    assert ops["S2-T5"] == [("ADD", "active", n, "spaCy", [], ["S2-T5"])]
    assert ops["S3-T1"] == []  # a mention
    assert ops["S3-T2"] == [("SUPERSEDE", None, s, "DistilBERT", [record_id(s, "S1-T1"), record_id(s, "S2-T3")],
                             ["S3-T2"])]
    assert ops["S3-T3"] == [("ADD", "proposed", m, "macro-F1", [], ["S3-T3"])]
    assert ops["S3-T4"] == [("SUPERSEDE", None, m, "macro-F1", [record_id(m, "S1-T3"), record_id(m, "S3-T3")],
                             ["S3-T4", "S3-T3"])]
    assert ops["S3-T6"] == []
    assert ops["S4-T1"] == [("KEEP", None, s, "DistilBERT", [record_id(s, "S3-T2")], ["S4-T1"]),
                            ("KEEP", None, m, "macro-F1", [record_id(m, "S3-T4")], ["S4-T1"])]
    assert ops["S4-T2"] == []
    total = sum(len(v) for v in ops.values())
    assert total == 10  # 13 script events minus 3 mentions


def test_pilot_02_contest_and_restate_operations():
    """contest -> FLAG on the active record; restate -> KEEP, which declines the open claim."""
    timeline = pilot_timeline("pilot-02")
    flag = timeline.ops_by_turn["S2-T1"][0]
    assert (flag.op, flag.value, flag.targets) == ("FLAG", "SST-2", [record_id("dataset.train", "S1-T1")])
    keep = timeline.ops_by_turn["S3-T1"][0]
    assert (keep.op, keep.targets) == ("KEEP", [record_id("dataset.train", "S1-T1")])
    state = timeline.log_after_session["S3"].item_state("dataset.train")
    assert [(r.value, r.status) for r in state.history] == [("SST-2", "declined")]
    assert [r.value for r in state.proposed] == ["Yelp"]


def test_gold_candidates_cite_only_their_own_turn():
    """Even an acceptance's candidate cites only its own turn; linking it to the suggestion is the resolver's job."""
    timeline = pilot_timeline("pilot-01")
    (candidate,) = timeline.candidates_by_turn["S3-T4"]
    assert candidate.source_turn_ids == ["S3-T4"]
    assert candidate.value == "macro-F1"
    assert candidate.speaker == "Mei"
    assert timeline.gold_op_for(candidate.candidate_id).source_turn_ids == ["S3-T4", "S3-T3"]
    assert timeline.candidates_by_turn["S3-T6"] == []  # a mention ("BERT was too slow anyway") yields no candidate


def test_episodes_group_repeated_unchanged_checkpoints():
    """Automatic questions that repeat an unchanged gold state share an episode; a change starts a new one."""
    e = pilot_timeline("pilot-01").expected
    episode = {qid: x.episode for qid, x in e.items()}
    assert len({episode["model.sentiment@S1"], episode["model.sentiment@S2"], episode["model.sentiment@S3"]}) == 3
    assert episode["model.sentiment@S3"] == episode["model.sentiment@S4"]
    assert episode["metric.primary@S1"] == episode["metric.primary@S2"] != episode["metric.primary@S3"]
    assert episode["metric.primary@S3"] == episode["metric.primary@S4"]
    assert episode["model.ner@S2"] != episode["model.ner@S3"] == episode["model.ner@S4"]  # confusable trap appears
    assert episode["model.sentiment@S3-previous"] not in {episode[f"model.sentiment@S{i}"] for i in range(1, 5)}
    assert all(x.episode for x in e.values())


# ---------------------------------------------------------------------------
# Question expansion and the act rules on small inline scenarios
# ---------------------------------------------------------------------------


def test_automatic_questions_start_at_the_first_memory_bearing_statement():
    """An item's automatic question starts in the first session with a non-mention act; mentions do not count."""
    ids = [q.question_id for q in expand_questions(pilot("pilot-01"))]
    assert "model.ner@S1" not in ids and "model.ner@S2" in ids
    assert ids[:2] == ["metric.primary@S1", "model.sentiment@S1"]  # sorted by session, then id
    assert ids[-1] == "model.sentiment@S4"


def _scenario(script: list[dict], questions: list[dict] | None = None, items: list[dict] | None = None) -> Scenario:
    """A one-session scenario with six turns and the given script."""
    return Scenario.model_validate({
        "scenario_id": "inline", "title": "inline", "category": "explicit_revision", "split": "dev",
        "author": "tests", "project_id": "p",
        "items": items or [{"key": "model.x", "kind": "decision", "description": "d", "ask": "Which model?",
                            "values": {"A": ["a-alias"], "B": [], "C": []}}],
        "sessions": [{"id": "S1", "date": "2026-01-05",
                      "turns": [{"id": f"S1-T{i}", "speaker": "Ana", "text": "..."} for i in range(1, 7)]}],
        "script": script, "questions": questions or [],
    })


def test_suggestion_alone_gives_none_with_the_suggestion_unconfirmed():
    """Only a suggestion so far: the expected answer is 'none', the proposal is unconfirmed, and it is a candidate trap."""
    timeline = replay(_scenario([{"turn": "S1-T1", "act": "suggest", "item": "model.x", "value": "A"}]))
    e = timeline.expected["model.x@S1"]
    assert (e.expected_status, e.expected_value) == ("none", None)
    assert set(e.unconfirmed_values) == {"a", "a-alias"}
    assert e.required_support == ["S1-T1"]
    assert e.trap_candidate is True


def test_accept_without_a_prior_decision_settles_the_value():
    """suggest then accept with nothing decided: the accepted value becomes the answer, citing both turns."""
    timeline = replay(_scenario([
        {"turn": "S1-T1", "act": "suggest", "item": "model.x", "value": "A"},
        {"turn": "S1-T2", "act": "accept", "item": "model.x", "accepts": "S1-T1"},
    ]))
    e = timeline.expected["model.x@S1"]
    assert (e.expected_status, e.expected_value) == ("answer", "A")
    assert e.required_support == ["S1-T1", "S1-T2"]
    assert e.stale_values == []  # the closed proposal had the same value


def test_contest_then_revise_to_a_third_value():
    """A decided, B contested, C revised: the answer is C, A is stale and B is unconfirmed (declined), no conflict."""
    timeline = replay(_scenario([
        {"turn": "S1-T1", "act": "decide", "item": "model.x", "value": "A"},
        {"turn": "S1-T2", "act": "contest", "item": "model.x", "value": "B"},
        {"turn": "S1-T3", "act": "revise", "item": "model.x", "value": "C"},
    ]))
    e = timeline.expected["model.x@S1"]
    assert (e.expected_status, e.expected_value) == ("answer", "C")
    assert set(e.stale_values) == {"a", "a-alias"}
    assert e.unconfirmed_values == ["b"]


def test_revert_gives_the_middle_value_as_previous():
    """A -> B -> A: 'what did we use before?' is B."""
    timeline = replay(_scenario(
        [{"turn": "S1-T1", "act": "decide", "item": "model.x", "value": "A"},
         {"turn": "S1-T2", "act": "revise", "item": "model.x", "value": "B"},
         {"turn": "S1-T3", "act": "revise", "item": "model.x", "value": "A"}],
        [{"id": "prev", "after": "S1", "kind": "previous", "item": "model.x", "text": "Before?"}]))
    e = timeline.expected["prev"]
    assert (e.expected_status, e.expected_value) == ("answer", "B")
    assert e.required_support == ["S1-T2", "S1-T3"]
    assert set(timeline.expected["model.x@S1"].stale_values) == {"b"}  # A is current again, so only B is stale


@pytest.mark.parametrize("script, message", [
    ([{"turn": "S1-T1", "act": "revise", "item": "model.x", "value": "A"}], "no active value"),
    ([{"turn": "S1-T1", "act": "decide", "item": "model.x", "value": "A"},
      {"turn": "S1-T2", "act": "decide", "item": "model.x", "value": "B"}], "already has an active value"),
    ([{"turn": "S1-T1", "act": "decide", "item": "model.x", "value": "A"},
      {"turn": "S1-T2", "act": "restate", "item": "model.x", "value": "B"}], "must repeat the active value"),
    ([{"turn": "S1-T1", "act": "decide", "item": "model.x", "value": "A"},
      {"turn": "S1-T2", "act": "suggest", "item": "model.x", "value": "A"}], "label it restate"),
    ([{"turn": "S1-T1", "act": "decide", "item": "model.x", "value": "A"},
      {"turn": "S1-T2", "act": "contest", "item": "model.x", "value": "A"}], "needs an active value that differs"),
    ([{"turn": "S1-T1", "act": "decide", "item": "model.x", "value": "A"},
      {"turn": "S1-T2", "act": "accept", "item": "model.x", "accepts": "S1-T1"}], "has no value"),
    ([{"turn": "S1-T1", "act": "suggest", "item": "model.x", "value": "A"},
      {"turn": "S1-T2", "act": "accept", "item": "model.x", "accepts": "S1-T1"},
      {"turn": "S1-T3", "act": "accept", "item": "model.x", "accepts": "S1-T1"}], "not an open suggestion"),
])
def test_scripts_that_break_an_act_rule_are_refused(script, message):
    """The replay refuses a script whose acts do not fit the state they are applied to."""
    with pytest.raises(ScriptError, match=message):
        replay(_scenario(script))


def test_accepted_forms_include_task_progress_words():
    """For a task, everyday words count: 'done' is a spelling of completed."""
    scenario = pilot("pilot-02")
    assert set(accepted_forms(scenario, "task.label_audit", "completed")) == COMPLETED
    assert accepted_forms(scenario, "task.label_audit", None) == []
