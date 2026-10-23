"""Replay task reopening failures without claiming to test live model semantics.

Both captured failures are structurally valid. Scripted corrected replies check
prompt wiring and the state/answer contract, not a model's ability to choose them.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest

from tracemem.ops import OpLog
from tracemem.resolver import (
    INTENT_GUIDE, TRANSITION_EVIDENCE_GUIDE, LLMResolver, ModelReply, ResolverConfig,
)
from tracemem.schema import Candidate, Record, SystemQuestion, Turn
from tracemem.systems.comparison import ANSWER_PROMPT, ANSWER_STATE_GUIDE, SharedAnswerer, answer_context
from tracemem.systems.no_versions import CurrentOnlyStore


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "task_reopening_failures.json").read_text(encoding="utf-8")
)
RESOLVER_CASE = FIXTURE["resolver_failure"]
ANSWER_CASE = FIXTURE["answer_failure"]
STEPS = FIXTURE["lifecycle"]
ITEM = RESOLVER_CASE["candidate"]["item"]
PROJECT = RESOLVER_CASE["candidate"]["project_id"]
CONFIG = ResolverConfig(model="offline-task-reopening", max_attempts=2)
DECISION_FIELDS = {"op", "add_as", "targets", "source_turn_ids", "reason", "rationale"}
ANSWER_FIELDS = {"status", "value", "cited_turn_ids", "text"}


class ScriptedClient:
    def __init__(self, decision: dict):
        self.decision = decision
        self.calls: list[dict] = []

    def complete(self, **request):
        self.calls.append(copy.deepcopy(request))
        return ModelReply(content=json.dumps(self.decision))


def observe(store, step):
    observation = step["observation"]
    store.observe_turn(
        observation["turn_id"], datetime.fromisoformat(observation["when"]), observation["speaker"]
    )


def resolve(store, step, decision=None):
    candidate = Candidate.model_validate(step["candidate"])
    observe(store, step)
    records = store.records(candidate.item)
    before = [record.model_dump() for record in records]
    client = ScriptedClient(step["decision"] if decision is None else decision)
    resolver = LLMResolver(CONFIG, client)

    operation = resolver.resolve(candidate, records)

    assert len(client.calls) == resolver.usage().calls == 1
    request = client.calls[0]
    assert request["config"] == CONFIG
    assert len(request["messages"]) == 2
    prompt = request["messages"][0]["content"]
    assert INTENT_GUIDE in prompt
    assert TRANSITION_EVIDENCE_GUIDE in prompt
    assert prompt.index(INTENT_GUIDE) < prompt.index("target_constraints lists")
    payload = json.loads(request["messages"][1]["content"])
    # The script and desired outcomes are not supplied as model evidence.
    assert set(payload) == {"candidate", "related", "target_constraints"}
    assert payload["candidate"] == candidate.model_dump(mode="json")
    assert payload["related"] == [record.model_dump(mode="json") for record in records]
    schema = request["response_format"]["json_schema"]["schema"]
    assert set(schema["properties"]) == set(schema["required"]) == DECISION_FIELDS
    assert [record.model_dump() for record in store.records(candidate.item)] == before
    for key, value in client.decision.items():
        assert getattr(operation, key) == value
    return operation


def cancelled_store(store_type=OpLog):
    store = store_type(PROJECT)
    for step in STEPS[:2]:
        store.apply(resolve(store, step))
    return store


def answer_scripted(records, decision, expected_payload=None):
    question = SystemQuestion(
        question_id="opaque-question", scenario_id="opaque-scenario", **ANSWER_CASE["request"]["question"]
    )
    client = ScriptedClient(decision)
    answerer = SharedAnswerer(CONFIG, client)
    # Raw dialogue must not leak back into the shared comparison reader.
    raw_turns = {
        "S3-T2": Turn(id="S3-T2", speaker="Ana", text="RAW_DIALOGUE_NOT_FOR_ANSWER_CONTEXT"),
    }

    answer = answerer.answer(question, records, raw_turns)

    assert len(client.calls) == answerer.usage().calls == answer.usage.calls == 1
    request = client.calls[0]
    assert request["config"] == CONFIG
    assert request["messages"][0] == {"role": "system", "content": ANSWER_PROMPT}
    assert ANSWER_STATE_GUIDE in request["messages"][0]["content"]
    assert len(request["messages"]) == 2
    payload = json.loads(request["messages"][1]["content"])
    context, sources = answer_context(records, 12000)
    assert payload == {
        "question": ANSWER_CASE["request"]["question"],
        "context": context,
        "allowed_source_turn_ids": sources,
    }
    assert "RAW_DIALOGUE_NOT_FOR_ANSWER_CONTEXT" not in request["messages"][1]["content"]
    if expected_payload is not None:
        assert payload == expected_payload
    schema = request["response_format"]["json_schema"]["schema"]
    assert set(schema["properties"]) == set(schema["required"]) == ANSWER_FIELDS
    assert answer.context_turn_ids == sources
    for key, value in decision.items():
        assert getattr(answer, key) == value
    return answer


def test_captured_wrong_reopening_remains_structurally_valid_with_real_prior_versions():
    store = cancelled_store()
    assert [record.model_dump(mode="json") for record in store.records()] == RESOLVER_CASE["related"]

    operation = resolve(store, STEPS[2], RESOLVER_CASE["observed_decision"])
    store.apply(operation)

    # This is the captured semantic error, not a validation failure or an auto-fix.
    state = store.item_state(ITEM)
    assert state.active.value == "open"
    assert state.active.record_id == STEPS[2]["candidate"]["candidate_id"]
    assert state.previous_active.value == "cancelled"
    assert not state.proposed


@pytest.mark.parametrize("store_type", [OpLog, CurrentOnlyStore], ids=["versioned", "current-only"])
def test_scripted_reopening_proposal_preserves_cancellation_and_its_sources(store_type):
    store = cancelled_store(store_type)
    active_before = store.item_state(ITEM).active.model_dump()
    history_before = [record.model_dump() for record in store.item_state(ITEM).history]

    store.apply(resolve(store, STEPS[2], RESOLVER_CASE["corrected_decision"]))

    state = store.item_state(ITEM)
    assert state.active.model_dump() == active_before
    assert [record.model_dump() for record in state.history] == history_before
    assert [(record.value, record.status, record.source_turn_ids) for record in state.proposed] == [
        ("open", "proposed", ["S4-T2"])
    ]
    assert not state.flagged and not state.contested
    result = answer_scripted(store.records(), ANSWER_CASE["corrected_decision"])
    assert (result.status, result.value) == ("answer", "cancelled")
    assert result.cited_turn_ids == ["S3-T2"]


@pytest.mark.parametrize("reply_key", ["observed_decision", "corrected_decision"])
def test_captured_answer_failure_and_scripted_correction_use_identical_visible_evidence(reply_key):
    records = [Record.model_validate(raw) for raw in ANSWER_CASE["records"]]
    assert FIXTURE["provenance"]["split"] == "dev"
    assert not any(record.status == "contested" for record in records)
    assert [(record.value, record.status) for record in records if record.item == ITEM] == [
        ("cancelled", "active"), ("open", "proposed")
    ]

    answer = answer_scripted(records, ANSWER_CASE[reply_key], ANSWER_CASE["request"])

    # The original conflict is still accepted by structural validation; the
    # instruction update must be evaluated separately with an actual model.
    if reply_key == "observed_decision":
        assert answer.status == "conflict" and answer.value is None
    else:
        assert answer.status == "answer" and answer.value == "cancelled"
        assert "[active]" not in answer.value


@pytest.mark.parametrize("store_type", [OpLog, CurrentOnlyStore], ids=["versioned", "current-only"])
def test_scripted_commit_cancel_suggest_and_explicit_acceptance_lifecycle(store_type):
    store = store_type(PROJECT)
    for step, expected in zip(STEPS, ["open", "cancelled", "cancelled", "open"], strict=True):
        store.apply(resolve(store, step))
        assert store.item_state(ITEM).active.value == expected
        assert not store.item_state(ITEM).flagged

    state = store.item_state(ITEM)
    assert not state.proposed and not state.contested
    assert state.active.created_turn == "S5-T1"
    assert state.active.source_turn_ids == ["S5-T1", "S4-T2"]
    assert [operation.op for operation in store.ops] == ["ADD", "SUPERSEDE", "ADD", "SUPERSEDE"]
    if store_type is OpLog:
        assert state.previous_active.record_id == "task.error_analysis@S3-T2"
        assert state.previous_active.value == "cancelled"
        assert [(record.value, record.status) for record in state.history] == [
            ("open", "superseded"), ("cancelled", "superseded"), ("open", "superseded")
        ]
        assert state.active.supersedes == ["task.error_analysis@S3-T2", "task.error_analysis@S4-T2"]
        # A proposal must not retrospectively rewrite the cancellation or origin.
        assert store.upto("S1-T3").item_state(ITEM).active.value == "open"
        assert store.upto("S3-T2").item_state(ITEM).active.value == "cancelled"
        assert store.upto("S4-T2").item_state(ITEM).active.value == "cancelled"
    else:
        assert state.history == [] and state.previous_active is None
        assert state.active.supersedes == []
        assert [record.record_id for record in store.records()] == ["task.error_analysis@S5-T1"]
        context, sources = answer_context(store.records(), 12000)
        assert "cancelled" not in context and "S1-T3" not in sources and "S3-T2" not in sources
    answer = answer_scripted(store.records(), {
        # The accepted reopening has two evidence roles: the suggestion at
        # S4-T2 and its formal adoption at S5-T1, not the original open task.
        "status": "answer", "value": "open", "cited_turn_ids": ["S4-T2", "S5-T1"],
        "text": "The task was explicitly reopened after the proposal was accepted.",
    })
    assert answer.value == "open"
    assert answer.cited_turn_ids == ["S4-T2", "S5-T1"]
