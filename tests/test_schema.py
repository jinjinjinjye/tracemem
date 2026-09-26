"""The data contracts in schema.py: what they accept, what they reject, and what they hide from systems."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from support import FIXTURES, MINIMAL, PILOT_IDS, minimal_dict, pilot, pilot_path, pilot_timeline
from tracemem.bench.load import load_scenario
from tracemem.schema import (
    Answer,
    ItemSpec,
    Question,
    Scenario,
    ScenarioMeta,
    ScriptEvent,
    SystemQuestion,
    Turn,
    normalise,
    public_question_id,
)

# -- loading -------------------------------------------------------------------------


def test_valid_fixtures_load():
    """Every fixture not named broken-* loads as a Scenario."""
    valid = [p for p in sorted(FIXTURES.glob("*.yaml")) if not p.name.startswith("broken-")]
    assert MINIMAL in valid
    for path in valid:
        assert isinstance(load_scenario(path), Scenario)


def test_broken_fixtures_do_not_load():
    """Every fixture named broken-* is rejected by the schema."""
    broken = sorted(FIXTURES.glob("broken-*.yaml"))
    assert broken, "expected at least one broken fixture"
    for path in broken:
        with pytest.raises(ValidationError):
            load_scenario(path)


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_pilots_load(scenario_id):
    """Each pilot file loads, and its scenario_id matches its file name."""
    scenario = pilot(scenario_id)
    assert scenario.scenario_id == scenario_id
    assert pilot_path(scenario_id).name.startswith(scenario_id)


# -- unknown and misspelt fields -----------------------------------------------------


def test_misspelt_top_level_field_is_rejected():
    """A misspelt field ("titel") is an error, not a silently ignored value."""
    data = minimal_dict()
    data["titel"] = data.pop("title")
    with pytest.raises(ValidationError, match="titel"):
        Scenario.model_validate(data)


@pytest.mark.parametrize("model, fields", [
    (Turn, {"id": "S1-T1", "speaker": "Ana", "text": "hi", "speeker": "Ana"}),
    (ScriptEvent, {"turn": "S1-T1", "act": "decide", "item": "model.x", "vaule": "BERT"}),
    (ItemSpec, {"key": "model.x", "kind": "decision", "description": "d", "value": {"BERT": []}}),
    (Answer, {"status": "none", "confidence": 0.9}),
])
def test_extra_fields_are_rejected_on_every_contract(model, fields):
    """Each contract forbids fields it does not define."""
    with pytest.raises(ValidationError):
        model.model_validate(fields)


def test_contracts_are_immutable():
    """A built contract cannot be changed in place."""
    turn = Turn(id="S1-T1", speaker="Ana", text="hi")
    with pytest.raises(ValidationError):
        turn.text = "changed"


def test_unknown_act_is_rejected():
    """Only the nine acts in the vocabulary are allowed."""
    with pytest.raises(ValidationError):
        ScriptEvent(turn="S1-T1", act="propose", item="model.x", value="BERT")


# -- identifiers -----------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["S1T1", "S0-T1", "S1-T0", "s1-t1", "S1-T", "T1", "S1-T1 "])
def test_bad_turn_ids_are_rejected(bad):
    """A turn id must look like S<n>-T<m> with n, m >= 1."""
    with pytest.raises(ValidationError):
        Turn(id=bad, speaker="Ana", text="hi")


@pytest.mark.parametrize("good", ["S1-T1", "S12-T10"])
def test_good_turn_ids_are_accepted(good):
    assert Turn(id=good, speaker="Ana", text="hi").id == good


@pytest.mark.parametrize("bad", ["model", "Model.sentiment", "model.", ".model", "model sentiment", "1model.x"])
def test_bad_item_keys_are_rejected(bad):
    """An item key is lowercase and dotted, e.g. model.sentiment."""
    with pytest.raises(ValidationError):
        ItemSpec(key=bad, kind="decision", description="d")


def test_bad_ids_inside_a_scenario_are_rejected():
    """The id patterns also apply when a whole scenario file is loaded."""
    data = minimal_dict()
    data["sessions"][0]["turns"][0]["id"] = "S1_T1"
    with pytest.raises(ValidationError):
        Scenario.model_validate(data)
    data = minimal_dict()
    data["items"][0]["key"] = "Model"
    with pytest.raises(ValidationError):
        Scenario.model_validate(data)


# -- answers ---------------------------------------------------------------------------


def test_answer_with_status_answer_needs_a_value():
    with pytest.raises(ValidationError, match="exactly when"):
        Answer(status="answer")


@pytest.mark.parametrize("status", ["none", "conflict", "abstain"])
def test_answer_without_status_answer_must_not_carry_a_value(status):
    """A value is allowed only with status 'answer', so a refusal cannot smuggle in a value."""
    with pytest.raises(ValidationError, match="exactly when"):
        Answer(status=status, value="BERT")
    assert Answer(status=status).value is None


def test_valid_answers_build():
    assert Answer(status="answer", value="BERT", cited_turn_ids=["S1-T1"]).value == "BERT"


def test_unknown_answer_status_is_rejected():
    with pytest.raises(ValidationError):
        Answer(status="maybe")


# -- what a system is allowed to see ---------------------------------------------------


def test_system_question_has_no_item_field():
    """The question a system receives never names the item it is about."""
    assert "item" not in SystemQuestion.model_fields
    with pytest.raises(ValidationError):
        SystemQuestion(question_id="q", scenario_id="s", kind="current", text="?", item="model.x")


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_system_question_id_does_not_reveal_the_item(scenario_id):
    """for_system() gives an opaque id: it contains neither the item key nor the benchmark's question id."""
    timeline = pilot_timeline(scenario_id)
    seen = set()
    for question in timeline.questions:
        public = question.for_system()
        assert isinstance(public, SystemQuestion)
        assert question.item not in public.question_id
        assert question.item.split(".")[0] not in public.question_id
        assert question.question_id not in public.question_id
        assert public.question_id == public_question_id(question.scenario_id, question.question_id)
        assert (public.kind, public.text, public.session) == (question.kind, question.text, question.session)
        assert "item" not in public.model_dump()
        seen.add(public.question_id)
    assert len(seen) == len(timeline.questions), "public ids must not collide within a scenario"


