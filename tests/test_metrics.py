"""Scorer self-tests: exact metric values, denominators, and the probes' known scores.

These tests exist to FAIL on a broken scorer (AGENTS.md, rule 5). Do not loosen
them to make a change pass; a change that needs them loosened is a scorer bug
until shown otherwise.
"""

from __future__ import annotations

import pytest

from support import PILOT_IDS, pilot_path, raw_yaml, run_on_pilots, scored
from tracemem.eval.classify import classify
from tracemem.eval.metrics import (
    METRICS,
    SUBSETS,
    compute_all,
    episode_weights,
    outcome_counts,
)
from tracemem.schema import Answer
from tracemem.systems import REGISTRY

VISIBLE = ("S1-T1", "S1-T2", "S1-T3")


def says(value, cited=(), context=()):
    return Answer(status="answer", value=value, cited_turn_ids=list(cited), context_turn_ids=list(context))


def hand_rows():
    """Eight scored answers whose metric values are worked out by hand in test_exact_metric_values."""
    return [
        # r1: settled value x (an older value 'old' was replaced), answered correctly with the right citation
        scored("r1", value="x", stale=["old"], required=["S1-T1"], visible=VISIBLE, outcome="correct",
               answer=says("x", ["S1-T1"], ["S1-T1", "S1-T2"])),
        # r2: the replaced value given; cites a turn the system never saw
        scored("r2", value="x", stale=["old"], required=["S1-T1"], visible=VISIBLE, outcome="stale",
               answer=says("old", ["S9-T9"]), trap_candidate=True),
        # r3: a suggestion given as settled
        scored("r3", value="x", unconfirmed=["sugg"], required=["S1-T2"], visible=VISIBLE,
               outcome="unconfirmed_as_current", answer=says("sugg", ["S1-T3"]), trap_candidate=True),
        # r4: an open dispute (with an older replaced value too), and the system picked a side
        scored("r4", status="conflict", value=None, stale=["old"], unconfirmed=["y"], required=["S1-T1", "S1-T2"],
               visible=VISIBLE, outcome="false_certainty", answer=says("y", [], ["S1-T1"]), trap_mention=True),
        # r5: nothing decided (only a suggestion), and the system said so
        scored("r5", status="none", value=None, unconfirmed=["s"], visible=VISIBLE, outcome="correct",
               answer=Answer(status="none")),
        # r6: settled, but the system reported a conflict
        scored("r6", value="x", required=["S1-T1"], visible=VISIBLE, outcome="false_conflict",
               answer=Answer(status="conflict", cited_turn_ids=["S1-T1"])),
        # r7: "what did we use before?", answered correctly, citing half of the required support
        scored("r7", kind="previous", value="p", required=["S1-T1", "S1-T2"], visible=VISIBLE, outcome="correct",
               answer=says("p", ["S1-T1"])),
        # r8: "what was it as of S1?", answered with today's value
        scored("r8", kind="as_of", value="q", current=["c"], required=["S1-T1"], visible=VISIBLE,
               outcome="current_as_historical", answer=says("c")),
    ]


def test_hand_rows_are_consistent_with_classify():
    """The outcomes written into hand_rows() are the ones classify() gives, so the rows are realistic."""
    for row in hand_rows():
        assert classify(row.answer, row.expected) == row.outcome, row.question.question_id


EXACT = {
    # metric: (value, denominator size), worked out by hand from hand_rows()
    "current_accuracy": (2 / 6, 6),  # r1, r5 correct among r1..r6
    "stale_answer_rate": (1 / 2, 2),  # denominator r1, r2 (r4 has stale values but is a conflict)
    "incorrect_replacement_rate": (1 / 2, 2),  # denominator r3, r5 (r4 has unconfirmed values but is a conflict)
    "presented_as_current_rate": (3 / 6, 6),  # r2 stale, r3 unconfirmed, r4 false certainty
    "false_certainty_rate": (1 / 1, 1),  # r4
    "false_conflict_rate": (1 / 5, 5),  # r6 among r1, r2, r3, r5, r6
    "non_answer_rate": (1 / 5, 5),  # r6 among the settled r1, r2, r3, r6 and the dispute r4 (answered correctly)
    "abstention_rate": (0.0, 6),
    "historical_accuracy": (1 / 2, 2),  # r7 right, r8 wrong
    "citation_validity": (4 / 5, 5),  # r2 cites an unseen turn; r1, r3, r6, r7 cite seen turns
    "supported_answer_rate": (2 / 7, 7),  # r1, r7 correct and citing support; r5 (none) has no evidence
    "citation_coverage": (1.5 / 7, 7),  # r1 1.0, r7 0.5, the rest 0
    "evidence_recall": (0.75, 2),  # r1 context covers 1/1, r4 context covers 1/2
}


