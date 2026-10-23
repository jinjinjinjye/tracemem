"""Offline policy wiring and boundary states with explicitly scripted decisions.

These are not model-accuracy tests. In particular, they ensure that code does not
rewrite a supplied decision based on words like 'maybe', 'not' or 'approval'.
"""

import json

import pytest

import tracemem.resolver as resolver_module
from tracemem.systems.comparison import comparison_settings
from test_resolver import (
    ITEM, ScriptedClient, candidate, decision, log_with, operation, reply, resolver, rid,
)


@pytest.mark.parametrize("text,value,op,add_as,active,proposed", [
    ("We chose A for classification. Maybe B for the main model?",
     "B", "ADD", "proposed", "A", ["B"]),
    ("Earlier we said 'maybe B'; we now confirm B for the main model.",
     "B", "SUPERSEDE", None, "B", []),
    ("We will not switch to B; keep A for the main model.",
     "A", "KEEP", None, "A", []),
])
def test_scripted_candidate_specific_decisions_preserve_text_and_do_not_use_keyword_overrides(
    text, value, op, add_as, active, proposed,
):
    log = log_with(operation("ADD", "S1-T1", "A", add_as="active"))
    cand = candidate(value=value, text=text)
    scripted = decision(op, add_as=add_as, targets=[] if op == "ADD" else [rid("S1-T1")])
    real, client = resolver(reply(scripted))

    log.apply(real.resolve(cand, log.records()))

    state = log.item_state(ITEM)
    assert state.active.value == active
    assert [record.value for record in state.proposed] == proposed
    assert not state.flagged
    assert len(client.calls) == 1
    assert json.loads(client.calls[0]["messages"][1]["content"])["candidate"] == cand.model_dump(mode="json")


@pytest.mark.parametrize("text,value", [
    ("The checks are blocked pending access approval, but remain assigned to me.", "blocked"),
    ("We will not run the checks; cancel the task.", "cancelled"),
])
def test_scripted_task_progress_with_approval_or_negation_still_replaces_active_state(text, value):
    item = "task.checks"
    log = log_with(operation("ADD", "S1-T1", "open", add_as="active", item=item))
    cand = candidate(item=item, candidate_id=rid("S1-T4", item), value=value, text=text)
    real, _ = resolver(reply(decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1", item)])))

    log.apply(real.resolve(cand, log.records()))

    state = log.item_state(item)
    assert state.active.value == value
    assert state.previous_active.value == "open"
    assert state.previous_active.status == "superseded"
    assert not state.proposed
    assert state.active.source_turn_ids == ["S1-T4"]


def test_scripted_same_value_tentative_suggestion_does_not_reaffirm_or_clear_dispute():
    log = log_with(operation("ADD", "S1-T1", "A", add_as="active"),
                   operation("FLAG", "S1-T2", "B", targets=[rid("S1-T1")]))
    cand = candidate(value="A", text="Maybe A could be considered, but I am not confirming either claim.")
    real, _ = resolver(reply(decision(add_as="proposed")))

    log.apply(real.resolve(cand, log.records()))

    state = log.item_state(ITEM)
    assert state.active.record_id == rid("S1-T1")
    assert state.active.source_turn_ids == ["S1-T1"]
    assert state.flagged
    assert [record.record_id for record in state.contested] == [rid("S1-T2")]
    assert [(record.value, record.status) for record in state.proposed] == [("A", "proposed")]


def test_structural_retry_keeps_original_evidence_and_intent_guide_without_extra_model_step():
    log = log_with(operation("ADD", "S1-T1", "A", add_as="active"))
    cand = candidate(text="A misses cases. Maybe try B?")
    bad = decision("SUPERSEDE", add_as=None, targets=[])
    corrected = decision(add_as="proposed")
    real, client = resolver(reply(bad), reply(corrected))

    log.apply(real.resolve(cand, log.records()))

    assert len(client.calls) == real.usage().calls == 2
    first, second = (call["messages"] for call in client.calls)
    assert second[:2] == first
    assert resolver_module.INTENT_GUIDE in second[0]["content"]
    feedback = json.loads(second[2]["content"])
    assert feedback["instruction"] == resolver_module.RETRY_INSTRUCTION
    assert "candidate-specific speech act" in feedback["instruction"]
    assert "Structural legality does not establish semantic correctness" in feedback["instruction"]
    assert log.item_state(ITEM).active.value == "A"
    assert [record.value for record in log.item_state(ITEM).proposed] == ["B"]
    assert not log.item_state(ITEM).flagged


@pytest.mark.parametrize("name,value,hash_key,reference_key", [
    ("INTENT_POLICY_VERSION", "offline-alternate-intent-policy", "decision_policy_hash",
     "resolver_reference_policy_hash"),
    ("SYSTEM_PROMPT", "offline-alternate-intent-guide", "prompt_hash",
     "resolver_reference_prompt_hash"),
])
def test_intent_policy_and_prompt_changes_reach_comparison_fingerprints_without_calls(
    monkeypatch, name, value, hash_key, reference_key,
):
    config = resolver_module.ResolverConfig(model="offline-model")
    client = ScriptedClient()
    real = resolver_module.LLMResolver(config, client)
    before = real.describe()
    old_comparison = comparison_settings(config, 12000, client)

    monkeypatch.setattr(resolver_module, name, value)

    after = real.describe()
    new_comparison = comparison_settings(config, 12000, client)
    assert before[hash_key] != after[hash_key]
    assert old_comparison[reference_key] == before[hash_key]
    assert new_comparison[reference_key] == after[hash_key]
    assert before["output_schema_hash"] == after["output_schema_hash"]
    assert client.calls == []
