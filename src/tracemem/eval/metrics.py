"""Aggregate metrics over scored answers (docs/metrics.md).

Every metric is a rate or a mean over a stated set of questions (its
denominator). A metric whose denominator is empty is reported as None, never 0.
Refusals stay in every denominator, and the non-answer rate is reported beside
every error rate, so a system cannot look safe by declining to answer.

Automatic checkpoint questions repeat while an item's gold state is unchanged.
With ``weighting="episode"`` each such run of repeats counts once in total.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from tracemem.schema import Answer, ExpectedAnswer, Question


@dataclass(frozen=True)
class ScoredAnswer:
    question: Question
    expected: ExpectedAnswer
    answer: Answer
    outcome: str
    visible_turns: frozenset[str]  # every turn the system had observed when it answered
    category: str = ""

    @property
    def scenario_id(self) -> str:
        return self.question.scenario_id


@dataclass(frozen=True)
class Value:
    value: float | None
    n: int  # number of questions in the denominator

    def fmt(self, digits: int = 3) -> str:
        return "n/a" if self.value is None else f"{self.value:.{digits}f}"


Weights = dict[int, float]

PRESENTED_AS_CURRENT = ("stale", "unconfirmed_as_current", "confusable_as_current", "false_certainty", "wrong_other")
NON_ANSWERS = ("missed", "false_conflict", "abstained")


def _episode_key(r: ScoredAnswer) -> tuple[str, str]:
    return (r.scenario_id, r.expected.episode or r.question.question_id)


def episode_weights(rows: list[ScoredAnswer]) -> Weights:
    """Weight each question 1/n, where n is the number of distinct questions sharing its scenario and episode.

    Distinct rows are counted once, so a scenario that a bootstrap resample draws
    twice keeps its full weight each time it appears.
    """
    distinct = {id(r): r for r in rows}.values()
    sizes: dict[tuple[str, str], int] = {}
    for r in distinct:
        sizes[_episode_key(r)] = sizes.get(_episode_key(r), 0) + 1
    return {id(r): 1.0 / sizes[_episode_key(r)] for r in distinct}


def _rate(rows, in_denominator: Callable, in_numerator: Callable, weights: Weights | None = None) -> Value:
    pool = [r for r in rows if in_denominator(r)]
    if not pool:
        return Value(None, 0)
    w = (lambda r: weights[id(r)]) if weights else (lambda r: 1.0)
    total = sum(w(r) for r in pool)
    return Value(sum(w(r) for r in pool if in_numerator(r)) / total, len(pool))


def _mean(rows, in_pool: Callable, score: Callable, weights: Weights | None = None) -> Value:
    pool = [r for r in rows if in_pool(r)]
    if not pool:
        return Value(None, 0)
    w = (lambda r: weights[id(r)]) if weights else (lambda r: 1.0)
    total = sum(w(r) for r in pool)
    return Value(sum(w(r) * score(r) for r in pool) / total, len(pool))


def _current(r: ScoredAnswer) -> bool:
    return r.question.kind == "current"


def _settled(r: ScoredAnswer) -> bool:
    return _current(r) and r.expected.expected_status == "answer"


# -- current-state questions ----------------------------------------------------


def current_accuracy(rows, weights=None):
    return _rate(rows, _current, lambda r: r.outcome == "correct", weights)


def stale_answer_rate(rows, weights=None):
    """Primary metric against plain similarity: an old, replaced value given as current."""
    return _rate(rows, lambda r: _settled(r) and bool(r.expected.stale_values), lambda r: r.outcome == "stale", weights)


def incorrect_replacement_rate(rows, weights=None):
    """A suggestion, disputed claim or another item's value given as the settled one."""

    def tempted(r: ScoredAnswer) -> bool:
        e = r.expected
        if not _current(r) or e.expected_status == "conflict":
            return False
        return e.expected_status == "none" or bool(e.unconfirmed_values) or bool(e.confusable_values)

    return _rate(rows, tempted, lambda r: r.outcome in ("unconfirmed_as_current", "confusable_as_current"), weights)


def presented_as_current_rate(rows, weights=None):
    """Any wrong value presented as settled: the comparison metric against similarity + recency.

    On current questions, accuracy + this rate + the share of non-answers is 1.
    """
    return _rate(rows, _current, lambda r: r.outcome in PRESENTED_AS_CURRENT, weights)


def false_certainty_rate(rows, weights=None):
    return _rate(
        rows,
        lambda r: _current(r) and r.expected.expected_status == "conflict",
        lambda r: r.outcome == "false_certainty",
        weights,
    )


