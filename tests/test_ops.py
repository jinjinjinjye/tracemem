"""The four memory operations (ADD, KEEP, SUPERSEDE, FLAG) and the statuses derived from them.

Every log here is built by hand, one operation at a time, so each test states a
rule of ops.py directly instead of going through a scenario.
"""

from __future__ import annotations

import pytest

from support import turn_clock
from tracemem.ops import InvalidOperation, OpLog, flat_records, record_id
from tracemem.schema import Candidate, Operation

ITEM = "model.x"
OTHER = "model.y"
UNDECIDED = "model.z"
TURNS = ("S1-T1", "S1-T2", "S1-T3", "S1-T4", "S1-T5", "S1-T6")


def make_log(*turns: str, observe: tuple[str, ...] = TURNS) -> OpLog:
    """A log that has observed the given turns (all of TURNS by default)."""
    log = OpLog("p")
    for turn, when in turn_clock(*(turns or observe)).items():
        log.observe_turn(turn, when, speaker="Ana" if turn.endswith(("1", "3", "5")) else "Ben")
    return log


def op(kind: str, turn: str, value: str | None = None, *, targets=(), add_as=None, item: str = ITEM,
       sources=None) -> Operation:
    return Operation(op_id=f"{kind}:{item}@{turn}", op=kind, turn_id=turn, item=item, value=value, add_as=add_as,
                     targets=list(targets), source_turn_ids=list(sources or [turn]))


def rid(turn: str, item: str = ITEM) -> str:
    return record_id(item, turn)


def snapshot(log: OpLog):
    """Everything a reader can see, to prove that a rejected operation changed nothing."""
    return (
        list(log.ops),
        [r.model_dump() for r in log.records()],
        {item: log.item_state(item).summary() for item in log.items()},
        log.fingerprint(),
    )


def statuses(log: OpLog, item: str = ITEM) -> dict[str, str]:
    return {r.record_id: r.status for r in log.records(item)}


# -- a log to break rules against --------------------------------------------------------------


def log_with_active_and_proposal() -> OpLog:
    """model.x: A active (S1-T1), B proposed (S1-T2); model.y: C active (S1-T3); model.z: only E proposed (S1-T5)."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("ADD", "S1-T2", "B", add_as="proposed"))
    log.apply(op("ADD", "S1-T3", "C", add_as="active", item=OTHER))
    log.apply(op("ADD", "S1-T5", "E", add_as="proposed", item=UNDECIDED))
    return log


REJECTED = {
    # rule: (the operation that breaks it, against log_with_active_and_proposal(); the check that must fire)
    "ADD active while an active record exists": (
        op("ADD", "S1-T4", "D", add_as="active"), "already has an active record"),
    "ADD without add_as": (op("ADD", "S1-T4", "D"), "ADD needs add_as"),
    "ADD proposed that also closes records": (
        op("ADD", "S1-T4", "B", add_as="proposed", targets=[rid("S1-T2")]), "may only promote open proposals"),
    "ADD promoting a proposal with a different value": (
        op("ADD", "S1-T6", "F", add_as="active", targets=[rid("S1-T5", UNDECIDED)], item=UNDECIDED),
        "may only promote open proposals with the same value"),
    "add_as on an operation that is not ADD": (
        op("SUPERSEDE", "S1-T4", "D", targets=[rid("S1-T1")], add_as="active"), "add_as is only valid for ADD"),
    "SUPERSEDE without the active target": (
        op("SUPERSEDE", "S1-T4", "B", targets=[rid("S1-T2")]), "must target the active record"),
    "SUPERSEDE with no target at all": (op("SUPERSEDE", "S1-T4", "D"), "needs at least one target"),
    "SUPERSEDE closing a proposal with a different value": (
        op("SUPERSEDE", "S1-T4", "D", targets=[rid("S1-T1"), rid("S1-T2")]), "may close only open proposals"),
    "SUPERSEDE to the value that is already active": (
        op("SUPERSEDE", "S1-T4", "A", targets=[rid("S1-T1")]), "equals the active value; use KEEP"),
    "SUPERSEDE without a value": (op("SUPERSEDE", "S1-T4", None, targets=[rid("S1-T1")]), "needs a value"),
    "target that belongs to another item": (
        op("SUPERSEDE", "S1-T4", "D", targets=[rid("S1-T3", OTHER)]), "belongs to item model.y"),
    "target that does not exist": (op("SUPERSEDE", "S1-T4", "D", targets=[rid("S1-T6")]), "unknown target"),
    "KEEP on a record that is not the active one": (
        op("KEEP", "S1-T4", "B", targets=[rid("S1-T2")]), "KEEP must target exactly the active record"),
    "KEEP with no target": (op("KEEP", "S1-T4", "A"), "KEEP must target exactly the active record"),
    "KEEP with a value different from the active value": (
        op("KEEP", "S1-T4", "D", targets=[rid("S1-T1")]), "KEEP value differs"),
    "KEEP on an item with no active record": (
        op("KEEP", "S1-T6", "E", targets=[rid("S1-T5", UNDECIDED)], item=UNDECIDED),
        "KEEP must target exactly the active record"),
    "FLAG without an active record": (
        op("FLAG", "S1-T6", "F", targets=[rid("S1-T5", UNDECIDED)], item=UNDECIDED), "FLAG needs an active record"),
    "FLAG with the active value": (op("FLAG", "S1-T4", "A", targets=[rid("S1-T1")]), "FLAG value equals"),
    "FLAG that does not target the active record": (
        op("FLAG", "S1-T4", "D", targets=[rid("S1-T2")]), "FLAG must target exactly the active record"),
    "second record on the same item at the same turn": (
        op("ADD", "S1-T2", "E", add_as="proposed"), "already has a record created at S1-T2"),
    "source turn not observed yet": (
        op("SUPERSEDE", "S1-T4", "D", targets=[rid("S1-T1")], sources=["S1-T4", "S2-T1"]), "not yet observed"),
    "issuing turn not observed yet": (op("SUPERSEDE", "S2-T1", "D", targets=[rid("S1-T1")]), "not yet observed"),
}


@pytest.mark.parametrize("rule", list(REJECTED))
def test_each_rule_rejects_its_case_and_leaves_the_log_unchanged(rule):
    """A rejected operation raises InvalidOperation from its own check and changes nothing:
    records, statuses, the operation list and the fingerprint all stay as they were."""
    log = log_with_active_and_proposal()
    operation, message = REJECTED[rule]
    before = snapshot(log)
    with pytest.raises(InvalidOperation, match=message):
        log.apply(operation)
    assert snapshot(log) == before


def test_keep_without_an_active_record_is_rejected():
    log = make_log()
    log.apply(op("ADD", "S1-T1", "B", add_as="proposed"))
    with pytest.raises(InvalidOperation, match="KEEP must target exactly the active record"):
        log.apply(op("KEEP", "S1-T2", "B", targets=[rid("S1-T1")]))


def test_superseded_record_cannot_be_targeted_again():
    """Once replaced, a record is closed: a second SUPERSEDE naming it is rejected."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("SUPERSEDE", "S1-T2", "B", targets=[rid("S1-T1")]))
    before = snapshot(log)
    with pytest.raises(InvalidOperation):
        log.apply(op("SUPERSEDE", "S1-T3", "C", targets=[rid("S1-T2"), rid("S1-T1")]))
    assert snapshot(log) == before


