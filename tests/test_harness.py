"""The harness's four fairness rules (eval/harness.py docstring), checked with spy systems.

1. every scenario gets a new system instance;
2. turns arrive in order, and a question is asked only after the last turn of its session;
3. a question never reaches observe(), and answering must not change memory;
4. gold labels reach only systems registered with uses_gold, and gold candidates only
   systems that accept them, only in the gold-candidate condition.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from support import PILOT_IDS, pilot, pilot_timeline
from tracemem.bench.replay import GoldTimeline
from tracemem.eval import harness
from tracemem.eval.harness import AnswerMutatedState, run, run_scenario, write_run
from tracemem.schema import Answer, Candidate, ScenarioMeta, SystemQuestion, Turn, session_of
from tracemem.systems.base import SystemSpec


class Spy:
    """Records everything the harness gives it and always abstains."""

    name = "spy"

    def __init__(self, meta: ScenarioMeta, gold: GoldTimeline | None):
        self.meta, self.gold = meta, gold
        self.observed: list[Turn] = []
        self.observe_calls: list[tuple] = []
        self.asked: list[tuple[SystemQuestion, tuple[str, ...]]] = []

    def observe(self, turn, when, gold_candidates=None):
        self.observed.append(turn)
        self.observe_calls.append((turn, when, gold_candidates))

    def answer(self, question):
        self.asked.append((question, tuple(t.id for t in self.observed)))
        return Answer(status="abstain")

    def fingerprint(self) -> str:
        return str(len(self.observed))


class GoldCandidateSpy(Spy):
    accepts_gold_candidates = True


def spy_spec(cls=Spy, uses_gold=False, instances=None):
    def factory(meta, gold):
        system = cls(meta, gold)
        if instances is not None:
            instances.append(system)
        return system

    return SystemSpec(cls.name, factory, uses_gold, "test spy")


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_questions_are_asked_after_their_session_and_never_see_later_turns(scenario_id):
    """At each question the spy has seen exactly the turns up to the end of the question's session: none later."""
    scenario, timeline = pilot(scenario_id), pilot_timeline(scenario_id)
    _, spy = run_scenario(spy_spec(), scenario, timeline)
    all_turns = [t.id for t in scenario.turns()]
    after_of = {timeline.public_id(q): q.after for q in timeline.questions}
    assert len(spy.asked) == len(timeline.questions)
    for question, seen in spy.asked:
        session = after_of[question.question_id]
        last = max(i for i, t in enumerate(all_turns) if session_of(t) == session)
        assert list(seen) == all_turns[: last + 1], question.question_id


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_observe_receives_only_turns_in_order(scenario_id):
    """observe() gets each scenario turn once, in order, with its synthetic time; never a question."""
    scenario, timeline = pilot(scenario_id), pilot_timeline(scenario_id)
    _, spy = run_scenario(spy_spec(), scenario, timeline)
    assert spy.observed == scenario.turns()
    question_texts = {q.text for q in timeline.questions}
    for turn, when, gold_candidates in spy.observe_calls:
        assert type(turn) is Turn
        assert turn.text not in question_texts
        assert isinstance(when, datetime) and when == timeline.turn_times[turn.id]
        assert gold_candidates is None  # end-to-end condition
    times = [when for _, when, _ in spy.observe_calls]
    assert times == sorted(times)


def test_the_question_a_system_receives_has_no_item():
    scenario, timeline = pilot("pilot-01"), pilot_timeline("pilot-01")
    _, spy = run_scenario(spy_spec(), scenario, timeline)
    items = {spec.key for spec in scenario.items}
    for question, _ in spy.asked:
        assert type(question) is SystemQuestion
        assert not hasattr(question, "item")
        assert not any(item in question.question_id for item in items)
        assert "item" not in question.model_dump()


def test_every_scenario_gets_a_new_instance():
    instances: list[Spy] = []
    scenarios = [pilot(sid) for sid in PILOT_IDS]
    run(spy_spec(instances=instances), scenarios, "dev")
    assert len(instances) == len(scenarios)
    assert len({id(s) for s in instances}) == len(scenarios)
    for system, scenario in zip(instances, scenarios):
        assert system.meta.scenario_id == scenario.scenario_id
        assert system.observed == scenario.turns()  # nothing carried over from the previous scenario


