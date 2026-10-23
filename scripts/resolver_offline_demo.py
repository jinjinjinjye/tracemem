"""Offline integration smoke test: real Resolver and OpLog, scripted model replies.

After installing the package, run from the repository root:
    python scripts/resolver_offline_demo.py

This is a synthetic plumbing example, not a benchmark or evidence of LLM accuracy.
Candidates and model replies are supplied explicitly. No API, key, SDK, extraction
model or answer model is used. Historical state comes from OpLog.upto(), not from
an LLM-generated answer or the benchmark's expected-answer implementation.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from tracemem.ops import OpLog, record_id
from tracemem.resolver import LLMResolver, ModelReply, ResolverConfig
from tracemem.schema import Candidate, Operation, Record


ITEM = "model.sentiment"  # The sentiment classifier selected for the project.
PROJECT = "synthetic-resolver-handoff"
TURNS = {
    "S1-T1": "Let's use BERT for the sentiment classifier.",
    "S2-T1": "Maybe we could try DistilBERT? It might be faster.",
    "S3-T1": "We accept the suggestion and switch the classifier to DistilBERT.",
    "S4-T1": "For the write-up: the sentiment classifier is still DistilBERT.",
}


def gloss(turn_id: str) -> str:
    return f'{turn_id} ("{TURNS[turn_id]}")'


def scripted_decision(op, turn_id, *, add_as=None, targets=(), extra_sources=()):
    """Hand-authored mock completion for this integration smoke test only."""
    return {
        "op": op,
        "add_as": add_as,
        "targets": list(targets),
        "source_turn_ids": [turn_id, *extra_sources],
        "reason": None,
        "rationale": "Scripted offline response; no semantic model evaluation.",
    }


class ScriptedClient:
    """Implement CompletionClient without importing any provider SDK."""

    def __init__(self, decisions):
        self.decisions = list(decisions)
        self.calls = 0

    def complete(self, *, config, messages, response_format):
        assert config.model == "offline-scripted-demo"
        assert response_format["type"] == "json_schema"
        assert messages[0]["role"] == "system"
        if not self.decisions:
            raise AssertionError("Unexpected additional model request in offline demo")
        self.calls += 1
        return ModelReply(content=json.dumps(self.decisions.pop(0)))


def main() -> None:
    original = record_id(ITEM, "S1-T1")  # Initial BERT decision.
    proposal = record_id(ITEM, "S2-T1")  # DistilBERT suggestion.
    adopted = record_id(ITEM, "S3-T1")  # Formal DistilBERT adoption.
    client = ScriptedClient([
        scripted_decision("ADD", "S1-T1", add_as="active"),
        scripted_decision("ADD", "S2-T1", add_as="proposed"),
        scripted_decision("SUPERSEDE", "S3-T1", targets=[original, proposal],
                          extra_sources=["S2-T1"]),
        scripted_decision("KEEP", "S4-T1", targets=[adopted]),
    ])
    resolver = LLMResolver(ResolverConfig(model="offline-scripted-demo"), client)
    log = OpLog(PROJECT)

    print("OFFLINE DEMO: scripted model replies; real Resolver validation and OpLog.")
    for index, (turn_id, text) in enumerate(TURNS.items()):
        value = "BERT" if index == 0 else "DistilBERT"
        log.observe_turn(turn_id, datetime(2026, 1, 1, 10) + timedelta(days=index),
                         speaker="Synthetic speaker")
        candidate = Candidate(
            candidate_id=record_id(ITEM, turn_id), project_id=PROJECT, item=ITEM,
            value=value, source_turn_ids=[turn_id], speaker="Synthetic speaker",
            text=text,
        )
        related: list[Record] = log.records(ITEM)
        before = log.fingerprint()
        operation: Operation = resolver.resolve(candidate, related)
        assert log.fingerprint() == before, "Resolver must not mutate storage"
        log.apply(operation)
        state = log.item_state(ITEM)
        assert state.active is not None

        print(f"\n{index + 1}. {gloss(turn_id)}")
        print(f"   Operation: {operation.op}; current value: {state.active.value}")
        if index == 0:
            assert operation.op == "ADD" and operation.add_as == "active"
            assert state.active.record_id == original
        elif index == 1:
            assert operation.op == "ADD" and operation.add_as == "proposed"
            assert state.active.value == "BERT"
            assert [r.record_id for r in state.proposed] == [proposal]
            print("   DistilBERT is only proposed; BERT remains the current decision.")
        elif index == 2:
            assert operation.op == "SUPERSEDE"
            assert set(operation.targets) == {original, proposal}
            assert state.active.record_id == adopted
            assert state.active.source_turn_ids == ["S3-T1", "S2-T1"]
            assert state.active.supersedes == [original, proposal]
            assert state.previous_active is not None
            assert state.previous_active.value == "BERT"
            assert state.proposed == []
            assert {r.record_id for r in state.history} == {original, proposal}
            assert all(r.status == "superseded" for r in state.history)
            print("   Closed both the old BERT decision and the accepted proposal.")
            print("   Adoption evidence includes the suggestion and the acceptance.")
        else:
            assert operation.op == "KEEP" and operation.targets == [adopted]
            assert state.active.record_id == adopted
            assert state.active.created_turn == "S3-T1"
            assert state.active.source_turn_ids == ["S3-T1", "S2-T1", "S4-T1"]
            assert len(log.records(ITEM)) == 3
            print("   Confirmation adds evidence; it does not create another version.")

    current_before_history = log.fingerprint()
    historical_log = log.upto("S2-T1")  # State at the suggestion, before adoption.
    historical = historical_log.item_state(ITEM)
    assert historical.active is not None and historical.active.value == "BERT"
    assert [r.value for r in historical.proposed] == ["DistilBERT"]
    assert len(historical_log.ops) == 2
    assert all("S3-T1" not in r.source_turn_ids and "S4-T1" not in r.source_turn_ids
               for r in historical_log.records())
    assert log.fingerprint() == current_before_history
    assert log.item_state(ITEM).active.value == "DistilBERT"
    assert client.calls == 4 and not client.decisions
    assert resolver.usage().calls == 4

    print(f"\n5. Historical state as of {gloss('S2-T1')}")
    print("   Current then: BERT; pending suggestion then: DistilBERT.")
    print("   Current now: DistilBERT; historical inspection did not alter storage.")
    print("\nPASS: all integration assertions passed; 4 scripted calls, 0 network calls.")
    print("This verifies wiring and state semantics, not live-model decision quality.")


if __name__ == "__main__":
    main()