@pytest.mark.parametrize("name", list(EXACT))
def test_exact_metric_values(name):
    value, n = EXACT[name]
    got = METRICS[name](hand_rows())
    assert got.n == n
    assert got.value == pytest.approx(value, abs=1e-12)


def test_every_metric_has_an_exact_check():
    assert set(EXACT) == set(METRICS)


def test_conflict_questions_are_outside_the_stale_and_replacement_denominators():
    """Removing the conflict question (r4) leaves both rates and their denominators unchanged."""
    rows = hand_rows()
    without_conflict = [r for r in rows if r.question.question_id != "r4"]
    for name in ("stale_answer_rate", "incorrect_replacement_rate"):
        assert METRICS[name](rows) == METRICS[name](without_conflict)
    # ...and a conflict question alone gives an empty denominator for both.
    only_conflict = [r for r in rows if r.question.question_id == "r4"]
    assert METRICS["stale_answer_rate"](only_conflict).value is None
    assert METRICS["incorrect_replacement_rate"](only_conflict).value is None


@pytest.mark.parametrize("name", list(METRICS))
def test_empty_denominator_gives_none_not_zero(name):
    value = METRICS[name]([])
    assert (value.value, value.n) == (None, 0)
    assert value.fmt() == "n/a"


def test_metric_with_no_eligible_question_is_none():
    """No conflict questions -> false_certainty_rate is None; no history questions -> historical_accuracy is None."""
    rows = [r for r in hand_rows() if r.question.question_id in ("r1", "r2")]
    assert METRICS["false_certainty_rate"](rows).value is None
    assert METRICS["historical_accuracy"](rows).value is None
    assert METRICS["current_accuracy"](rows).value == 0.5


def test_subsets_select_by_trap_flag():
    """Subsets split questions by trap flag: r2, r3 are candidate traps, r4 a mention trap."""
    table = compute_all(hand_rows())
    assert set(table["current_accuracy"]) == set(SUBSETS)
    assert table["current_accuracy"]["trap_candidate"].value == 0.0
    assert table["current_accuracy"]["trap_candidate"].n == 2
    assert table["current_accuracy"]["trap_mention"].n == 1
    assert table["current_accuracy"]["trap_confusable"].value is None
    assert table["current_accuracy"]["any_trap"].n == 3
    assert table["current_accuracy"]["no_trap"].value == pytest.approx(2 / 3)  # r1, r5 right; r6 wrong
    assert table["current_accuracy"]["all"].value == pytest.approx(2 / 6)


def test_outcome_counts():
    assert outcome_counts(hand_rows()) == {"correct": 3, "stale": 1, "unconfirmed_as_current": 1,
                                           "false_certainty": 1, "false_conflict": 1, "current_as_historical": 1}


def test_unknown_weighting_is_rejected():
    with pytest.raises(ValueError):
        compute_all(hand_rows(), weighting="scenario")


# -- episode weighting ----------------------------------------------------------------------------


def test_episode_weighting_counts_a_repeated_checkpoint_once():
    """Three repeats of one unchanged stale checkpoint plus one other question: 3/4 per question, 1/2 per episode."""
    rows = [scored(f"rep{i}", value="x", stale=["old"], outcome="stale", answer=says("old"), episode="e1")
            for i in range(3)]
    rows.append(scored("other", value="x", stale=["old"], outcome="correct", answer=says("x"), episode="e2"))
    assert compute_all(rows)["stale_answer_rate"]["all"].value == pytest.approx(3 / 4)
    by_episode = compute_all(rows, weighting="episode")
    assert by_episode["stale_answer_rate"]["all"].value == pytest.approx(1 / 2)
    assert by_episode["current_accuracy"]["all"].value == pytest.approx(1 / 2)
    assert by_episode["stale_answer_rate"]["all"].n == 4  # n still counts questions


