"""Executable adoption-source requirements, independent of model interpretation."""

import json

import pytest

import tracemem.resolver as resolver_module
from tracemem.resolver import ResolverError
from test_resolver import candidate, decision, log_with, operation, reply, resolver, rid, seeded_log


@pytest.mark.parametrize("op,status", [
    ("ADD", "proposed"),
    ("SUPERSEDE", "proposed"),
    ("SUPERSEDE", "contested"),
])
def test_adoption_requires_the_selected_origin_and_retries_without_applying_partial_evidence(op, status):
    log = log_with()
    if op == "SUPERSEDE":
        log.apply(operation("ADD", "S1-T1", "A", add_as="active"))
    log.apply(operation("FLAG" if status == "contested" else "ADD", "S1-T2", "B",
                        add_as="proposed" if status == "proposed" else None,
                        targets=[rid("S1-T1")] if status == "contested" else []))
    targets = ([rid("S1-T1")] if op == "SUPERSEDE" else []) + [rid("S1-T2")]
    bad = decision(op, add_as="active" if op == "ADD" else None, targets=targets)
    good = {**bad, "source_turn_ids": ["S1-T2", "S1-T4"]}
    real, client = resolver(reply(bad), reply(good))
    before = [record.model_dump() for record in log.records()]

    resolved = real.resolve(candidate(), log.records())

    assert [record.model_dump() for record in log.records()] == before
    assert len(client.calls) == real.usage().calls == 2
    first, retried = (call["messages"] for call in client.calls)
    assert retried[:2] == first
    assert set(json.loads(first[1]["content"])) == {"candidate", "related", "target_constraints"}
    feedback = json.loads(retried[2]["content"])
    assert "creating turns in sources: S1-T2" in feedback["error"]
    assert feedback["rejected_decision"]["targets"] == targets
    assert feedback["rejected_decision"]["source_turn_ids"] == ["S1-T4"]
    assert "dropping a justified target" in feedback["instruction"]
    assert resolved.targets == targets and resolved.source_turn_ids == ["S1-T4", "S1-T2"]
    log.apply(resolved)
    state = log.item_state(candidate().item)
    assert state.active.value == "B" and state.active.source_turn_ids == ["S1-T4", "S1-T2"]
    assert not state.proposed and not state.contested and not state.flagged
    if op == "SUPERSEDE":
        assert state.previous_active.value == "A"
    else:
        assert state.previous_active is None


def test_each_selected_proposal_origin_is_required_without_copying_its_other_sources():
    log = log_with(operation("ADD", "S1-T1", "A", add_as="active"),
                   operation("ADD", "S1-T2", "B", add_as="proposed", sources=["S1-T1", "S1-T2"]),
                   operation("ADD", "S1-T3", "B", add_as="proposed"))
    targets = [rid("S1-T1"), rid("S1-T2"), rid("S1-T3")]
    partial = decision("SUPERSEDE", add_as=None, targets=targets, sources=["S1-T5", "S1-T4", "S1-T2"])
    complete = {**partial, "source_turn_ids": ["S1-T2", "S1-T3", "S1-T4", "S1-T5"]}
    real, client = resolver(reply(partial), reply(complete))
    cand = candidate(turn="S1-T5", source_turn_ids=["S1-T5", "S1-T4"])

    op = real.resolve(cand, log.records())

    assert "creating turns in sources: S1-T3" in json.loads(client.calls[1]["messages"][2]["content"])["error"]
    assert op.source_turn_ids == ["S1-T5", "S1-T4", "S1-T2", "S1-T3"]
    assert "S1-T1" not in op.source_turn_ids  # Neither active history nor unrelated accumulated support.
    log.apply(op)
    assert log.item_state(cand.item).active.supersedes == targets


def test_visible_creation_turn_is_usable_even_when_not_in_the_records_source_list():
    # The public contract allows this: creation metadata and supporting sources differ.
    log = log_with(operation("ADD", "S1-T2", "B", add_as="proposed", sources=["S1-T1"]))
    assert log.records()[0].created_turn == "S1-T2"
    assert log.records()[0].source_turn_ids == ["S1-T1"]
    bad = decision(targets=[rid("S1-T2")], sources=["S1-T4", "S1-T1"])
    good = decision(targets=[rid("S1-T2")], sources=["S1-T4", "S1-T2"])
    real, client = resolver(reply(bad), reply(good))

    log.apply(real.resolve(candidate(), log.records()))

    assert len(client.calls) == 2
    assert log.item_state(candidate().item).active.source_turn_ids == ["S1-T4", "S1-T2"]


