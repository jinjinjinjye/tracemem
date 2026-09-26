"""Shared helpers for the tests: where things are, the five pilot scenarios, and small builders.

Test modules import this file directly (``from support import ...``); pytest puts
the tests folder on the import path because it has no ``__init__.py``.
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

import yaml

from tracemem.bench.load import load_scenario
from tracemem.bench.replay import GoldTimeline, replay
from tracemem.eval.harness import run_scenario
from tracemem.eval.metrics import ScoredAnswer
from tracemem.schema import Answer, ExpectedAnswer, Question, Scenario

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
FIXTURES = TESTS / "fixtures"
DEV = REPO / "benchmark" / "scenarios" / "dev"
MINIMAL = FIXTURES / "minimal.yaml"

PILOT_IDS = ["pilot-01", "pilot-02", "pilot-03", "pilot-04", "pilot-05"]


def pilot_path(scenario_id: str) -> Path:
    """The file of one pilot, e.g. pilot_path("pilot-01") -> .../pilot-01-suggestion-after-decision.yaml."""
    matches = sorted(DEV.glob(f"{scenario_id}-*.yaml"))
    assert len(matches) == 1, f"expected exactly one file for {scenario_id}, found {matches}"
    return matches[0]


@lru_cache(maxsize=None)
def pilot(scenario_id: str) -> Scenario:
    return load_scenario(pilot_path(scenario_id))


@lru_cache(maxsize=None)
def pilot_timeline(scenario_id: str) -> GoldTimeline:
    """The replayed gold of one pilot. Shared between tests, so never modify it."""
    return replay(pilot(scenario_id))


def raw_yaml(path: Path) -> dict:
    """The scenario file as plain data, without going through the schema or the replay."""
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def minimal_dict() -> dict:
    """A fresh, mutable copy of tests/fixtures/minimal.yaml."""
    return copy.deepcopy(raw_yaml(MINIMAL))


def run_on_pilots(spec, condition: str = "end_to_end") -> list[ScoredAnswer]:
    """Run one registered system over every pilot and return all scored answers."""
    rows: list[ScoredAnswer] = []
    for sid in PILOT_IDS:
        scenario_rows, _ = run_scenario(spec, pilot(sid), pilot_timeline(sid), condition=condition)
        rows.extend(scenario_rows)
    return rows


def turn_clock(*turn_ids: str) -> dict[str, datetime]:
    """Synthetic times for hand-built operation logs: one minute apart, in the order given."""
    start = datetime(2026, 1, 5, 10, 0)
    return {turn: start + timedelta(minutes=index) for index, turn in enumerate(turn_ids)}


def scored(question_id: str = "q", *, scenario: str = "s1", kind: str = "current", status: str = "answer",
           value: str | None = "x", outcome: str = "correct", answer: Answer | None = None,
           accepted=None, stale=(), unconfirmed=(), confusable=(), current=(), required=(), additional=(),
           episode: str = "", visible=("S1-T1",), category: str = "", **traps) -> ScoredAnswer:
    """A hand-built ScoredAnswer for metric tests. The outcome is given directly, not computed."""
    if accepted is None:
        accepted = [value] if status == "answer" and value is not None else []
    question = Question(question_id=question_id, scenario_id=scenario, after="S1", kind=kind,
                        item="model.x", text="?", session="S1" if kind == "as_of" else None)
    expected = ExpectedAnswer(
        question_id=question_id, scenario_id=scenario, kind=kind, item="model.x", after="S1",
        expected_status=status, expected_value=value if status == "answer" else None,
        accepted_values=list(accepted), stale_values=list(stale), unconfirmed_values=list(unconfirmed),
        confusable_values=list(confusable), current_values=list(current), required_support=list(required),
        additional_support=list(additional), episode=episode, **traps,
    )
    return ScoredAnswer(question, expected, answer or Answer(status="abstain"), outcome, frozenset(visible), category)
