"""The version ablation keeps current operation semantics and loses historical memory."""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from support import PILOT_IDS, pilot, pilot_timeline, turn_clock
from tracemem.components import GoldMatcher
from tracemem.ops import InvalidOperation, OpLog, record_id
from tracemem.resolver import LLMResolver, ModelReply, ResolverConfig
from tracemem.schema import Candidate, Operation
from tracemem.systems.no_versions import CurrentOnlyStore


ITEM = "model.main"
CLOCK = turn_clock(*(f"S1-T{i}" for i in range(1, 10)))


def operation(turn, value, *, op="ADD", add_as="active", targets=(), sources=None, item=ITEM):
    return Operation(op_id=f"op:{item}@{turn}", op=op, turn_id=turn, item=item, value=value,
                     add_as=add_as if op == "ADD" else None, targets=list(targets),
                     source_turn_ids=list(sources or [turn]), candidate_id=f"{item}@{turn}")


def populated(*operations):
    store = CurrentOnlyStore("synthetic-project")
    for turn, when in CLOCK.items():
        store.observe_turn(turn, when, "Speaker")
    for op in operations:
        store.apply(op)
    return store


def current_projection(log):
    return [record.model_copy(update={"supersedes": []}, deep=True)
            for record in log.records() if record.status in ("active", "proposed", "contested")]


@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_each_development_operation_matches_the_reference_current_projection(scenario_id):
    """Exercise current semantics independently of a language model on all public pilots."""
    scenario = pilot(scenario_id)
    gold = pilot_timeline(scenario_id)
    store, reference = CurrentOnlyStore(scenario.project_id), OpLog(scenario.project_id)
    turns = {turn.id: turn for turn in scenario.turns()}
    for turn_id in gold.turn_order:
        turn = turns[turn_id]
        for target in (store, reference):
            target.observe_turn(turn_id, gold.turn_times[turn_id], turn.speaker)
        for op in gold.ops_by_turn[turn_id]:
            reference.apply(op)
            store.apply(op)
            assert store.records() == current_projection(reference)
            for item in reference.items():
                actual, expected = store.item_state(item), reference.item_state(item)
                assert actual.summary() == expected.summary()
                assert actual.history == [] and actual.previous_active is None
                live = {record.record_id for record in store.records(item)}
                assert actual.creating_turns == {rid: sources for rid, sources in expected.creating_turns.items()
                                                 if rid in live}
                assert actual.kept_turns == {rid: sources for rid, sources in expected.kept_turns.items()
                                             if rid in live}
    assert store.ops == reference.ops
    assert not hasattr(store, "upto")
    assert not any(isinstance(value, OpLog) for value in vars(store).values())


def test_adopting_a_proposal_keeps_citations_but_drops_both_predecessors_and_links():
    initial = operation("S1-T1", "old-choice")
    proposal = operation("S1-T2", "new-choice", add_as="proposed")
    adoption = operation("S1-T3", "new-choice", op="SUPERSEDE",
                         targets=[initial.candidate_id, proposal.candidate_id], sources=["S1-T3", "S1-T2"])
    store = populated(initial, proposal, adoption)
    current, = store.records()
    assert current.record_id == adoption.candidate_id
    assert current.value == "new-choice"
    assert current.status == "active"
    assert current.supersedes == []
    assert current.source_turn_ids == ["S1-T3", "S1-T2"]
    assert current.speakers == ["Speaker", "Speaker"]
    assert current.created_at == CLOCK["S1-T3"]
    assert "old-choice" not in json.dumps([record.model_dump(mode="json") for record in store.records()])
    assert set(store._live) == {adoption.candidate_id}
    assert set(store._creating_turns) == set(store._kept_turns) == {adoption.candidate_id}


