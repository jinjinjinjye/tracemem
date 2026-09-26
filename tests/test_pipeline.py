"""TraceMem's pipeline (pipeline.py) wired from the gold stand-ins (components.py).

With every component replaced by its gold stand-in, the pipeline must score
exactly like the oracle. That is what lets each teammate swap in one real
component and attribute any drop in score to it.
"""

from __future__ import annotations

import pytest

import json

from support import PILOT_IDS, minimal_dict, pilot, pilot_timeline, run_on_pilots
from tracemem.components import (
    GoldExtractor,
    GoldMatcher,
    GoldResolver,
    GoldRetriever,
    RuleAnswerer,
    render_records,
)
from tracemem.eval.harness import CONDITIONS, run, run_scenario, write_run
from tracemem.pipeline import TraceMemPipeline
from tracemem.schema import Operation, Scenario, Turn
from tracemem.systems import REGISTRY
from tracemem.systems.base import SystemSpec


def outcomes(rows) -> dict:
    return {(r.scenario_id, r.question.question_id): r.outcome for r in rows}


@pytest.mark.parametrize("condition", CONDITIONS)
def test_gold_pipeline_matches_the_oracle_on_every_question(condition):
    """Same outcome as the oracle on every pilot question, in both conditions (all of them 'correct')."""
    oracle = outcomes(run_on_pilots(REGISTRY["oracle"]))
    pipeline = outcomes(run_on_pilots(REGISTRY["pipeline-gold"], condition=condition))
    assert pipeline == oracle
    assert set(pipeline.values()) == {"correct"}


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_gold_pipeline_issues_the_gold_operations(scenario_id):
    """Its operation log is exactly the replay's gold operations, in order, with nothing rejected."""
    timeline = pilot_timeline(scenario_id)
    _, system = run_scenario(REGISTRY["pipeline-gold"], pilot(scenario_id), timeline)
    gold_ops = [op for turn in timeline.turn_order for op in timeline.ops_by_turn[turn]]
    assert system.operations() == gold_ops
    assert system.rejected_operations() == []
    assert system.candidates() == [c for turn in timeline.turn_order for c in timeline.candidates_by_turn[turn]]


class SpyAnswerer(RuleAnswerer):
    """RuleAnswerer that records what it was given."""

    def __init__(self):
        self.calls = []

    def answer(self, question, records, turns):
        self.calls.append((question, list(records), dict(turns)))
        return super().answer(question, records, turns)


def build(gold, resolver=None, answerer=None):
    meta = gold.scenario.meta()
    return TraceMemPipeline(meta, GoldExtractor(gold), GoldMatcher(), resolver or GoldResolver(gold),
                            GoldRetriever(gold), answerer or RuleAnswerer(), name="pipeline-test")


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_answerer_sees_only_turns_cited_by_the_retrieved_records(scenario_id):
    """The answer step gets the retrieved records plus only the turns those records cite, not the conversation."""
    spy = SpyAnswerer()
    spec = SystemSpec("pipeline-test", lambda meta, gold: build(gold, answerer=spy), True, "test")
    scenario = pilot(scenario_id)
    run_scenario(spec, scenario, pilot_timeline(scenario_id))
    assert spy.calls
    all_turns = {t.id: t for t in scenario.turns()}
    for question, records, turns in spy.calls:
        cited = {t for record in records for t in record.source_turn_ids}
        assert set(turns) == cited
        for turn_id, turn in turns.items():
            assert isinstance(turn, Turn) and turn == all_turns[turn_id]
    assert any(len(turns) < len(all_turns) for _, _, turns in spy.calls)


class SabotagedResolver(GoldResolver):
    """Gold operations, except one invalid KEEP (a value that differs from the active one) at pilot-01 S4-T1."""

    def resolve(self, candidate, related):
        op = super().resolve(candidate, related)
        if op.turn_id == "S4-T1" and op.item == "model.sentiment":
            return op.model_copy(update={"value": "RoBERTa", "op_id": "sabotaged"})
        return op


def test_an_invalid_operation_is_rejected_without_crashing_the_run():
    """The run completes, the bad operation is kept in rejected_operations() with the reason, and nothing else changes."""
    timeline = pilot_timeline("pilot-01")
    spec = SystemSpec("pipeline-test", lambda meta, gold: build(gold, resolver=SabotagedResolver(gold)), True, "test")
    rows, system = run_scenario(spec, pilot("pilot-01"), timeline)
    assert len(rows) == len(timeline.questions)
    ((rejected, reason),) = system.rejected_operations()
    assert isinstance(rejected, Operation) and rejected.op_id == "sabotaged"
    assert "KEEP value differs" in reason
    gold_ops = [op for turn in timeline.turn_order for op in timeline.ops_by_turn[turn]]
    assert system.operations() == [op for op in gold_ops if op.candidate_id != rejected.candidate_id]
    # The KEEP only added support, so every answer is still right; only the support on S4 is thinner.
    assert {r.outcome for r in rows} == {"correct"}
    s4 = next(r for r in rows if r.question.question_id == "model.sentiment@S4")
    assert "S4-T1" not in s4.answer.cited_turn_ids


