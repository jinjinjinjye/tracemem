"""Regression tests for the bugs found by the post-implementation review."""

import json

import pytest

from tracemem.eval.harness import run, run_scenario, write_run
from tracemem.eval.metrics import non_answer_rate
from tracemem.schema import Scenario
from tracemem.systems import REGISTRY

from support import minimal_dict


def _scenario(script, sessions=None, questions=()):
    data = minimal_dict()
    if sessions is not None:
        data["sessions"] = sessions
    data["script"] = script
    data["questions"] = list(questions)
    return Scenario.model_validate(data)


def test_trap_flags_do_not_depend_on_the_order_events_are_listed_within_a_turn():
    base = minimal_dict()
    first = base["sessions"][0]["turns"][0]["id"]
    second = base["sessions"][1]["turns"][0]["id"]
    a = [{"turn": first, "act": "decide", "item": "model.main", "value": "BERT"},
         {"turn": second, "act": "revise", "item": "model.main", "value": "DistilBERT"},
         {"turn": second, "act": "mention", "item": "model.main", "value": "BERT"}]
    b = [a[0], a[2], a[1]]
    from tracemem.bench.replay import replay
    flags = [tuple((e.trap_candidate, e.trap_mention, e.trap_confusable) for e in replay(_scenario(s)).expected.values())
             for s in (a, b)]
    assert flags[0] == flags[1]


def test_non_answer_on_an_open_dispute_counts_as_a_non_answer():
    rows = [r for r in run(REGISTRY["always-none"], [_pilot_02()], "dev").rows
            if r.question.kind == "current" and r.expected.expected_status == "conflict"]
    assert rows and non_answer_rate(rows).value == 1.0


def _pilot_02():
    from tracemem.bench.load import load_scenario
    return load_scenario("benchmark/scenarios/dev/pilot-02-unresolved-contradiction.yaml")


def test_duplicate_scenario_ids_are_refused():
    s = _pilot_02()
    with pytest.raises(ValueError, match="duplicate scenario_id"):
        run(REGISTRY["oracle"], [s, s], "dev")


def test_manifest_command_holds_no_absolute_path(tmp_path, monkeypatch):
    import sys
    monkeypatch.setattr(sys, "argv", ["/" + "home/someone/venv/bin/tracemem", "run", "--system", "oracle"])
    folder = write_run(run(REGISTRY["oracle"], [_pilot_02()], "dev"), tmp_path)
    command = json.loads((folder / "manifest.json").read_text())["command"]
    assert command == ["tracemem", "run", "--system", "oracle"]


def test_public_question_ids_cannot_be_rebuilt_without_the_salt():
    from tracemem.bench.replay import replay
    timeline = replay(_pilot_02())
    q = timeline.questions[0]
    assert timeline.public_id(q) != q.for_system().question_id


def test_probes_and_gold_pipeline_answer_as_of_an_empty_session():
    data = minimal_dict()
    data["sessions"].insert(1, {"id": "S2", "date": data["sessions"][0]["date"], "turns": []})
    for i, session in enumerate(data["sessions"][2:], start=3):
        old = session["id"]
        session["id"] = f"S{i}"
        for turn in session["turns"]:
            turn["id"] = turn["id"].replace(old + "-", f"S{i}-")
        for event in data["script"]:
            event["turn"] = event["turn"].replace(old + "-", f"S{i}-")
    last = data["sessions"][-1]["id"]
    data["questions"] = [{"id": "asof-S2", "after": last, "kind": "as_of", "session": "S2", "item": "model.main",
                          "text": "What were we using at the end of the second meeting?"}]
    scenario = Scenario.model_validate(data)
    for name in ("oracle", "latest-candidate", "pipeline-gold"):
        rows, _ = run_scenario(REGISTRY[name], scenario)
        assert rows[0].outcome == "correct", name