def test_adoption_without_an_active_choice_and_keep_preserve_open_state_semantics():
    proposal = operation("S1-T1", "B", add_as="proposed")
    accepted = operation("S1-T2", "B", targets=[proposal.candidate_id], sources=["S1-T2", "S1-T1"])
    dispute = operation("S1-T3", "C", op="FLAG", targets=[accepted.candidate_id])
    store = populated(proposal)
    assert store.item_state(ITEM).summary() == (None, False, ("B",), ())
    store.apply(accepted)
    store.apply(dispute)
    assert store.item_state(ITEM).summary() == ("B", True, (), ("C",))
    confirmation = operation("S1-T4", "B", op="KEEP", targets=[accepted.candidate_id])
    store.apply(confirmation)
    state = store.item_state(ITEM)
    assert state.summary() == ("B", False, (), ())
    assert state.active.source_turn_ids == ["S1-T2", "S1-T1", "S1-T4"]
    assert state.creating_turns == {accepted.candidate_id: ["S1-T2", "S1-T1"]}
    assert state.kept_turns == {accepted.candidate_id: ["S1-T4"]}
    assert state.history == []
    assert [record.record_id for record in store.records()] == [accepted.candidate_id]
    # A subsequent write reconstructs only open state, preserving KEEP evidence.
    store.apply(operation("S1-T5", "D", add_as="proposed"))
    assert store.item_state(ITEM).kept_turns[accepted.candidate_id] == ["S1-T4"]
    assert store.item_state(ITEM).active.source_turn_ids == ["S1-T2", "S1-T1", "S1-T4"]


def test_unadopted_proposals_remain_when_a_current_choice_changes():
    first = operation("S1-T1", "A")
    proposal = operation("S1-T2", "B", add_as="proposed")
    replacement = operation("S1-T3", "C", op="SUPERSEDE", targets=[first.candidate_id])
    store = populated(first, proposal, replacement)
    assert store.item_state(ITEM).summary() == ("C", False, ("B",), ())
    assert [record.record_id for record in store.records()] == [proposal.candidate_id, replacement.candidate_id]
    assert all(record.supersedes == [] for record in store.records())


def test_return_to_an_old_value_creates_a_new_identity_without_restoring_history():
    first = operation("S1-T1", "A")
    second = operation("S1-T2", "B", op="SUPERSEDE", targets=[first.candidate_id])
    third = operation("S1-T3", "A", op="SUPERSEDE", targets=[second.candidate_id])
    store = populated(first, second, third)
    current, = store.records()
    assert current.record_id == third.candidate_id
    assert current.created_turn == "S1-T3"
    assert current.source_turn_ids == ["S1-T3"]
    assert current.supersedes == []
    assert store.item_state(ITEM).previous_active is None
    assert set(store._created_ids) == {first.candidate_id, second.candidate_id, third.candidate_id}


@pytest.mark.parametrize("invalid", [
    operation("S1-T2", "B"),
    operation("S1-T2", "B", op="KEEP", targets=[record_id(ITEM, "S1-T1")]),
    operation("S1-T2", "A", op="FLAG", targets=[record_id(ITEM, "S1-T1")]),
    operation("S1-T2", "B", op="SUPERSEDE", targets=[record_id(ITEM, "S1-T8")]),
    operation("S1-T2", "B", add_as="proposed", sources=["S2-T1"]),
])
def test_invalid_writes_do_not_change_memory_audit_or_fingerprint(invalid):
    store = populated(operation("S1-T1", "A"))
    before = store.records(), list(store.ops), store.fingerprint()
    with pytest.raises(InvalidOperation):
        store.apply(invalid)
    assert (store.records(), store.ops, store.fingerprint()) == before


def test_a_dropped_creation_id_cannot_be_reused_or_targeted():
    first = operation("S1-T1", "A")
    second = operation("S1-T2", "B", op="SUPERSEDE", targets=[first.candidate_id])
    store = populated(first, second)
    before = store.fingerprint()
    with pytest.raises(InvalidOperation):
        store.apply(operation("S1-T1", "C", add_as="proposed"))
    with pytest.raises(InvalidOperation):
        store.apply(operation("S1-T3", "C", op="SUPERSEDE", targets=[first.candidate_id]))
    assert store.fingerprint() == before