def test_rejections_that_cascade_are_all_kept():
    """If an early operation is rejected, later ones that depend on it are rejected too, and the run still ends."""

    class DropSuggestion(GoldResolver):
        def resolve(self, candidate, related):
            op = super().resolve(candidate, related)
            if op.turn_id == "S2-T3":  # the DistilBERT suggestion becomes an invalid FLAG with no target
                return op.model_copy(update={"op": "FLAG", "add_as": None, "targets": []})
            return op

    timeline = pilot_timeline("pilot-01")
    spec = SystemSpec("pipeline-test", lambda meta, gold: build(gold, resolver=DropSuggestion(gold)), True, "test")
    rows, system = run_scenario(spec, pilot("pilot-01"), timeline)
    assert len(rows) == len(timeline.questions)
    rejected_turns = [op.turn_id for op, _ in system.rejected_operations()]
    assert rejected_turns[0] == "S2-T3"
    assert "S3-T2" in rejected_turns  # the revision named the missing proposal as a target
    assert system.log.item_state("model.sentiment").active.value == "BERT"


def test_pipeline_describes_its_components():
    system = build(pilot_timeline("pilot-01"))
    assert system.describe() == {"extractor": "GoldExtractor", "matcher": "GoldMatcher", "resolver": "GoldResolver",
                                 "retriever": "GoldRetriever", "answerer": "RuleAnswerer", "budget_tokens": 2000}


def test_rejected_operations_are_saved_with_the_run(tmp_path):
    """The harness collects rejected operations per scenario and write_run saves them with their reasons."""
    spec = SystemSpec("pipeline-test", lambda meta, gold: build(gold, resolver=SabotagedResolver(gold)), True, "test")
    result = run(spec, [pilot("pilot-01")], "dev")
    ((op, reason),) = result.rejected["pilot-01"]
    assert op.op_id == "sabotaged"
    folder = write_run(result, tmp_path)
    (line,) = (folder / "rejected_ops.jsonl").read_text(encoding="utf-8").splitlines()
    saved = json.loads(line)
    assert (saved["scenario_id"], saved["op_id"], saved["op"]) == ("pilot-01", "sabotaged", "KEEP")


def test_saved_rejection_keeps_the_rejection_message(tmp_path):
    spec = SystemSpec("pipeline-test", lambda meta, gold: build(gold, resolver=SabotagedResolver(gold)), True, "test")
    folder = write_run(run(spec, [pilot("pilot-01")], "dev"), tmp_path)
    line = (folder / "rejected_ops.jsonl").read_text(encoding="utf-8")
    assert "KEEP value differs" in line


def test_render_records_orders_by_time_and_shows_status_only_when_asked():
    """The shared renderer lists records oldest first, quoting each record's turn; status is optional."""
    timeline = pilot_timeline("pilot-01")
    log = timeline.log_after_session["S3"]
    records = list(reversed(log.records("model.sentiment")))
    turns = {t.id: t for t in pilot("pilot-01").turns()}
    with_status = render_records(records, turns, show_status=True).splitlines()
    assert [line.split()[0] for line in with_status] == ["S1-T1", "S2-T3", "S3-T2"]
    assert with_status[0].startswith("S1-T1 Mei: model.sentiment = BERT [superseded] \"Let's go with BERT")
    assert "[active]" in with_status[2]
    assert "[" not in render_records(records, turns, show_status=False)


def _same_day_scenario(same_day: bool) -> Scenario:
    """minimal.yaml plus an 'as of S1' question; optionally with both meetings on the same date."""
    data = minimal_dict()
    if same_day:
        data["sessions"][1]["date"] = data["sessions"][0]["date"]
    data["questions"].append({"id": "asof-S1", "after": "S2", "kind": "as_of", "session": "S1", "item": "model.main",
                              "text": "What were we training at the end of the first meeting?"})
    return Scenario.model_validate(data)


def _as_of_outcomes(scenario: Scenario) -> dict:
    return {name: next(r.outcome for r in run_scenario(REGISTRY[name], scenario)[0]
                       if r.question.question_id == "asof-S1")
            for name in ("oracle", "pipeline-gold")}


def test_gold_pipeline_answers_as_of_questions_when_meetings_are_on_different_days():
    """Control for the next test: with distinct dates, both answer 'BERT' as of S1."""
    assert _as_of_outcomes(_same_day_scenario(False)) == {"oracle": "correct", "pipeline-gold": "correct"}


def test_gold_pipeline_answers_as_of_questions_when_two_meetings_share_a_date():
    """The validator allows two sessions on the same date (only backwards dates are errors)."""
    assert _as_of_outcomes(_same_day_scenario(True)) == {"oracle": "correct", "pipeline-gold": "correct"}