def test_turns_given_at_construction_count_as_observed():
    log = OpLog("p", turn_clock("S1-T1"))
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    assert log.item_state(ITEM).active.value == "A"


# -- derived statuses ------------------------------------------------------------------------


def test_add_and_supersede_basic_lifecycle():
    """ADD makes a record active; SUPERSEDE makes the new one active and the old one superseded."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("SUPERSEDE", "S1-T2", "B", targets=[rid("S1-T1")]))
    assert statuses(log) == {rid("S1-T1"): "superseded", rid("S1-T2"): "active"}
    state = log.item_state(ITEM)
    assert state.active.value == "B"
    assert state.active.supersedes == [rid("S1-T1")]
    assert [r.value for r in state.history] == ["A"]
    assert state.previous_active.record_id == rid("S1-T1")
    assert state.flagged is False


def test_flag_marks_the_item_flagged_while_a_claim_is_open():
    """FLAG adds a contested record and leaves the active one active; the item counts as flagged."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("FLAG", "S1-T2", "B", targets=[rid("S1-T1")]))
    assert statuses(log) == {rid("S1-T1"): "active", rid("S1-T2"): "contested"}
    state = log.item_state(ITEM)
    assert state.flagged is True
    assert [r.value for r in state.contested] == ["B"]
    assert state.summary() == ("A", True, (), ("B",))


def test_contest_then_revise_to_a_third_value_declines_the_claim():
    """A active, B contested, then SUPERSEDE to C: B becomes declined (not superseded), and the item is no longer flagged."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("FLAG", "S1-T2", "B", targets=[rid("S1-T1")]))
    log.apply(op("SUPERSEDE", "S1-T3", "C", targets=[rid("S1-T1")]))
    assert statuses(log) == {rid("S1-T1"): "superseded", rid("S1-T2"): "declined", rid("S1-T3"): "active"}
    state = log.item_state(ITEM)
    assert state.flagged is False
    assert state.contested == []
    assert [(r.value, r.status) for r in state.history] == [("A", "superseded"), ("B", "declined")]


def test_contest_then_revise_to_the_contested_value_closes_it_as_superseded():
    """If the team adopts the disputed value, SUPERSEDE may close the contested record along with the active one."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("FLAG", "S1-T2", "B", targets=[rid("S1-T1")]))
    log.apply(op("SUPERSEDE", "S1-T3", "B", targets=[rid("S1-T1"), rid("S1-T2")]))
    assert statuses(log) == {rid("S1-T1"): "superseded", rid("S1-T2"): "superseded", rid("S1-T3"): "active"}
    assert log.item_state(ITEM).flagged is False