def test_real_resolver_and_same_item_matcher_receive_only_retained_memory():
    first = operation("S1-T1", "superseded-only-secret-choice")
    current = operation("S1-T2", "current-choice", op="SUPERSEDE", targets=[first.candidate_id])
    store = populated(first, current, operation("S1-T2", "other-choice", item="model.other"))
    candidate = Candidate(candidate_id=f"{ITEM}@S1-T3", project_id="synthetic-project", item=ITEM,
                          value="current-choice", source_turn_ids=["S1-T3"], speaker="Speaker",
                          text="We confirm the current choice.")

    class InspectClient:
        def complete(self, *, config, messages, response_format):
            evidence = json.loads(messages[1]["content"])
            assert "superseded-only-secret-choice" not in messages[1]["content"]
            assert "other-choice" not in messages[1]["content"]
            assert [record["record_id"] for record in evidence["related"]] == [current.candidate_id]
            assert evidence["related"][0]["supersedes"] == []
            return ModelReply(content=json.dumps({"op": "KEEP", "add_as": None,
                "targets": [current.candidate_id], "source_turn_ids": ["S1-T3"],
                "reason": None, "rationale": "The current choice is explicitly confirmed."}))

    resolver = LLMResolver(ResolverConfig(model="offline-model"), InspectClient())
    related = GoldMatcher().match(candidate, store)
    store.apply(resolver.resolve(candidate, related))
    assert store.item_state(ITEM).active.source_turn_ids == ["S1-T2", "S1-T3"]


def test_audit_is_not_a_hidden_source_for_memory_reconstruction():
    first = operation("S1-T1", "old-choice")
    current = operation("S1-T2", "current-choice", op="SUPERSEDE", targets=[first.candidate_id])
    store = populated(first, current)
    before = store.fingerprint()
    store.ops.clear()
    assert store.fingerprint() == before
    store.apply(operation("S1-T3", "current-choice", op="KEEP", targets=[current.candidate_id]))
    current_record, = store.records()
    assert current_record.value == "current-choice"
    assert current_record.source_turn_ids == ["S1-T2", "S1-T3"]
    assert current_record.supersedes == []
    assert len(store.ops) == 1


def test_read_snapshots_and_input_operations_do_not_expose_mutable_memory():
    original = operation("S1-T1", "A")
    store = populated(original)
    before = store.fingerprint()
    original.source_turn_ids.append("S1-T9")
    record = store.records()[0]
    record.source_turn_ids.append("S1-T8")
    record.supersedes.append("invented-history")
    state = store.item_state(ITEM)
    state.creating_turns[original.candidate_id].clear()
    state.active.source_turn_ids.clear()
    assert store.fingerprint() == before
    assert store.records()[0].source_turn_ids == ["S1-T1"]
    assert store.ops[0].source_turn_ids == ["S1-T1"]


def test_observations_and_keep_support_affect_fingerprint_but_reads_do_not():
    store = CurrentOnlyStore("synthetic-project")
    empty = store.fingerprint()
    store.observe_turn("S1-T1", CLOCK["S1-T1"], "Speaker")
    observed = store.fingerprint()
    assert observed != empty
    first = operation("S1-T1", "A")
    store.apply(first)
    populated_fingerprint = store.fingerprint()
    assert populated_fingerprint != observed
    for _ in range(2):
        store.records()
        store.items()
        store.item_state(ITEM)
        store.item_state("model.absent")
    assert store.fingerprint() == populated_fingerprint
    store.observe_turn("S1-T2", CLOCK["S1-T2"], "Speaker")
    before_keep = store.fingerprint()
    keep = operation("S1-T2", "A", op="KEEP", targets=[first.candidate_id])
    store.apply(keep)
    assert store.fingerprint() != before_keep
    supported = store.fingerprint()
    store.apply(keep)
    assert store.fingerprint() == supported
    assert store.records()[0].source_turn_ids == ["S1-T1", "S1-T2"]


def test_reobserved_metadata_does_not_rewrite_existing_creation_time():
    first = operation("S1-T1", "A")
    store = populated(first)
    store.observe_turn("S1-T1", CLOCK["S1-T1"] + timedelta(days=1), "Updated speaker")
    store.apply(operation("S1-T2", "B", add_as="proposed"))
    active = store.item_state(ITEM).active
    assert active.created_at == CLOCK["S1-T1"]
    assert active.speakers == ["Updated speaker"]
