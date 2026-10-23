"""Offline contract tests for the real Mem0 adapter (no SDK or API key needed)."""

from __future__ import annotations

import json
from datetime import datetime
from types import SimpleNamespace

import pytest

from tracemem.schema import ScenarioMeta, SystemQuestion, Turn
from tracemem.systems import REGISTRY
from tracemem.systems.mem0 import Mem0System, make_mem0


class FakeMemory:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.adds = []
        self.searches = []

    def add(self, messages, **kwargs):
        self.adds.append((messages, kwargs))
        return {"results": []}

    def search(self, query, **kwargs):
        self.searches.append((query, kwargs))
        return {"results": list(self.rows)}


class FakeCompletions:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(self.payload)))],
            usage=SimpleNamespace(prompt_tokens=27, completion_tokens=8),
        )


def system(rows=None, answer=None):
    memory = FakeMemory(rows)
    completions = FakeCompletions(answer or {"status": "answer", "value": "BERT", "cited_turn_ids": ["S1-T1"]})
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    meta = ScenarioMeta(scenario_id="pilot", project_id="proj.example")
    instance = Mem0System(meta, memory=memory, answer_client=client)
    return instance, memory, completions


def q(kind="current", session=None):
    return SystemQuestion(question_id="opaque-id", scenario_id="pilot", kind=kind,
                          text="Which model is the team using?", session=session)


def turn(turn_id, text):
    return Turn(id=turn_id, speaker="Alex", text=text)


def test_registry_system_is_not_a_gold_probe():
    assert REGISTRY["mem0"].uses_gold is False
    assert REGISTRY["mem0"].factory is make_mem0
    assert make_mem0.__name__ == "make_mem0"
    with pytest.raises(ValueError, match="gold timeline"):
        make_mem0(ScenarioMeta(scenario_id="x", project_id="p"), gold=object())


def test_observe_passes_real_turns_to_mem0_without_labels():
    instance, memory, _ = system()
    instance.observe(turn("S1-T1", "Let's use BERT."), datetime(2026, 10, 1))
    messages, kwargs = memory.adds[0]
    assert messages == [{"role": "user", "content": "Alex: Let's use BERT."}]
    assert kwargs["infer"] is True
    assert kwargs["metadata"]["source_turn_id"] == "S1-T1"
    assert kwargs["metadata"]["project_id"] == "proj.example"
    assert kwargs["user_id"] == instance.user_id
    assert "BERT" not in instance.describe()  # never writes benchmark item values to config
    with pytest.raises(ValueError, match="own extraction"):
        instance.observe(turn("S1-T2", "More"), datetime(2026, 10, 1), gold_candidates=[])
    assert len(memory.adds) == 1


def test_search_scoped_and_citations_limited_to_seen_evidence():
    rows = [{"memory": "BERT is the current project model", "metadata": {"source_turn_id": "S1-T1"}}]
    instance, memory, model = system(rows, {"status": "answer", "value": "BERT", "cited_turn_ids": ["S1-T1", "S9-T1"]})
    instance.observe(turn("S1-T1", "Use BERT."), datetime(2026, 10, 1))
    before = instance.fingerprint()
    answer = instance.answer(q())
    assert answer.status == "answer" and answer.value == "BERT"
    assert answer.cited_turn_ids == ["S1-T1"]
    assert answer.context_turn_ids == ["S1-T1"]
    assert answer.usage.calls == 1 and answer.usage.input_tokens == 27
    assert instance.fingerprint() == before
    assert memory.searches == [(q().text, {"filters": {"user_id": instance.user_id}, "top_k": 10})]
    sent = json.loads(model.calls[0]["messages"][1]["content"])
    assert sent["memories"] == [{"text": rows[0]["memory"], "source_turn_id": "S1-T1"}]
    assert "gold" not in json.dumps(sent).lower()


def test_as_of_avoids_using_future_memories():
    rows = [
        {"memory": "BERT was chosen", "source_turn_id": "S1-T1"},
        {"memory": "DistilBERT replaced BERT", "source_turn_id": "S3-T1"},
        {"memory": "Unattributed summary (cannot be time-filtered)"},
    ]
    instance, memory, model = system(rows)
    for identifier in ("S1-T1", "S3-T1"):
        instance.observe(turn(identifier, "Something"), datetime(2026, 10, 1))
    answer = instance.answer(q(kind="as_of", session="S1"))
    assert answer.context_turn_ids == ["S1-T1"]
    passed = json.loads(model.calls[0]["messages"][1]["content"])
    assert passed["memories"] == [{"text": "BERT was chosen", "source_turn_id": "S1-T1"}]


def test_empty_memory_returns_none_without_answer_model_call():
    instance, memory, model = system()
    answer = instance.answer(q())
    assert answer.status == "none"
    assert answer.value is None
    assert not model.calls


def test_malformed_answer_abstains_and_dispute_is_not_a_value():
    rows = [{"memory": "Possible conflict: BERT or DistilBERT"}]
    instance, _, model = system(rows, {"status": "conflict", "value": "DistilBERT", "cited_turn_ids": []})
    conflict = instance.answer(q())
    assert conflict.status == "conflict" and conflict.value is None
    model.payload = {"status": "answer", "value": None, "cited_turn_ids": []}
    abstain = instance.answer(q())
    assert abstain.status == "abstain" and abstain.value is None


def test_unobserved_source_is_never_accepted():
    instance, _, model = system([{"memory": "Leak", "source_turn_id": "S99-T1"}])
    result = instance.answer(q())
    assert result.status == "none"
    assert not model.calls
