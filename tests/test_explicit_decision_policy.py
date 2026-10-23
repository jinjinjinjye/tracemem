"""Scripted boundary and retry contracts; these do not classify text with a model."""

import json

import pytest

import tracemem.resolver as resolver_module
from tracemem.systems.comparison import comparison_settings
from test_resolver import (
    ITEM, ScriptedClient, candidate, decision, log_with, operation, reply, resolver, rid,
)


@pytest.mark.parametrize("text,add_as", [
    ("For the parser we'll use Cedar once the input arrives.", "active"),
    ("Let's make Cedar our parser from now on.", "active"),
    ("Let's consider making Cedar our parser.", "proposed"),
    ("If the team approves the choice, we'll use Cedar for the parser.", "proposed"),
    ("Earlier we said 'we will use Cedar'; that choice is withdrawn and only under consideration now.", "proposed"),
    ("We chose Pine for tagging. Should we use Cedar for the parser?", "proposed"),
])
def test_scripted_initial_choice_does_not_require_an_active_record_or_adopt_an_unrelated_proposal(text, add_as):
    # An older proposal is not the current selection, nor a target for a different value.
    log = log_with(operation("ADD", "S1-T1", "Birch", add_as="proposed"))
    cand = candidate(text=text, value="Cedar")
    real, client = resolver(reply(decision(add_as=add_as)))

    op = real.resolve(cand, log.records())
    log.apply(op)

    state = log.item_state(ITEM)
    assert (state.active.value if state.active else None) == ("Cedar" if add_as == "active" else None)
    assert [r.value for r in state.proposed] == (["Birch"] if add_as == "active" else ["Birch", "Cedar"])
    assert not state.history and state.previous_active is None
    assert op.targets == [] and op.source_turn_ids == ["S1-T4"]
    assert len(client.calls) == real.usage().calls == 1
    payload = json.loads(client.calls[0]["messages"][1]["content"])
    assert payload["candidate"] == cand.model_dump(mode="json")
    assert payload["target_constraints"]["active_record_id"] is None
    assert set(payload) == {"candidate", "related", "target_constraints"}


@pytest.mark.parametrize("text,op,add_as", [
    ("Let's consider reopening the checks now that time is available.", "ADD", "proposed"),
    ("If the team approves reopening, we'll restart the checks.", "ADD", "proposed"),
    ("Let's reopen the checks; I am assigned to restart them today.", "SUPERSEDE", None),
    ("We are reopening the checks and will run them once access returns.", "SUPERSEDE", None),
])
def test_scripted_selection_wording_does_not_bypass_the_cancelled_task_boundary(text, op, add_as):
    item = "task.checks"
    log = log_with(operation("ADD", "S1-T1", "open", add_as="active", item=item),
                   operation("SUPERSEDE", "S1-T2", "cancelled", targets=[rid("S1-T1", item)], item=item))
    cand = candidate(item=item, candidate_id=rid("S1-T4", item), value="open", text=text)
    real, client = resolver(reply(decision(op, add_as=add_as,
        targets=[rid("S1-T2", item)] if op == "SUPERSEDE" else [])))

    log.apply(real.resolve(cand, log.records()))

    state = log.item_state(item)
    assert state.active.value == ("open" if op == "SUPERSEDE" else "cancelled")
    assert [r.value for r in state.proposed] == ([] if op == "SUPERSEDE" else ["open"])
    assert not state.flagged and not state.contested
    assert log.upto("S1-T2").item_state(item).active.value == "cancelled"
    assert len(client.calls) == 1
    prompt = client.calls[0]["messages"][0]["content"]
    assert prompt.endswith(resolver_module.TRANSITION_EVIDENCE_GUIDE)


def test_scripted_retry_of_a_settled_replacement_keeps_the_active_predecessor_and_unaccepted_alternative():
    log = log_with(operation("ADD", "S1-T1", "Cedar", add_as="active"),
                   operation("ADD", "S1-T2", "Birch", add_as="proposed"))
    cand = candidate(text="The measurements favour Pine. Let's make Pine our parser.", value="Pine")
    real, client = resolver(
        reply(decision("SUPERSEDE", add_as=None)),
        reply(decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1")])),
    )

    log.apply(real.resolve(cand, log.records()))

    assert len(client.calls) == real.usage().calls == 2
    first, retried = (call["messages"] for call in client.calls)
    assert retried[:2] == first
    assert first[0]["content"] == resolver_module.SYSTEM_PROMPT
    feedback = json.loads(retried[2]["content"])
    assert feedback["instruction"] == resolver_module.RETRY_INSTRUCTION
    assert "without a second confirmation" in feedback["instruction"]
    assert "asking whether to restart" in feedback["instruction"]
    state = log.item_state(ITEM)
    assert state.active.value == "Pine" and state.active.supersedes == [rid("S1-T1")]
    assert state.active.source_turn_ids == ["S1-T4"]
    assert state.previous_active.value == "Cedar"
    assert state.previous_active.source_turn_ids == ["S1-T1"]
    assert [r.value for r in state.proposed] == ["Birch"]
    assert log.upto("S1-T2").item_state(ITEM).active.value == "Cedar"
    assert len(log.ops) == 3  # The structurally invalid first response was not applied.


def test_selection_policy_version_changes_write_fingerprints_without_changing_the_reader_or_schemas(monkeypatch):
    config = resolver_module.ResolverConfig(model="offline-selection-boundaries")
    client = ScriptedClient()
    real = resolver_module.LLMResolver(config, client)
    current = comparison_settings(config, 12000, client)
    description = real.describe()
    assert resolver_module.INTENT_POLICY_VERSION == "candidate-speech-act-v4"

    monkeypatch.setattr(resolver_module, "INTENT_POLICY_VERSION", "candidate-speech-act-v3")
    preceding_version = comparison_settings(config, 12000, client)

    assert {k for k in current if current[k] != preceding_version[k]} == {"resolver_reference_policy_hash"}
    assert real.describe()["output_schema_hash"] == description["output_schema_hash"]
    assert current["answer_prompt_hash"] == preceding_version["answer_prompt_hash"]
    assert not client.calls