def test_episode_weights_are_per_scenario_and_default_to_the_question():
    rows = [
        scored("a", scenario="s1", episode="e1"), scored("b", scenario="s1", episode="e1"),
        scored("c", scenario="s2", episode="e1"),  # same label, other scenario: a different episode
        scored("d", scenario="s2"), scored("e", scenario="s2"),  # no episode: each question is its own
    ]
    weights = episode_weights(rows)
    assert [weights[id(r)] for r in rows] == [0.5, 0.5, 1.0, 1.0, 1.0]


def test_pilot_episodes_share_weight():
    """On pilot-01, the unchanged S3 and S4 checkpoints of the sentiment model share one unit of weight."""
    rows = [r for r in run_on_pilots(REGISTRY["oracle"]) if r.scenario_id == "pilot-01"]
    by_row = episode_weights(rows)
    weights = {r.question.question_id: by_row[id(r)] for r in rows}
    assert weights["model.sentiment@S3"] == weights["model.sentiment@S4"] == 0.5
    assert weights["model.sentiment@S1"] == weights["model.sentiment@S2"] == 1.0
    assert weights["metric.primary@S1"] == weights["metric.primary@S2"] == 0.5


# -- the probes' known scores on the pilots ---------------------------------------------------------

ERROR_RATES = ("stale_answer_rate", "incorrect_replacement_rate", "presented_as_current_rate", "false_certainty_rate")


@pytest.mark.parametrize("weighting", ["question", "episode"])
def test_oracle_scores_perfectly(weighting):
    """The oracle replays the gold, so it is right on every question, cites correctly, and makes no error."""
    rows = run_on_pilots(REGISTRY["oracle"])
    assert {r.outcome for r in rows} == {"correct"}
    table = compute_all(rows, weighting=weighting)
    for name in ("current_accuracy", "historical_accuracy", "citation_validity", "supported_answer_rate",
                 "citation_coverage", "evidence_recall"):
        assert table[name]["all"].value == 1.0, name
    for name in ERROR_RATES + ("false_conflict_rate", "non_answer_rate", "abstention_rate"):
        assert table[name]["all"].value == 0.0, name
    for subset in SUBSETS:
        value = table["current_accuracy"][subset].value
        assert value in (1.0, None), subset


def first_value_stale_questions(path) -> set[str]:
    """Current questions where the item's first stated value has been replaced by the checkpoint.

    Computed straight from the YAML file with a few lines of bookkeeping, without
    the replay or the operation log: track each item's settled value, every value
    that was ever settled, and whether a dispute is open. The first value is stale
    at a checkpoint when it was settled once, is not the settled value now, and no
    dispute is open (during a dispute the right answer is 'conflict').
    """
    raw = raw_yaml(path)
    turn_session = {t["id"]: s["id"] for s in raw["sessions"] for t in s["turns"]}
    sessions = [s["id"] for s in raw["sessions"]]
    out = set()
    for item in raw["items"]:
        key = item["key"]
        events = [e for e in raw["script"] if e["item"] == key and e["act"] != "mention"]
        if not events or not item.get("ask"):
            continue
        suggestions, settled, ever_settled, disputed, first = {}, None, set(), False, None
        start = sessions.index(turn_session[events[0]["turn"]])
        for session in sessions:
            for e in (e for e in events if turn_session[e["turn"]] == session):
                act = e["act"]
                value = {"task_open": "open", "task_progress": e.get("progress"),
                         "accept": suggestions.get(e.get("accepts"))}.get(act, e.get("value"))
                first = first if first is not None else value
                if act == "suggest":
                    suggestions[e["turn"]] = value
                elif act == "contest":
                    disputed = True
                elif act == "restate":
                    disputed = False
                else:  # decide, task_open, revise, task_progress, accept all settle a value
                    settled, disputed = value, False
                    ever_settled.add(value)
            if sessions.index(session) >= start and not disputed and first in ever_settled - {settled}:
                out.add(f"{key}@{session}")
    return out