def test_public_question_id_is_stable_and_short():
    qid = public_question_id("pilot-01", "model.sentiment@S1")
    assert qid == public_question_id("pilot-01", "model.sentiment@S1")
    assert qid != public_question_id("pilot-02", "model.sentiment@S1")
    assert qid.startswith("q-") and len(qid) == 14


def test_question_for_system_drops_the_item():
    question = Question(question_id="model.main@S2", scenario_id="fixture-minimal", after="S2", kind="current",
                        item="model.main", text="Which classifier are we training?")
    assert set(question.for_system().model_dump()) == {"question_id", "scenario_id", "kind", "text", "session"}


def test_meta_with_keys_exposes_keys_and_descriptions_only():
    """meta("keys") gives each item's key, kind and description; never values, aliases, ask text or confusable labels."""
    scenario = load_scenario(MINIMAL)
    meta = scenario.meta("keys")
    assert isinstance(meta, ScenarioMeta)
    assert meta.vocabulary == "keys"
    assert [(i.key, i.kind, i.description) for i in meta.items] == [
        (s.key, s.kind, s.description) for s in scenario.items
    ]
    for info in meta.model_dump()["items"]:
        assert set(info) == {"key", "kind", "description"}
    dumped = meta.model_dump_json().lower()
    for spec in scenario.items:
        for canonical, aliases in spec.values.items():
            for form in [canonical, *aliases]:
                assert normalise(form) not in dumped, f"value spelling {form!r} leaked into the metadata"
        if spec.ask:
            assert normalise(spec.ask) not in dumped
    for field in ("values", "aliases", "confusable_with", "ask", "script", "questions"):
        assert f'"{field}"' not in dumped


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_meta_of_pilots_carries_no_values(scenario_id):
    """The same holds on every pilot: no canonical value appears in what a system sees up front."""
    scenario = pilot(scenario_id)
    dumped = scenario.meta("keys").model_dump_json().lower()
    for spec in scenario.items:
        for canonical in spec.values:
            assert canonical.lower() not in dumped, f"{canonical!r} leaked into the metadata"
        if spec.ask:
            assert spec.ask.lower() not in dumped
    assert "confusable_with" not in dumped


def test_meta_with_no_vocabulary_exposes_no_items():
    """meta("none") withholds even the item keys."""
    meta = load_scenario(MINIMAL).meta("none")
    assert meta.vocabulary == "none"
    assert meta.items == []
    assert "model.main" not in meta.model_dump_json()
    assert meta.project_id == "fixture-project"


# -- small helpers ---------------------------------------------------------------------


@pytest.mark.parametrize("raw, expected", [
    ("  BERT-Base. ", "bert-base"),
    ("Macro  F1", "macro f1"),
    ('"DistilBERT"!', "distilbert"),
    (None, ""),
])
def test_normalise(raw, expected):
    """Answers are compared after lowercasing, trimming, collapsing spaces and stripping outer punctuation."""
    assert normalise(raw) == expected
