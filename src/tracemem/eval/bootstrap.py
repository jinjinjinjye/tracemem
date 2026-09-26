"""Uncertainty by resampling whole scenarios.

Questions from one scenario share a conversation, so they are not independent.
Resampling scenarios (a cluster bootstrap) keeps each scenario's questions
together; a paired bootstrap resamples the same scenarios for two systems.
With ``stratify=True`` scenarios are resampled within their category, because
the benchmark fixes how many scenarios each category has.

An interval is returned only when at least ``min_scenarios`` scenarios
contribute to the metric; below that, only the point estimate is reported.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from tracemem.eval.metrics import ScoredAnswer, Value


@dataclass(frozen=True)
class Interval:
    estimate: float | None
    low: float | None
    high: float | None
    n_scenarios: int  # scenarios that contribute at least one question to the metric

    def fmt(self, digits: int = 3) -> str:
        if self.estimate is None:
            return "n/a"
        if self.low is None:
            return f"{self.estimate:.{digits}f}"
        return f"{self.estimate:.{digits}f} [{self.low:.{digits}f}, {self.high:.{digits}f}]"


def _by_scenario(rows: list[ScoredAnswer]) -> dict[str, list[ScoredAnswer]]:
    groups: dict[str, list[ScoredAnswer]] = {}
    for r in rows:
        groups.setdefault(r.scenario_id, []).append(r)
    return groups


def _contributing(metric, groups: dict[str, list[ScoredAnswer]]) -> int:
    return sum(1 for rows in groups.values() if metric(rows).n > 0)


def _resample(ids: list[str], strata: dict[str, str], rng: random.Random) -> list[str]:
    if not strata:
        return [rng.choice(ids) for _ in ids]
    by_stratum: dict[str, list[str]] = {}
    for sid in ids:
        by_stratum.setdefault(strata.get(sid, ""), []).append(sid)
    chosen: list[str] = []
    for members in by_stratum.values():
        chosen.extend(rng.choice(members) for _ in members)
    return chosen


def _strata(rows: list[ScoredAnswer]) -> dict[str, str]:
    """Scenario -> category, or {} (plain resampling) when any category has fewer than two scenarios.

    A category with a single scenario has nothing to resample, so stratifying on
    it would report a spuriously narrow interval.
    """
    strata = {r.scenario_id: r.category for r in rows}
    sizes: dict[str, int] = {}
    for category in strata.values():
        sizes[category] = sizes.get(category, 0) + 1
    return strata if sizes and min(sizes.values()) >= 2 else {}


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = q * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap(metric: Callable[[list[ScoredAnswer]], Value], rows: list[ScoredAnswer],
              n: int = 2000, seed: int = 0, level: float = 0.95, stratify: bool = False,
              min_scenarios: int = 5) -> Interval:
    groups = _by_scenario(rows)
    ids = sorted(groups)
    point = metric(rows).value
    contributing = _contributing(metric, groups)
    if point is None or contributing < max(2, min_scenarios):
        return Interval(point, None, None, contributing)
    strata = _strata(rows) if stratify else {}
    rng = random.Random(seed)
    draws: list[float] = []
    for _ in range(n):
        sample = [r for sid in _resample(ids, strata, rng) for r in groups[sid]]
        value = metric(sample).value
        if value is not None:
            draws.append(value)
    if not draws:
        return Interval(point, None, None, contributing)
    tail = (1 - level) / 2
    return Interval(point, _percentile(draws, tail), _percentile(draws, 1 - tail), contributing)


def paired_bootstrap(metric: Callable[[list[ScoredAnswer]], Value], rows_a: list[ScoredAnswer],
                     rows_b: list[ScoredAnswer], n: int = 2000, seed: int = 0, level: float = 0.95,
                     stratify: bool = False, min_scenarios: int = 5) -> Interval:
    """Difference metric(a) - metric(b) over the scenarios both systems answered."""
    groups_a, groups_b = _by_scenario(rows_a), _by_scenario(rows_b)
    ids = sorted(set(groups_a) & set(groups_b))
    a_all = [r for sid in ids for r in groups_a[sid]]
    b_all = [r for sid in ids for r in groups_b[sid]]
    va, vb = metric(a_all).value, metric(b_all).value
    contributing = _contributing(metric, {sid: groups_a[sid] for sid in ids})
    if va is None or vb is None:
        return Interval(None, None, None, contributing)
    point = va - vb
    if contributing < max(2, min_scenarios):
        return Interval(point, None, None, contributing)
    strata = _strata(a_all) if stratify else {}
    rng = random.Random(seed)
    draws: list[float] = []
    for _ in range(n):
        chosen = _resample(ids, strata, rng)
        sa = metric([r for sid in chosen for r in groups_a[sid]]).value
        sb = metric([r for sid in chosen for r in groups_b[sid]]).value
        if sa is not None and sb is not None:
            draws.append(sa - sb)
    if not draws:
        return Interval(point, None, None, contributing)
    tail = (1 - level) / 2
    return Interval(point, _percentile(draws, tail), _percentile(draws, 1 - tail), contributing)