def test_independent_stale_sets_match_a_hand_count():
    """Guard for the helper above: its result on the pilots, listed by hand."""
    got = {sid: first_value_stale_questions(pilot_path(sid)) for sid in PILOT_IDS}
    assert got == {
        "pilot-01": {"model.sentiment@S3", "model.sentiment@S4", "metric.primary@S3", "metric.primary@S4"},
        "pilot-02": {"task.label_audit@S2", "task.label_audit@S4"},
        "pilot-03": {"model.ner@S3", "model.ner@S4"},
        "pilot-04": {"compute.gpu@S2", "compute.gpu@S3", "compute.gpu@S4", "task.baseline_runs@S2",
                     "task.baseline_runs@S4", "task.error_analysis@S3", "task.error_analysis@S4"},
        "pilot-05": {"model.baseline@S3", "model.baseline@S4"},
    }


def test_always_oldest_is_stale_exactly_where_the_first_value_was_replaced():
    """always-oldest answers with the first value ever stated; it must be scored 'stale' on exactly those
    current questions where that value has been replaced, and nowhere else."""
    rows = run_on_pilots(REGISTRY["always-oldest"])
    got = {(r.scenario_id, r.question.question_id) for r in rows if r.question.kind == "current" and r.outcome == "stale"}
    want = {(sid, qid) for sid in PILOT_IDS for qid in first_value_stale_questions(pilot_path(sid))}
    assert got == want
    assert compute_all(rows)["stale_answer_rate"]["all"].value > 0


# always-conflict is right on the one open dispute in the pilots (45 settled + 1 dispute), so 45/46.
@pytest.mark.parametrize("name, false_conflict, non_answer",
                         [("always-conflict", 1.0, 45 / 46), ("always-none", 0.0, 1.0)])
def test_refusal_bounds_have_no_value_errors_but_never_answer(name, false_conflict, non_answer):
    """A system that never commits makes none of the value errors, yet fails every settled question:
    this is why the non-answer rate is reported beside every error rate."""
    rows = run_on_pilots(REGISTRY[name])
    table = compute_all(rows)
    for metric in ERROR_RATES:
        assert table[metric]["all"].value == 0.0, metric
    assert table["non_answer_rate"]["all"].value == pytest.approx(non_answer)
    assert table["false_conflict_rate"]["all"].value == false_conflict
    assert table["current_accuracy"]["all"].value < 0.25


def test_latest_candidate_is_wrong_exactly_on_candidate_traps():
    """trap_candidate means 'the newest memory-bearing statement is not the answer', which is what the
    latest-candidate probe answers: on current questions it is right exactly when the flag is off."""
    rows = run_on_pilots(REGISTRY["latest-candidate"])
    for r in rows:
        if r.question.kind == "current":
            assert (r.outcome == "correct") == (not r.expected.trap_candidate), r.question.question_id


def test_latest_mention_is_wrong_on_candidate_and_mention_traps_in_the_pilots():
    """On the pilots, the newest mention of any kind is wrong exactly on candidate or mention traps."""
    rows = run_on_pilots(REGISTRY["latest-mention"])
    for r in rows:
        if r.question.kind == "current":
            trapped = r.expected.trap_candidate or r.expected.trap_mention
            assert (r.outcome == "correct") == (not trapped), r.question.question_id


def test_accuracy_wrong_assertions_and_non_answers_add_up_to_one():
    """On current questions every answer is correct, a wrong value presented as current, or a non-answer
    (including a wrongly reported 'none' or 'conflict'); the three rates must therefore sum to 1."""
    from tracemem.bench.load import load_split
    from tracemem.eval.harness import run
    from tracemem.eval.metrics import current_accuracy, presented_as_current_rate
    from tracemem.systems import REGISTRY

    scenarios = load_split("benchmark/scenarios", "dev")
    for name in ("oracle", "always-oldest", "latest-candidate", "latest-mention", "always-conflict", "always-none"):
        rows = [r for r in run(REGISTRY[name], scenarios, "dev").rows if r.question.kind == "current"]
        non_answers = sum(r.outcome in ("missed", "false_conflict", "abstained") for r in rows) / len(rows)
        total = current_accuracy(rows).value + presented_as_current_rate(rows).value + non_answers
        assert total == pytest.approx(1.0), name