@pytest.mark.parametrize("foreign_field,foreign_value", [("project_id", "foreign"), ("item", "model.other")])
def test_filtered_record_creation_turns_are_not_available_sources(foreign_field, foreign_value):
    record = log_with(operation("ADD", "S1-T2", "B", add_as="proposed", sources=["S1-T1"])).records()[0]
    foreign = record.model_copy(update={foreign_field: foreign_value})
    bad = reply(decision(sources=["S1-T4", "S1-T2"]))
    real, client = resolver(bad, bad)

    with pytest.raises(ResolverError, match="sources must come from the candidate or supplied records"):
        real.resolve(candidate(), [foreign])

    assert json.loads(client.calls[0]["messages"][1]["content"])["related"] == []
    assert len(client.calls) == 2


@pytest.mark.parametrize("op,value", [("SUPERSEDE", "B"), ("KEEP", "A"), ("FLAG", "B")])
def test_operations_without_adopted_targets_do_not_require_old_or_unselected_sources(op, value):
    log = seeded_log()
    real, client = resolver(reply(decision(op, add_as=None, targets=[rid("S1-T1")])))

    resolved = real.resolve(candidate(value=value), log.records())

    assert resolved.source_turn_ids == ["S1-T4"]
    log.apply(resolved)
    assert len(client.calls) == 1
    assert [r.record_id for r in log.item_state(candidate().item).proposed] == [rid("S1-T2")]


def test_unselected_proposal_does_not_force_adoption_or_sources_without_an_active_record():
    log = log_with(operation("ADD", "S1-T2", "B", add_as="proposed"))
    real, client = resolver(reply(decision()))

    log.apply(real.resolve(candidate(), log.records()))

    assert len(client.calls) == 1
    state = log.item_state(candidate().item)
    assert state.active.source_turn_ids == ["S1-T4"]
    assert state.proposed[0].record_id == rid("S1-T2")
    # Choosing which proposals were adopted remains a semantic responsibility.


def test_missing_origin_diagnostics_are_bounded_and_exhaustion_does_not_mutate_inputs(monkeypatch):
    template = log_with(operation("ADD", "S1-T2", "B", add_as="proposed")).records()[0]
    origins = ["S1-T123456", "S1-T234567", "S1-T345678"]
    records = [template.model_copy(update={"record_id": rid(turn), "created_turn": turn,
                                          "source_turn_ids": [turn]}) for turn in origins]
    targets = [record.record_id for record in records]
    before = [record.model_dump() for record in records]
    monkeypatch.setattr(resolver_module, "FEEDBACK_MAX_IDS", 2)
    monkeypatch.setattr(resolver_module, "FEEDBACK_MAX_ID_CHARS", 9)
    bad = reply(decision(targets=targets))
    real, client = resolver(bad, bad)

    with pytest.raises(ResolverError) as caught:
        real.resolve(candidate(), records)

    feedback = json.loads(client.calls[1]["messages"][2]["content"])
    assert feedback["error"].endswith("S1-T12345, S1-T23456 (truncated)")
    assert origins[2] not in feedback["error"]
    assert feedback["rejected_decision_truncated"] is True
    assert caught.value.attempts == len(client.calls) == real.usage().calls == 2
    assert [record.model_dump() for record in records] == before


def test_feedback_reports_missing_and_extra_sources_together_without_dropping_targets():
    log = log_with(operation("ADD", "S1-T1", "A", add_as="active"),
                   operation("ADD", "S1-T2", "B", add_as="proposed"))
    targets = [rid("S1-T1"), rid("S1-T2")]
    bad = decision("SUPERSEDE", add_as=None, targets=targets, sources=["S1-T4", "S1-T1"])
    good = {**bad, "source_turn_ids": ["S1-T2", "S1-T4"]}
    real, client = resolver(reply(bad), reply(good))

    resolved = real.resolve(candidate(), log.records())

    feedback = json.loads(client.calls[1]["messages"][2]["content"])
    assert "requires their creating turns in sources: S1-T2" in feedback["error"]
    assert "extra sources outside candidate sources and selected creating turns: S1-T1" in feedback["error"]
    assert feedback["rejected_decision"]["targets"] == targets
    assert resolved.targets == targets
    assert resolved.source_turn_ids == ["S1-T4", "S1-T2"]
    log.apply(resolved)
    assert log.item_state(candidate().item).previous_active.value == "A"


