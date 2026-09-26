"""Uncertainty intervals from resampling whole scenarios (eval/bootstrap.py)."""

from __future__ import annotations

import random

import pytest

from support import scored
from tracemem.eval.bootstrap import Interval, _resample, _strata, bootstrap, paired_bootstrap
from tracemem.eval.metrics import current_accuracy, historical_accuracy
from tracemem.eval.report import _metric
from tracemem.schema import Answer


def scenario_rows(scenario: str, correct: int, total: int = 4, category: str = "a", kind: str = "current"):
    """`total` questions from one scenario, the first `correct` of them answered correctly."""
    return [
        scored(f"{scenario}-q{i}", scenario=scenario, kind=kind, category=category,
               outcome="correct" if i < correct else "stale", answer=Answer(status="abstain"))
        for i in range(total)
    ]


def spread_rows(n_scenarios: int = 8, category_of=lambda i: "a"):
    """Scenarios with accuracies 0/4, 1/4, ... so that resampling moves the estimate."""
    rows = []
    for i in range(n_scenarios):
        rows += scenario_rows(f"s{i}", correct=i % 5, category=category_of(i))
    return rows


def test_bootstrap_is_deterministic_under_a_seed():
    rows = spread_rows()
    first = bootstrap(current_accuracy, rows, n=300, seed=11)
    assert first == bootstrap(current_accuracy, rows, n=300, seed=11)
    assert isinstance(first, Interval)


def test_different_seeds_give_different_draws():
    rows = spread_rows()
    a = bootstrap(current_accuracy, rows, n=300, seed=1)
    b = bootstrap(current_accuracy, rows, n=300, seed=2)
    assert a.estimate == b.estimate
    assert (a.low, a.high) != (b.low, b.high)


def test_interval_contains_the_estimate():
    rows = spread_rows()
    interval = bootstrap(current_accuracy, rows, n=500, seed=0)
    assert interval.estimate == pytest.approx(current_accuracy(rows).value)
    assert interval.low <= interval.estimate <= interval.high
    assert interval.low < interval.high
    assert interval.n_scenarios == 8


def test_interval_is_degenerate_when_every_scenario_scores_the_same():
    rows = [r for i in range(6) for r in scenario_rows(f"s{i}", correct=2)]
    interval = bootstrap(current_accuracy, rows, n=200, seed=0)
    assert (interval.estimate, interval.low, interval.high) == (0.5, 0.5, 0.5)


def test_identical_systems_have_a_paired_difference_of_exactly_zero():
    """Pairing resamples the same scenarios for both systems, so a system compared with itself differs by 0."""
    rows = spread_rows()
    diff = paired_bootstrap(current_accuracy, rows, rows, n=300, seed=3)
    assert (diff.estimate, diff.low, diff.high) == (0.0, 0.0, 0.0)
    assert diff.n_scenarios == 8


def test_paired_difference_has_the_right_sign():
    better = [r for i in range(6) for r in scenario_rows(f"s{i}", correct=3)]
    worse = [r for i in range(6) for r in scenario_rows(f"s{i}", correct=1 + i % 2)]
    diff = paired_bootstrap(current_accuracy, better, worse, n=300, seed=0)
    assert diff.estimate == pytest.approx(0.75 - 1.5 / 4)
    assert 0 < diff.low <= diff.estimate <= diff.high


def test_paired_bootstrap_uses_only_shared_scenarios():
    a = spread_rows(6) + scenario_rows("only-in-a", correct=0)
    b = spread_rows(6)
    assert paired_bootstrap(current_accuracy, a, b, n=100, seed=0).estimate == 0.0


def test_fewer_than_five_scenarios_give_no_interval():
    """With four scenarios the estimate is reported but the interval is not."""
    rows = spread_rows(4)
    interval = bootstrap(current_accuracy, rows, n=200, seed=0)
    assert interval.estimate == pytest.approx(current_accuracy(rows).value)
    assert (interval.low, interval.high) == (None, None)
    assert interval.n_scenarios == 4
    assert interval.fmt() == f"{interval.estimate:.3f}"
    assert paired_bootstrap(current_accuracy, rows, rows, n=200, seed=0).low is None
    assert bootstrap(current_accuracy, spread_rows(5), n=200, seed=0).low is not None


def test_only_scenarios_that_contribute_to_the_metric_count():
    """Seven scenarios, but only four have history questions: historical accuracy gets no interval."""
    rows = spread_rows(7)
    for i in range(4):
        rows += scenario_rows(f"s{i}", correct=1, total=2, kind="previous")
    interval = bootstrap(historical_accuracy, rows, n=200, seed=0)
    assert interval.n_scenarios == 4
    assert interval.low is None and interval.estimate == 0.5
    assert bootstrap(current_accuracy, rows, n=200, seed=0).n_scenarios == 7


def test_empty_metric_gives_no_estimate():
    interval = bootstrap(historical_accuracy, spread_rows(), n=100, seed=0)
    assert (interval.estimate, interval.low, interval.high) == (None, None, None)
    assert interval.fmt() == "n/a"


# -- stratification ------------------------------------------------------------------------------


def test_stratification_falls_back_when_a_category_has_one_scenario():
    """One scenario alone in its category cannot be resampled, so stratifying is dropped altogether."""
    rows = spread_rows(8, category_of=lambda i: "lonely" if i == 0 else "a")
    assert _strata(rows) == {}
    stratified = bootstrap(current_accuracy, rows, n=300, seed=5, stratify=True)
    plain = bootstrap(current_accuracy, rows, n=300, seed=5, stratify=False)
    assert stratified == plain


def test_stratification_is_used_when_every_category_has_two_scenarios():
    rows = spread_rows(8, category_of=lambda i: "a" if i < 4 else "b")
    strata = _strata(rows)
    assert strata == {f"s{i}": ("a" if i < 4 else "b") for i in range(8)}
    rng = random.Random(0)
    for _ in range(50):
        sample = _resample(sorted(strata), strata, rng)
        assert sum(strata[s] == "a" for s in sample) == 4  # each category keeps its size
        assert sum(strata[s] == "b" for s in sample) == 4
    stratified = bootstrap(current_accuracy, rows, n=300, seed=5, stratify=True)
    assert stratified.low <= stratified.estimate <= stratified.high


def test_episode_weighting_counts_a_scenario_drawn_twice_twice():
    """A resample [A, A, B] with A right and B wrong should score 2/3 under either weighting."""
    a = scored("a", scenario="A", outcome="correct", episode="e", answer=Answer(status="abstain"))
    b = scored("b", scenario="B", outcome="stale", episode="e", answer=Answer(status="abstain"))
    assert _metric("current_accuracy", "question")([a, a, b]).value == pytest.approx(2 / 3)
    assert _metric("current_accuracy", "episode")([a, a, b]).value == pytest.approx(2 / 3)
