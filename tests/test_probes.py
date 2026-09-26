"""Probes never look ahead: cutting a scenario after session k does not change any answer given by then.

A probe reads gold labels, so it could in principle peek at turns it has not
been shown yet. If it did, its answers at session k would change when the
sessions after k are removed. Every registered system (the probes and the
gold-stand-in pipeline) is checked on every pilot and every cut point.
"""

from __future__ import annotations

import pytest

from support import PILOT_IDS, pilot
from tracemem.eval.harness import run_scenario
from tracemem.schema import Scenario
from tracemem.systems import REGISTRY


def truncate(scenario: Scenario, k: int) -> Scenario:
    """The scenario as it would look if it ended after its k-th session."""
    data = scenario.model_dump()
    data["sessions"] = data["sessions"][:k]
    sessions = {s["id"] for s in data["sessions"]}
    turns = {t["id"] for s in data["sessions"] for t in s["turns"]}
    data["script"] = [e for e in data["script"] if e["turn"] in turns]
    data["questions"] = [q for q in data["questions"]
                         if q["after"] in sessions and (q["session"] is None or q["session"] in sessions)]
    return Scenario.model_validate(data)


def answers(spec, scenario: Scenario) -> dict:
    rows, _ = run_scenario(spec, scenario)
    return {r.question.question_id: (r.question.after, r.answer) for r in rows}


def test_truncate_keeps_only_the_first_sessions():
    cut = truncate(pilot("pilot-01"), 2)
    assert [s.id for s in cut.sessions] == ["S1", "S2"]
    assert {e.turn.split("-")[0] for e in cut.script} == {"S1", "S2"}
    assert cut.questions == []  # both explicit questions are asked after S3 or S4


@pytest.mark.parametrize("name", list(REGISTRY))
@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_answers_do_not_depend_on_later_sessions(scenario_id, name):
    spec = REGISTRY[name]
    full_scenario = pilot(scenario_id)
    full = answers(spec, full_scenario)
    for k in range(1, len(full_scenario.sessions)):
        kept = {s.id for s in full_scenario.sessions[:k]}
        cut = answers(spec, truncate(full_scenario, k))
        expected_ids = {qid for qid, (after, _) in full.items() if after in kept}
        assert set(cut) == expected_ids, f"cut after S{k}"
        for qid in expected_ids:
            assert cut[qid][1] == full[qid][1], f"{name} changed its answer to {qid} when cut after S{k}"