@pytest.mark.parametrize("op,status", [("ADD", "proposed"), ("SUPERSEDE", "proposed"),
                                      ("SUPERSEDE", "contested")])
def test_selected_accumulated_support_and_unselected_origins_are_not_adoption_sources(op, status):
    log = log_with()
    if op == "SUPERSEDE":
        log.apply(operation("ADD", "S1-T1", "A", add_as="active"))
    log.apply(operation("FLAG" if status == "contested" else "ADD", "S1-T3", "B",
                        add_as="proposed" if status == "proposed" else None,
                        targets=[rid("S1-T1")] if status == "contested" else [],
                        sources=["S1-T3", "S1-T2"]))
    log.apply(operation("ADD", "S1-T4", "B", add_as="proposed"))
    targets = ([rid("S1-T1")] if op == "SUPERSEDE" else []) + [rid("S1-T3")]
    bad = decision(op, add_as="active" if op == "ADD" else None, targets=targets,
                   sources=["S1-T6", "S1-T3", "S1-T2", "S1-T4"])
    good = {**bad, "source_turn_ids": ["S1-T6", "S1-T3"]}
    real, client = resolver(reply(bad), reply(good))

    resolved = real.resolve(candidate(turn="S1-T6"), log.records())

    feedback = json.loads(client.calls[1]["messages"][2]["content"])
    assert feedback["error"].endswith("selected creating turns: S1-T2, S1-T4")
    assert resolved.source_turn_ids == ["S1-T6", "S1-T3"]
    log.apply(resolved)
    state = log.item_state(candidate().item)
    assert state.active.source_turn_ids == ["S1-T6", "S1-T3"]
    assert [record.record_id for record in state.proposed] == [rid("S1-T4")]


def test_candidate_origin_overlap_is_a_set_union_with_multiple_selected_proposals():
    log = log_with(operation("ADD", "S1-T2", "B", add_as="proposed"),
                   operation("ADD", "S1-T3", "B", add_as="proposed"))
    targets = [rid("S1-T2"), rid("S1-T3")]
    cand = candidate(source_turn_ids=["S1-T4", "S1-T2"])
    real, client = resolver(reply(decision(targets=targets, sources=["S1-T2", "S1-T3", "S1-T4"])))

    resolved = real.resolve(cand, log.records())

    assert resolved.source_turn_ids == ["S1-T4", "S1-T2", "S1-T3"]
    assert len(client.calls) == 1
    log.apply(resolved)
    assert not log.item_state(cand.item).proposed


def test_extra_source_diagnostics_are_bounded_and_exhaustion_does_not_mutate_inputs(monkeypatch):
    template = log_with(operation("ADD", "S1-T2", "B", add_as="proposed")).records()[0]
    extras = ["S1-T123456", "S1-T234567", "S1-T345678"]
    record = template.model_copy(update={"source_turn_ids": ["S1-T2", *extras]})
    before = record.model_dump()
    monkeypatch.setattr(resolver_module, "FEEDBACK_MAX_IDS", 2)
    monkeypatch.setattr(resolver_module, "FEEDBACK_MAX_ID_CHARS", 9)
    bad = reply(decision(targets=[record.record_id], sources=["S1-T4", "S1-T2", *extras]))
    real, client = resolver(bad, bad)

    with pytest.raises(ResolverError) as caught:
        real.resolve(candidate(), [record])

    feedback = json.loads(client.calls[1]["messages"][2]["content"])
    assert feedback["error"].endswith("S1-T12345, S1-T23456 (truncated)")
    assert extras[2] not in feedback["error"]
    assert feedback["rejected_decision_truncated"] is True
    assert caught.value.attempts == len(client.calls) == real.usage().calls == 2
    assert record.model_dump() == before