def false_conflict_rate(rows, weights=None):
    """Over-caution: a conflict reported where the matter is settled or simply undecided."""
    return _rate(
        rows,
        lambda r: _current(r) and r.expected.expected_status in ("answer", "none"),
        lambda r: r.outcome == "false_conflict",
        weights,
    )


def non_answer_rate(rows, weights=None):
    """Failing to commit where something is on record: declining, wrongly reporting a conflict, or
    saying nothing is settled, on questions whose gold is a settled value or an open dispute."""
    return _rate(
        rows,
        lambda r: _current(r) and r.expected.expected_status in ("answer", "conflict"),
        lambda r: r.outcome in NON_ANSWERS,
        weights,
    )


def abstention_rate(rows, weights=None):
    return _rate(rows, _current, lambda r: r.outcome == "abstained", weights)


# -- historical questions --------------------------------------------------------


def historical_accuracy(rows, weights=None):
    return _rate(rows, lambda r: r.question.kind in ("previous", "as_of"), lambda r: r.outcome == "correct", weights)


# -- citations and evidence ---------------------------------------------------------


def _support(r: ScoredAnswer) -> set[str]:
    return set(r.expected.required_support) | set(r.expected.additional_support)


def _has_evidence(r: ScoredAnswer) -> bool:
    return r.expected.expected_status in ("answer", "conflict") and bool(r.expected.required_support)


def citation_validity(rows, weights=None):
    """Of answers that cite anything, the share whose every citation is a turn the system had seen."""
    return _rate(
        rows,
        lambda r: bool(r.answer.cited_turn_ids),
        lambda r: all(t in r.visible_turns for t in r.answer.cited_turn_ids),
        weights,
    )


def supported_answer_rate(rows, weights=None):
    """Common denominator for every system: correct AND citing a supporting turn; wrong or uncited counts as no."""
    return _rate(
        rows,
        _has_evidence,
        lambda r: r.outcome == "correct" and bool(set(r.answer.cited_turn_ids) & _support(r)),
        weights,
    )


def citation_coverage(rows, weights=None):
    """Common denominator: the share of required support cited, counting a wrong answer as 0."""

    def score(r: ScoredAnswer) -> float:
        if r.outcome != "correct":
            return 0.0
        required = set(r.expected.required_support)
        return len(set(r.answer.cited_turn_ids) & required) / len(required)

    return _mean(rows, _has_evidence, score, weights)


def evidence_recall(rows, weights=None):
    """Diagnostic: the share of required support among the turns behind the system's context."""
    return _mean(
        rows,
        lambda r: _has_evidence(r) and bool(r.answer.context_turn_ids),
        lambda r: len(set(r.answer.context_turn_ids) & set(r.expected.required_support)) / len(r.expected.required_support),
        weights,
    )


METRICS: dict[str, Callable] = {
    "current_accuracy": current_accuracy,
    "stale_answer_rate": stale_answer_rate,
    "incorrect_replacement_rate": incorrect_replacement_rate,
    "presented_as_current_rate": presented_as_current_rate,
    "false_certainty_rate": false_certainty_rate,
    "false_conflict_rate": false_conflict_rate,
    "non_answer_rate": non_answer_rate,
    "abstention_rate": abstention_rate,
    "historical_accuracy": historical_accuracy,
    "citation_validity": citation_validity,
    "supported_answer_rate": supported_answer_rate,
    "citation_coverage": citation_coverage,
    "evidence_recall": evidence_recall,
}

# Question-level subsets. Categories are authoring quotas; comparisons use these flags.
SUBSETS: dict[str, Callable[[ScoredAnswer], bool]] = {
    "all": lambda r: True,
    "trap_candidate": lambda r: r.expected.trap_candidate,
    "trap_mention": lambda r: r.expected.trap_mention,
    "trap_confusable": lambda r: r.expected.trap_confusable,
    "any_trap": lambda r: r.expected.trap_candidate or r.expected.trap_mention or r.expected.trap_confusable,
    "no_trap": lambda r: not (r.expected.trap_candidate or r.expected.trap_mention or r.expected.trap_confusable),
}


def compute_all(rows: list[ScoredAnswer], weighting: str = "question") -> dict[str, dict[str, Value]]:
    """metric name -> subset name -> Value. ``weighting`` is "question" or "episode"."""
    if weighting not in ("question", "episode"):
        raise ValueError(f"unknown weighting {weighting!r}")
    out: dict[str, dict[str, Value]] = {}
    for subset, keep in SUBSETS.items():
        chosen = [r for r in rows if keep(r)]
        weights = episode_weights(chosen) if weighting == "episode" else None
        for name, fn in METRICS.items():
            out.setdefault(name, {})[subset] = fn(chosen, weights)
    return out


def outcome_counts(rows: list[ScoredAnswer]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.outcome] = counts.get(r.outcome, 0) + 1
    return counts