def test_contest_then_restate_declines_the_claim_and_keeps_the_support():
    """A active, B contested, then KEEP A: B becomes declined, A stays active and gains the restating turn."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("FLAG", "S1-T2", "B", targets=[rid("S1-T1")]))
    log.apply(op("KEEP", "S1-T3", "A", targets=[rid("S1-T1")]))
    assert statuses(log) == {rid("S1-T1"): "active", rid("S1-T2"): "declined"}
    state = log.item_state(ITEM)
    assert state.flagged is False
    assert state.active.source_turn_ids == ["S1-T1", "S1-T3"]
    assert state.creating_turns[rid("S1-T1")] == ["S1-T1"]
    assert state.kept_turns[rid("S1-T1")] == ["S1-T3"]


def test_two_open_claims_stay_flagged_until_settled():
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("FLAG", "S1-T2", "B", targets=[rid("S1-T1")]))
    log.apply(op("FLAG", "S1-T3", "C", targets=[rid("S1-T1")]))
    assert log.item_state(ITEM).summary() == ("A", True, (), ("B", "C"))
    log.apply(op("KEEP", "S1-T4", "A", targets=[rid("S1-T1")]))
    assert log.item_state(ITEM).summary() == ("A", False, (), ())


def test_accept_with_no_active_value_promotes_the_proposal():
    """A suggestion accepted before anything was decided: ADD active closing the proposal, which becomes superseded."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "B", add_as="proposed"))
    log.apply(op("ADD", "S1-T2", "B", add_as="active", targets=[rid("S1-T1")], sources=["S1-T2", "S1-T1"]))
    assert statuses(log) == {rid("S1-T1"): "superseded", rid("S1-T2"): "active"}
    state = log.item_state(ITEM)
    assert state.proposed == []
    assert state.active.source_turn_ids == ["S1-T2", "S1-T1"]
    assert state.previous_active is None, "a promoted proposal was never the active value, so it is not 'previous'"


def test_proposal_survives_an_unrelated_revision():
    """SUPERSEDE to C leaves an open proposal B untouched; only same-value proposals are closed."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("ADD", "S1-T2", "B", add_as="proposed"))
    log.apply(op("SUPERSEDE", "S1-T3", "C", targets=[rid("S1-T1")]))
    assert statuses(log) == {rid("S1-T1"): "superseded", rid("S1-T2"): "proposed", rid("S1-T3"): "active"}


def test_revert_a_b_a_names_b_as_previous():
    """A -> B -> A: the current A is a new record, the first A is history, and 'previous' is B, not the first A."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("SUPERSEDE", "S1-T2", "B", targets=[rid("S1-T1")]))
    log.apply(op("SUPERSEDE", "S1-T3", "A", targets=[rid("S1-T2")]))
    state = log.item_state(ITEM)
    assert state.active.record_id == rid("S1-T3")
    assert state.previous_active.record_id == rid("S1-T2")
    assert state.previous_active.value == "B"
    assert [(r.record_id, r.status) for r in state.history] == [
        (rid("S1-T1"), "superseded"), (rid("S1-T2"), "superseded")]


