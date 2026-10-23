"""Captured declaration failures and their downstream state effects, without APIs.

Scripted gold replies exercise Resolver wiring, legal targets, provenance and
historical reads. They do not test whether a live model recognises the speech act.
The captured wrong replies remain structurally legal; no keyword auto-fix is added.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest

from support import pilot_timeline
from tracemem.ops import OpLog
from tracemem.resolver import (
    INTENT_GUIDE, TRANSITION_EVIDENCE_GUIDE, LLMResolver, ModelReply, ResolverConfig,
)
from tracemem.schema import Answer, Candidate
from tracemem.systems.comparison import ANSWER_PROMPT, SharedAnswerer, answer_context
from tracemem.systems.no_versions import CurrentOnlyStore


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "explicit_decision_failures.json").read_text(encoding="utf-8")
)
CAPTURES = FIXTURE["resolver_captures"]
STORES = {"tracemem-controlled": OpLog, "tracemem-no-versions": CurrentOnlyStore}
CONFIG = ResolverConfig(model="offline-explicit-decision", max_attempts=2)
DECISION_FIELDS = {"op", "add_as", "targets", "source_turn_ids", "reason", "rationale"}


class ScriptedClient:
    def __init__(self, decision):
        self.decision = decision
        self.calls = []

    def complete(self, **request):
        self.calls.append(copy.deepcopy(request))
        return ModelReply(content=json.dumps(self.decision))


def captures(system, item):
    return [case for case in CAPTURES if case["system"] == system and case["request"]["candidate"]["item"] == item]


def resolve_capture(store, case, *, corrected=False):
    candidate = Candidate.model_validate(case["request"]["candidate"])
    observation = case["observation"]
    store.observe_turn(observation["turn_id"], datetime.fromisoformat(observation["when"]), observation["speaker"])
    records = store.records(candidate.item)
    before = [record.model_dump() for record in records]
    if corrected:
        gold = pilot_timeline(case["scenario_id"]).gold_op_for(candidate.candidate_id)
        decision = gold.model_dump(include=DECISION_FIELDS)
        decision["rationale"] = "Scripted development replay decision; not a model prediction."
    else:
        decision = case["observed_decision"]
    client = ScriptedClient(decision)
    resolver = LLMResolver(CONFIG, client)

    operation = resolver.resolve(candidate, records)

    assert len(client.calls) == resolver.usage().calls == 1
    request = client.calls[0]
    assert request["config"] == CONFIG
    assert len(request["messages"]) == 2
    prompt = request["messages"][0]["content"]
    assert INTENT_GUIDE in prompt and TRANSITION_EVIDENCE_GUIDE in prompt
    assert prompt.index(INTENT_GUIDE) < prompt.index("target_constraints lists")
    payload = json.loads(request["messages"][1]["content"])
    # Replay labels, gold outcomes and test expectations never become model evidence.
    assert set(payload) == {"candidate", "related", "target_constraints"}
    assert payload["candidate"] == candidate.model_dump(mode="json")
    assert payload["related"] == [record.model_dump(mode="json") for record in records]
    if not corrected:
        assert payload == case["request"]
    schema = request["response_format"]["json_schema"]["schema"]
    assert set(schema["properties"]) == set(schema["required"]) == DECISION_FIELDS
    assert [record.model_dump() for record in store.records(candidate.item)] == before
    for field, value in decision.items():
        assert getattr(operation, field) == value
    assert operation.candidate_id == candidate.candidate_id
    store.apply(operation)
    return operation


def baseline_chain(store_type, *, corrected):
    system = next(name for name, cls in STORES.items() if cls is store_type)
    cases = captures(system, "model.baseline")
    store = store_type(cases[0]["request"]["candidate"]["project_id"])
    for case in cases:
        resolve_capture(store, case, corrected=corrected)
    return store


def test_captures_preserve_dev_evidence_and_identical_requests_with_different_live_decisions():
    assert FIXTURE["provenance"]["split"] == "dev"
    assert len(CAPTURES) == 10
    for case in CAPTURES:
        candidate = case["request"]["candidate"]
        timeline = pilot_timeline(case["scenario_id"])
        expected = next(c for c in timeline.candidates_by_turn[case["observation"]["turn_id"]]
                        if c.candidate_id == candidate["candidate_id"])
        assert candidate == expected.model_dump(mode="json")
        assert case["observation"]["when"] == timeline.turn_times[case["observation"]["turn_id"]].isoformat()
    trace = captures("tracemem-controlled", "model.baseline")[0]
    no_versions = captures("tracemem-no-versions", "model.baseline")[0]
    assert trace["request"] == no_versions["request"]
    assert trace["request_hash"] == no_versions["request_hash"]
    assert trace["observed_decision"]["add_as"] == "proposed"
    assert no_versions["observed_decision"]["add_as"] == "active"


@pytest.mark.parametrize("system", STORES)
def test_captured_spacy_declaration_error_and_scripted_correction_reach_answer_context(system):
    case = captures(system, "model.ner")[0]
    item = case["request"]["candidate"]["item"]
    store_type = STORES[system]
    wrong = store_type(case["request"]["candidate"]["project_id"])
    resolve_capture(wrong, case)
    assert wrong.item_state(item).active is None
    assert [(record.value, record.status) for record in wrong.records()] == [("spaCy", "proposed")]
    assert "model.ner = spaCy [proposed]" in answer_context(wrong.records(), 12000)[0]

    corrected = store_type(case["request"]["candidate"]["project_id"])
    operation = resolve_capture(corrected, case, corrected=True)
    assert (operation.op, operation.add_as, operation.targets) == ("ADD", "active", [])
    state = corrected.item_state(item)
    assert state.active.value == "spaCy"
    assert state.active.source_turn_ids == ["S2-T5"]  # "for the NER part we'll use a spaCy model"
    assert not state.proposed and not state.history and not state.flagged
    assert "model.ner = spaCy [active]" in answer_context(corrected.records(), 12000)[0]
    assert corrected.records() == pilot_timeline("pilot-01").log_after_session["S2"].records(item)


@pytest.mark.parametrize("system", STORES)
def test_captured_baseline_chain_preserves_upstream_failure_instead_of_rewriting_history(system):
    store = baseline_chain(STORES[system], corrected=False)
    state = store.item_state("model.baseline")
    assert state.active.value == "linear SVM"
    assert state.active.source_turn_ids == ["S3-T1", "S3-T2"]  # SVM adoption, then "OK, SVM it is."
    assert store.ops[-1].op == "KEEP"
    if system == "tracemem-controlled":
        # With no prior active value, the captured SVM ADD-active is legal. It
        # cannot invent a replacement link or retrospectively adopt a proposal.
        assert [(op.op, op.add_as) for op in store.ops] == [
            ("ADD", "proposed"), ("ADD", "proposed"), ("ADD", "active"), ("KEEP", None),
        ]
        assert state.previous_active is None and not state.history
        assert state.active.supersedes == []
        assert [(record.value, record.status) for record in state.proposed] == [
            ("logistic regression", "proposed"), ("naive Bayes", "proposed"),
        ]
        assert store.upto("S1-T1").item_state("model.baseline").active is None
    else:
        assert [op.op for op in store.ops] == ["ADD", "ADD", "SUPERSEDE", "KEEP"]
        assert [record.value for record in state.proposed] == ["naive Bayes"]


@pytest.mark.parametrize("store_type", [OpLog, CurrentOnlyStore], ids=["versioned", "current-only"])
def test_scripted_declaration_suggestion_replacement_and_keep_match_development_replay(store_type):
    system = next(name for name, cls in STORES.items() if cls is store_type)
    cases = captures(system, "model.baseline")
    store = store_type("spam-filter")
    prior_active = None
    for index, case in enumerate(cases):
        operation = resolve_capture(store, case, corrected=True)
        state = store.item_state("model.baseline")
        assert not state.flagged
        if index == 0:
            assert (operation.op, operation.add_as, operation.targets) == ("ADD", "active", [])
            assert state.active.value == "logistic regression"
            prior_active = state.active.model_dump()
        elif index == 1:
            assert operation.op == "ADD" and operation.add_as == "proposed" and operation.targets == []
            assert state.active.model_dump() == prior_active
            assert [record.value for record in state.proposed] == ["naive Bayes"]
        elif index == 2:
            assert operation.op == "SUPERSEDE"
            assert operation.targets == ["model.baseline@S1-T1"]  # "Let's make the baseline logistic regression"
            assert operation.source_turn_ids == ["S3-T1"]  # "Let's make the SVM our baseline"
            assert state.active.value == "linear SVM"
            assert [record.value for record in state.proposed] == ["naive Bayes"]
        else:
            assert operation.op == "KEEP" and operation.targets == ["model.baseline@S3-T1"]
            assert state.active.record_id == "model.baseline@S3-T1"
            assert state.active.source_turn_ids == ["S3-T1", "S3-T2"]
            assert state.creating_turns[state.active.record_id] == ["S3-T1"]
            assert state.kept_turns[state.active.record_id] == ["S3-T2"]

    expected = pilot_timeline("pilot-05").log_after_session["S3"].records("model.baseline")
    if store_type is CurrentOnlyStore:
        expected = [record.model_copy(update={"supersedes": []}) for record in expected
                    if record.status in {"active", "proposed", "contested"}]
    assert store.records() == expected
    if store_type is OpLog:
        assert state.previous_active.value == "logistic regression"
        assert state.previous_active.status == "superseded"
        assert state.active.supersedes == [state.previous_active.record_id]
        assert [record.value for record in state.history] == ["logistic regression"]
        assert state.previous_active.source_turn_ids == ["S1-T1"]
        assert store.upto("S1-T1").item_state("model.baseline").active.value == "logistic regression"
        assert store.upto("S1-T2").item_state("model.baseline").active.value == "logistic regression"
        before_keep = store.upto("S3-T1").item_state("model.baseline")
        assert before_keep.active.value == "linear SVM"
        assert before_keep.active.source_turn_ids == ["S3-T1"]
        assert before_keep.previous_active.value == "logistic regression"
    else:
        assert state.history == [] and state.previous_active is None
        context, sources = answer_context(store.records(), 12000)
        assert "logistic regression" not in context and "S1-T1" not in sources
        assert state.active.supersedes == []


def test_scripted_previous_answer_receives_superseded_decision_not_a_proposal_as_history():
    store = baseline_chain(OpLog, corrected=True)
    timeline = pilot_timeline("pilot-05")
    question = next(question for question in timeline.questions if question.kind == "previous")
    expected = timeline.expected[question.question_id]
    client = ScriptedClient({
        "status": expected.expected_status, "value": expected.expected_value,
        "cited_turn_ids": expected.required_support, "text": "Scripted answer from development replay.",
    })

    answer = SharedAnswerer(CONFIG, client).answer(question.for_system(timeline.salt), store.records(), {})

    assert len(client.calls) == answer.usage.calls == 1
    request = client.calls[0]
    assert request["messages"][0] == {"role": "system", "content": ANSWER_PROMPT}
    payload = json.loads(request["messages"][1]["content"])
    assert set(payload) == {"question", "context", "allowed_source_turn_ids"}
    context, sources = answer_context(store.records(), 12000)
    assert payload["context"] == context
    assert payload["allowed_source_turn_ids"] == sources
    assert "logistic regression [superseded]" in context
    assert "naive Bayes [proposed]" in context
    assert "linear SVM [active]" in context
    assert answer.value == expected.expected_value == "logistic regression"
    assert answer.cited_turn_ids == ["S1-T1", "S3-T1"]
    assert "S1-T2" not in answer.cited_turn_ids  # "What if we used naive Bayes instead?"


def test_captured_reader_errors_remain_distinct_from_scripted_state_restoration():
    for case in FIXTURE["reader_captures"]:
        observed = Answer.model_validate(case["observed_answer"])
        expected = pilot_timeline(case["scenario_id"]).expected[case["question_id"]]
        assert (observed.status, observed.value) != (expected.expected_status, expected.expected_value)
        context = case["request"]["context"]
        if case["request"]["question"]["kind"] == "previous":
            assert observed.value == "naive Bayes"
            assert "logistic regression [proposed]" in context
            assert "naive Bayes [proposed]" in context
            assert "logistic regression [superseded]" not in context
        else:
            assert observed.status == "none"
            assert "model.ner = spaCy [proposed]" in context
