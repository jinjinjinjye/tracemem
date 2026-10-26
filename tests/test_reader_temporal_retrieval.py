"""Historical reads use observed operations, while the ablation keeps only live state.

The fixture is a small independent operation sequence, with no scenario labels:
a choice is disputed in S2 and confirmed in S3. Its final declined record cannot
by itself reveal when the dispute closed, so an as-of read must project the log.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json

import pytest

from tracemem.ops import OpLog, record_id
from tracemem.resolver import ModelReply, ResolverConfig
from tracemem.schema import Operation, ScenarioMeta, SystemQuestion, Turn
from tracemem.systems import comparison
from tracemem.systems.no_versions import CurrentOnlyStore


CHOICE = "choice.main"
OTHER = "choice.secondary"


def operation(turn, value, *, item=CHOICE, op="ADD", target=None):
    return Operation(
        op_id=f"{item}:{turn}:{op}", op=op, turn_id=turn, item=item, value=value,
        add_as="active" if op == "ADD" else None,
        targets=[] if target is None else [record_id(item, target)],
        source_turn_ids=[turn], candidate_id=f"{item}@{turn}",
    )


def clock(turn):
    session, number = (int(part[1:]) for part in turn.split("-"))
    return datetime(2026, 1, session, 10, number)


def populated(store_type=OpLog):
    store = store_type("synthetic-temporal-project")
    sequence = [
        operation("S1-T1", "option X"),
        operation("S1-T2", "tool A", item=OTHER),
        operation("S2-T1", "option Y", op="FLAG", target="S1-T1"),
        operation("S3-T1", "option X", op="KEEP", target="S1-T1"),
        operation("S3-T2", "tool B", item=OTHER, op="SUPERSEDE", target="S1-T2"),
        operation("S4-T1", "option X", op="KEEP", target="S1-T1"),
    ]
    for op in sequence:
        store.observe_turn(op.turn_id, clock(op.turn_id), "Analyst")
        store.apply(op)
    return store


def question(kind="as_of", session="S2", *, opaque_id="opaque-temporal-question"):
    return SystemQuestion(question_id=opaque_id, scenario_id="opaque-scenario", kind=kind,
                          session=session if kind == "as_of" else None,
                          text="What was the primary choice at the requested time?")


def retrieve(store, kind="as_of", session="S2"):
    return comparison._AllMemory().retrieve(question(kind, session), store, 1)


def snapshot(store):
    return deepcopy((store.records(), store.ops, store.turn_times, store.speakers, store.fingerprint()))


def test_closed_current_claim_is_still_contested_in_observed_s2_projection():
    store = populated()
    assert store.item_state(CHOICE).flagged is False
    assert store.item_state(CHOICE).history[0].status == "declined"
    before = snapshot(store)

    records = retrieve(store)
    choice = {record.value: record for record in records if record.item == CHOICE}
    assert choice["option X"].status == "active"
    assert choice["option Y"].status == "contested"
    assert choice["option X"].source_turn_ids == ["S1-T1"]
    assert choice["option Y"].source_turn_ids == ["S2-T1"]
    assert {source for record in records for source in record.source_turn_ids} == {
        "S1-T1", "S1-T2", "S2-T1",
    }
    assert snapshot(store) == before


def test_s1_projection_does_not_include_a_future_claim_resolution_or_replacement():
    records = retrieve(populated(), session="S1")
    assert [(record.item, record.value, record.status) for record in records] == [
        (CHOICE, "option X", "active"), (OTHER, "tool A", "active"),
    ]
    assert {source for record in records for source in record.source_turn_ids} == {"S1-T1", "S1-T2"}


def test_s3_projection_includes_resolution_but_not_later_confirmation():
    records = retrieve(populated(), session="S3")
    choice = {record.value: record for record in records if record.item == CHOICE}
    assert choice["option X"].status == "active"
    assert choice["option X"].source_turn_ids == ["S1-T1", "S3-T1"]
    assert choice["option Y"].status == "declined"
    assert not any(record.status == "contested" for record in records)
    assert "S4-T1" not in {source for record in records for source in record.source_turn_ids}
    assert {(record.value, record.status) for record in records if record.item == OTHER} == {
        ("tool A", "superseded"), ("tool B", "active"),
    }


@pytest.mark.parametrize("kind", ["current", "previous"])
def test_other_question_kinds_keep_current_projection_and_retained_versions(kind):
    store = populated()
    records = retrieve(store, kind=kind)
    assert records == store.records()
    assert not any(record.status == "contested" for record in records)
    assert {(record.value, record.status) for record in records if record.item == OTHER} == {
        ("tool A", "superseded"), ("tool B", "active"),
    }
    assert "S4-T1" in next(record for record in records if record.value == "option X").source_turn_ids


@pytest.mark.parametrize("session", [None, "S0", "S9", "S10", "S2-extra"])
def test_unknown_or_unobserved_session_has_no_current_state_fallback(session):
    assert retrieve(populated(), session=session) == []


def test_session_boundary_is_exact_not_a_prefix_and_uses_last_observed_time():
    store = OpLog("synthetic-boundary-project")
    sequence = [operation("S1-T1", "option X"),
                operation("S1-T2", "option Y", op="FLAG", target="S1-T1"),
                operation("S10-T1", "option X", op="KEEP", target="S1-T1")]
    for op in sequence:
        store.observe_turn(op.turn_id, clock(op.turn_id))
        store.apply(op)
    # There was no write at this observed turn, but it is still the S1 boundary.
    store.observe_turn("S1-T3", clock("S1-T3"))
    records = retrieve(store, session="S1")
    assert [record.status for record in records] == ["active", "contested"]
    assert all("S10-T1" not in record.source_turn_ids for record in records)
    assert not any(record.status == "contested" for record in retrieve(store, session="S10"))


def test_retrieval_does_not_filter_by_question_identity_text_or_hidden_item():
    store = populated()
    reader = comparison._AllMemory()
    first = reader.retrieve(question(), store, 1)
    unrelated_question = question(opaque_id="unrelated-opaque-id").model_copy(update={
        "scenario_id": "another-opaque-scenario", "text": "What was the secondary choice?",
    })
    second = reader.retrieve(unrelated_question, store, 999999)
    assert first == second
    assert {record.item for record in first} == {CHOICE, OTHER}


def test_mutating_a_historical_result_does_not_mutate_the_store():
    store = populated()
    before = snapshot(store)
    records = retrieve(store)
    records[0].source_turn_ids.append("S99-T99")
    records.clear()
    assert snapshot(store) == before


@pytest.mark.parametrize("session", ["S1", "S2", "S3", "S9"])
def test_no_versions_reads_live_memory_even_when_its_audit_contains_historical_claims(session):
    store = populated(CurrentOnlyStore)
    expected = store.records()
    assert len(store.ops) == 6
    assert not hasattr(store, "upto")
    assert retrieve(store, session=session) == expected
    assert {record.value for record in expected} == {"option X", "tool B"}
    assert not any(record.status in ("contested", "declined", "superseded") for record in expected)
    before_fingerprint = store.fingerprint()
    store.ops.clear()
    assert retrieve(store, session=session) == expected
    assert store.fingerprint() == before_fingerprint


class CaptureClient:
    def __init__(self):
        self.requests = []

    def complete(self, **request):
        self.requests.append(deepcopy(request))
        return ModelReply(json.dumps({"status": "abstain", "value": None,
                                      "cited_turn_ids": [], "text": "Offline context capture."}))


@pytest.mark.parametrize("name", ["tracemem-controlled", "tracemem-no-versions"])
@pytest.mark.parametrize("budget_bytes", [256, 12000])
def test_pipeline_passes_only_retained_temporal_context_through_shared_budget(name, budget_bytes):
    client = CaptureClient()
    system = comparison.make_system(
        name, ScenarioMeta(scenario_id="synthetic-temporal", project_id="synthetic-temporal-project"),
        config=ResolverConfig(model="offline-temporal-reader", max_attempts=2),
        client=client, budget_bytes=budget_bytes,
    )
    system.log = populated(OpLog if name == "tracemem-controlled" else CurrentOnlyStore)
    system.turns = {turn: Turn(id=turn, speaker="Analyst", text="RAW_DIALOGUE_MUST_NOT_BE_READ")
                    for turn in system.log.turn_times}
    before = snapshot(system.log)
    answer = system.answer(question())
    payload = json.loads(client.requests[0]["messages"][1]["content"])
    assert answer.status == "abstain"
    assert len(client.requests) == 1
    assert len(payload["context"].encode("utf-8")) <= budget_bytes
    assert "RAW_DIALOGUE_MUST_NOT_BE_READ" not in payload["context"]
    assert payload["allowed_source_turn_ids"] == answer.context_turn_ids
    assert snapshot(system.log) == before
    if name == "tracemem-controlled":
        assert not {"S3-T1", "S3-T2", "S4-T1"}.intersection(answer.context_turn_ids)
        if budget_bytes == 12000:
            assert "option Y [contested]" in payload["context"]
            assert "tool A [active]" in payload["context"]
    else:
        assert "option Y" not in payload["context"]
        assert "tool A" not in payload["context"]