def test_previous_active_walks_back_one_change_at_a_time():
    """A -> B -> A -> C: previous of C is the second A; the walk-back never returns the current value."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("SUPERSEDE", "S1-T2", "B", targets=[rid("S1-T1")]))
    log.apply(op("SUPERSEDE", "S1-T3", "A", targets=[rid("S1-T2")]))
    log.apply(op("SUPERSEDE", "S1-T4", "C", targets=[rid("S1-T3")]))
    state = log.item_state(ITEM)
    assert state.previous_active.record_id == rid("S1-T3")
    assert state.previous_active.value == "A" != state.active.value


def test_records_carry_speakers_and_times_of_their_turns():
    log = make_log()
    log.apply(op("ADD", "S1-T2", "A", add_as="active"))
    record = log.records(ITEM)[0]
    assert record.speakers == ["Ben"]
    assert record.created_at == turn_clock(*TURNS)["S1-T2"]
    assert record.project_id == "p"


def test_items_are_listed_in_order_of_first_record():
    log = log_with_active_and_proposal()
    assert log.items() == [ITEM, OTHER, UNDECIDED]
    assert [r.item for r in log.records()] == [ITEM, ITEM, OTHER, UNDECIDED]
    assert [r.item for r in log.records(OTHER)] == [OTHER]


# -- snapshots and copies ------------------------------------------------------------------


def build_history() -> OpLog:
    """A at T1, B proposed at T2, FLAG C at T3, SUPERSEDE to B at T4 (closing the proposal), KEEP at T5."""
    log = make_log()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    log.apply(op("ADD", "S1-T2", "B", add_as="proposed"))
    log.apply(op("FLAG", "S1-T3", "C", targets=[rid("S1-T1")]))
    log.apply(op("SUPERSEDE", "S1-T4", "B", targets=[rid("S1-T1"), rid("S1-T2")]))
    log.apply(op("KEEP", "S1-T5", "B", targets=[rid("S1-T4")]))
    return log


def test_upto_is_the_state_as_it_stood_at_that_turn():
    """upto(T3) holds only operations issued at or before T3, with the statuses they had then."""
    full = build_history()
    early = full.upto("S1-T3")
    assert len(early.ops) == 3
    assert early.item_state(ITEM).summary() == ("A", True, ("B",), ("C",))
    assert statuses(early) == {rid("S1-T1"): "active", rid("S1-T2"): "proposed", rid("S1-T3"): "contested"}
    # The full log is untouched by taking a snapshot.
    assert full.item_state(ITEM).summary() == ("B", False, (), ())
    assert statuses(full) == {rid("S1-T1"): "superseded", rid("S1-T2"): "superseded", rid("S1-T3"): "declined",
                              rid("S1-T4"): "active"}


def test_upto_forgets_later_turns_and_is_independent():
    """The snapshot has not observed later turns, and changing it does not change the original."""
    full = build_history()
    early = full.upto("S1-T3")
    assert set(early.turn_times) == {"S1-T1", "S1-T2", "S1-T3"}
    with pytest.raises(InvalidOperation, match="not yet observed"):
        early.apply(op("KEEP", "S1-T4", "A", targets=[rid("S1-T1")]))
    early.apply(op("KEEP", "S1-T3", "A", targets=[rid("S1-T1")], sources=["S1-T2"]))
    assert early.item_state(ITEM).flagged is False
    assert len(full.ops) == 5


def test_upto_the_last_turn_equals_the_full_log():
    full = build_history()
    last = full.upto("S1-T6")
    assert [r.model_dump() for r in last.records()] == [r.model_dump() for r in full.records()]


def test_copy_is_independent():
    full = build_history()
    clone = full.copy()
    clone.apply(op("SUPERSEDE", "S1-T6", "D", targets=[rid("S1-T4")]))
    assert full.item_state(ITEM).active.value == "B"
    assert clone.item_state(ITEM).active.value == "D"


def test_fingerprint_changes_with_operations_and_observations():
    log = make_log("S1-T1")
    first = log.fingerprint()
    log.apply(op("ADD", "S1-T1", "A", add_as="active"))
    second = log.fingerprint()
    log.observe_turn("S1-T2", turn_clock("S1-T1", "S1-T2")["S1-T2"])
    assert len({first, second, log.fingerprint()}) == 3


# -- systems without a resolver ----------------------------------------------------------------


def test_flat_records_have_no_status_and_one_record_per_candidate():
    """flat_records keeps every candidate, including repeats and contradictions, with status None."""
    times = turn_clock("S1-T1", "S1-T2")
    candidates = [
        Candidate(candidate_id=rid("S1-T1"), project_id="p", item=ITEM, value="A", source_turn_ids=["S1-T1"],
                  speaker="Ana", text="We use A."),
        Candidate(candidate_id=rid("S1-T2"), project_id="p", item=ITEM, value="B", source_turn_ids=["S1-T2"],
                  speaker="Ben", text="No, B."),
    ]
    records = flat_records("p", candidates, times)
    assert [(r.record_id, r.value, r.status, r.speakers) for r in records] == [
        (rid("S1-T1"), "A", None, ["Ana"]), (rid("S1-T2"), "B", None, ["Ben"])]
    assert records[1].created_at == times["S1-T2"]


def test_flat_records_keep_ids_unique_when_one_turn_yields_two_candidates():
    """An over-extracting system may produce two candidates for one item from one turn; both are kept."""
    times = turn_clock("S1-T1")
    candidates = [
        Candidate(candidate_id=f"c{i}", project_id="p", item=ITEM, value=value, source_turn_ids=["S1-T1"],
                  speaker="Ana", text="A or B?")
        for i, value in enumerate(["A", "B"])
    ]
    records = flat_records("p", candidates, times)
    assert [(r.record_id, r.value) for r in records] == [(rid("S1-T1"), "A"), (rid("S1-T1") + "#2", "B")]