def test_meta_follows_the_vocabulary_setting():
    instances: list[Spy] = []
    run_scenario(spy_spec(instances=instances), pilot("pilot-01"), vocabulary="keys")
    run_scenario(spy_spec(instances=instances), pilot("pilot-01"), vocabulary="none")
    keys, none = instances
    assert [i.key for i in keys.meta.items] == ["model.sentiment", "metric.primary", "model.ner"]
    assert none.meta.items == [] and none.meta.vocabulary == "none"


class Mutating(Spy):
    """Changes its memory while answering, which rule 3 forbids."""

    name = "mutating"

    def answer(self, question):
        self.observed.append(Turn(id="S9-T9", speaker="?", text=question.text))
        return Answer(status="abstain")


def test_changing_memory_while_answering_raises():
    with pytest.raises(AnswerMutatedState):
        run_scenario(spy_spec(Mutating), pilot("pilot-01"), pilot_timeline("pilot-01"))


def test_a_read_only_answer_passes_the_fingerprint_check():
    rows, _ = run_scenario(spy_spec(), pilot("pilot-01"), pilot_timeline("pilot-01"))
    assert {r.outcome for r in rows} == {"abstained"}


@pytest.mark.parametrize("uses_gold", [False, True])
def test_gold_labels_reach_only_systems_that_use_gold(uses_gold):
    instances: list[Spy] = []
    run_scenario(spy_spec(uses_gold=uses_gold, instances=instances), pilot("pilot-01"))
    gold = instances[0].gold
    if uses_gold:
        assert isinstance(gold, GoldTimeline)
    else:
        assert gold is None


def test_gold_candidate_condition_refuses_a_system_that_does_not_accept_them():
    with pytest.raises(ValueError, match="gold-candidate"):
        run_scenario(spy_spec(), pilot("pilot-01"), condition="gold_candidates")


def test_gold_candidates_are_passed_only_in_their_condition():
    """In the gold-candidate condition, each turn arrives with exactly the replay's candidates for it."""
    timeline = pilot_timeline("pilot-01")
    _, spy = run_scenario(spy_spec(GoldCandidateSpy), pilot("pilot-01"), timeline, condition="gold_candidates")
    for turn, _, candidates in spy.observe_calls:
        assert candidates == timeline.candidates_by_turn[turn.id]
        assert all(isinstance(c, Candidate) for c in candidates)
    _, spy = run_scenario(spy_spec(GoldCandidateSpy), pilot("pilot-01"), timeline)
    assert all(candidates is None for _, _, candidates in spy.observe_calls)


def test_unknown_condition_is_rejected():
    with pytest.raises(ValueError, match="unknown condition"):
        run_scenario(spy_spec(), pilot("pilot-01"), condition="oracle_mode")


def test_rows_record_what_was_visible_and_the_category():
    rows, _ = run_scenario(spy_spec(), pilot("pilot-01"), pilot_timeline("pilot-01"))
    row = next(r for r in rows if r.question.question_id == "model.sentiment@S2")
    assert row.visible_turns == {t.id for t in pilot("pilot-01").turns() if session_of(t.id) in ("S1", "S2")}
    assert row.category == "suggestion_after_decision"


def test_write_run_saves_answers_metrics_and_manifest(tmp_path):
    from tracemem.eval.report import load_run
    from tracemem.systems import REGISTRY

    result = run(REGISTRY["pipeline-gold"], [pilot("pilot-01")], "dev")
    folder = write_run(result, tmp_path, extra_manifest={"note": "test"})
    assert {p.name for p in folder.iterdir()} == {"manifest.json", "answers.jsonl", "ops.jsonl", "candidates.jsonl",
                                                  "metrics.json"}
    manifest, rows = load_run(folder)
    assert manifest["system"] == "pipeline-gold" and manifest["uses_gold_labels"] is True
    assert manifest["note"] == "test"
    assert [r.outcome for r in rows] == [r.outcome for r in result.rows]
    assert result.system_config["answerer"] == "RuleAnswerer"


class _FrozenClock(datetime):
    """datetime whose now() is fixed, to make two runs land in the same second deterministically."""

    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 9, 26, 12, 0, 0, tzinfo=timezone.utc)


def test_two_runs_in_the_same_second_are_both_saved(tmp_path, monkeypatch):
    from tracemem.systems import REGISTRY

    monkeypatch.setattr(harness, "datetime", _FrozenClock)
    keys = run(REGISTRY["oracle"], [pilot("pilot-01")], "dev", vocabulary="keys")
    none = run(REGISTRY["oracle"], [pilot("pilot-01")], "dev", vocabulary="none")
    assert write_run(keys, tmp_path) != write_run(none, tmp_path)
