"""Reference meaning of the four memory operations.

The memory is an append-only list of operations (an operation log). The records a
reader sees, and each record's status, are computed from that list; nothing
stores a status directly, so the status can never disagree with the history.

This module is the single definition of what ADD, KEEP, SUPERSEDE and FLAG do.
The benchmark's expected answers are computed with it, and any production store
must give the same item states on the same operations (tests/test_ops.py).

Record ids are deterministic: ``<item>@<turn id>``. A system therefore numbers
its records exactly as the gold does, which lets the scorer compare them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from tracemem.schema import Candidate, Operation, Record


class InvalidOperation(ValueError):
    """Raised when an operation breaks a rule; the log is left unchanged."""


def record_id(item: str, turn_id: str) -> str:
    return f"{item}@{turn_id}"


@dataclass
class _Rec:
    record_id: str
    item: str
    value: str
    status: str
    source_turn_ids: list[str]
    created_turn: str
    created_at: datetime
    supersedes: list[str] = field(default_factory=list)
    reason: str | None = None
    previous_active: str | None = None  # the record that was active when this one became active
    creating_turns: list[str] = field(default_factory=list)  # source turns of the creating operation
    kept_turns: list[str] = field(default_factory=list)  # turns attached later by KEEP


@dataclass
class ItemState:
    """Everything known about one item at one moment."""

    item: str
    active: Record | None
    proposed: list[Record]
    contested: list[Record]
    history: list[Record]  # superseded and declined records, oldest first
    flagged: bool
    previous_active: Record | None  # the record the active one replaced, if any
    creating_turns: dict[str, list[str]]  # record id -> source turns of its creating operation
    kept_turns: dict[str, list[str]]  # record id -> turns attached by KEEP

    def summary(self) -> tuple:
        """A comparison key that ignores record ids: (active value, flagged, proposed values, contested values)."""
        return (
            self.active.value if self.active else None,
            self.flagged,
            tuple(sorted(r.value for r in self.proposed)),
            tuple(sorted(r.value for r in self.contested)),
        )


class OpLog:
    """An append-only operation log with its current projection.

    ``apply`` validates an operation against the current state and then appends
    it. A rejected operation raises InvalidOperation and changes nothing, so one
    operation is applied completely or not at all.
    """

    def __init__(self, project_id: str, turn_times: dict[str, datetime] | None = None):
        self.project_id = project_id
        self.turn_times = dict(turn_times or {})
        self.speakers: dict[str, str] = {}
        self.ops: list[Operation] = []
        self._records: dict[str, _Rec] = {}
        self._order: list[str] = []
        self._active: dict[str, str] = {}
        self._observed: set[str] = set(self.turn_times)

    # -- observation ---------------------------------------------------------

    def observe_turn(self, turn_id: str, when: datetime, speaker: str = "") -> None:
        """Record that a turn has been seen; operations may cite only observed turns."""
        self.turn_times[turn_id] = when
        self.speakers[turn_id] = speaker
        self._observed.add(turn_id)

    # -- the four operations ---------------------------------------------------

    def apply(self, op: Operation) -> None:
        self._validate(op)
        handler = {"ADD": self._add, "KEEP": self._keep, "SUPERSEDE": self._supersede, "FLAG": self._flag}[op.op]
        handler(op)
        self.ops.append(op)

    def _validate(self, op: Operation) -> None:
        unseen = [t for t in op.source_turn_ids + [op.turn_id] if t not in self._observed]
        if unseen:
            raise InvalidOperation(f"{op.op_id}: cites turns not yet observed: {unseen}")
        for target in op.targets:
            rec = self._records.get(target)
            if rec is None:
                raise InvalidOperation(f"{op.op_id}: unknown target record {target}")
            if rec.item != op.item:
                raise InvalidOperation(f"{op.op_id}: target {target} belongs to item {rec.item}, not {op.item}")
        active = self._active.get(op.item)
        new_id = record_id(op.item, op.turn_id)

        if op.op in ("ADD", "SUPERSEDE", "FLAG"):
            if op.value is None:
                raise InvalidOperation(f"{op.op_id}: {op.op} needs a value")
            if new_id in self._records:
                raise InvalidOperation(f"{op.op_id}: item {op.item} already has a record created at {op.turn_id}")

        if op.op == "ADD":
            if op.add_as is None:
                raise InvalidOperation(f"{op.op_id}: ADD needs add_as (active or proposed)")
            if op.add_as == "active" and active is not None:
                raise InvalidOperation(f"{op.op_id}: {op.item} already has an active record; use SUPERSEDE")
            for target in op.targets:
                rec = self._records[target]
                if op.add_as == "proposed" or rec.status != "proposed" or rec.value != op.value:
                    raise InvalidOperation(f"{op.op_id}: ADD may only promote open proposals with the same value")
        elif op.add_as is not None:
            raise InvalidOperation(f"{op.op_id}: add_as is only valid for ADD")

        if op.op == "KEEP":
            if active is None or op.targets != [active]:
                raise InvalidOperation(f"{op.op_id}: KEEP must target exactly the active record of {op.item}")
            if op.value is not None and op.value != self._records[active].value:
                raise InvalidOperation(f"{op.op_id}: KEEP value differs from the active value; use SUPERSEDE or FLAG")
        if op.op == "SUPERSEDE":
            if not op.targets:
                raise InvalidOperation(f"{op.op_id}: SUPERSEDE needs at least one target")
            if active is not None and active not in op.targets:
                raise InvalidOperation(f"{op.op_id}: SUPERSEDE must target the active record {active}")
            for target in op.targets:
                rec = self._records[target]
                if rec.status not in ("active", "proposed", "contested"):
                    raise InvalidOperation(f"{op.op_id}: target {target} is already {rec.status}")
                if rec.status != "active" and rec.value != op.value:
                    raise InvalidOperation(
                        f"{op.op_id}: SUPERSEDE may close only open proposals or contested claims with the new value"
                    )
            if active is not None and self._records[active].value == op.value:
                raise InvalidOperation(f"{op.op_id}: SUPERSEDE value equals the active value; use KEEP")
        if op.op == "FLAG":
            if active is None:
                raise InvalidOperation(f"{op.op_id}: FLAG needs an active record to dispute")
            if op.targets != [active]:
                raise InvalidOperation(f"{op.op_id}: FLAG must target exactly the active record of {op.item}")
            if self._records[active].value == op.value:
                raise InvalidOperation(f"{op.op_id}: FLAG value equals the active value; use KEEP")

    def _new(self, op: Operation, status: str) -> _Rec:
        rec = _Rec(
            record_id=record_id(op.item, op.turn_id),
            item=op.item,
            value=op.value,
            status=status,
            source_turn_ids=list(op.source_turn_ids),
            created_turn=op.turn_id,
            created_at=self.turn_times[op.turn_id],
            supersedes=list(op.targets),
            reason=op.reason,
            creating_turns=list(op.source_turn_ids),
        )
        self._records[rec.record_id] = rec
        self._order.append(rec.record_id)
        return rec

    def _settle(self, item: str) -> None:
        """The item has a settled value again: every still-open contested claim becomes declined."""
        for rec in self._records.values():
            if rec.item == item and rec.status == "contested":
                rec.status = "declined"

    def _flagged(self, item: str) -> bool:
        """An item is flagged while at least one contested claim about it is open (derived, never stored)."""
        return any(r.item == item and r.status == "contested" for r in self._records.values())

    def _add(self, op: Operation) -> None:
        rec = self._new(op, op.add_as)
        for target in op.targets:
            self._records[target].status = "superseded"
        if op.add_as == "active":
            self._active[op.item] = rec.record_id
            self._settle(op.item)

    def _keep(self, op: Operation) -> None:
        rec = self._records[op.targets[0]]
        for turn in op.source_turn_ids:
            if turn not in rec.source_turn_ids:
                rec.source_turn_ids.append(turn)
                rec.kept_turns.append(turn)
        self._settle(op.item)

    def _supersede(self, op: Operation) -> None:
        previous = self._active.get(op.item)
        rec = self._new(op, "active")
        rec.previous_active = previous
        for target in op.targets:
            self._records[target].status = "superseded"
        self._active[op.item] = rec.record_id
        self._settle(op.item)

    def _flag(self, op: Operation) -> None:
        self._new(op, "contested")

    # -- reading -----------------------------------------------------------------

    def _public(self, rec: _Rec) -> Record:
        return Record(
            record_id=rec.record_id,
            project_id=self.project_id,
            item=rec.item,
            value=rec.value,
            status=rec.status,
            source_turn_ids=list(rec.source_turn_ids),
            speakers=[self.speakers.get(t, "") for t in rec.source_turn_ids],
            created_turn=rec.created_turn,
            created_at=rec.created_at,
            supersedes=list(rec.supersedes),
            reason=rec.reason,
        )

    def records(self, item: str | None = None) -> list[Record]:
        return [self._public(self._records[i]) for i in self._order if item is None or self._records[i].item == item]

    def items(self) -> list[str]:
        seen: list[str] = []
        for record_key in self._order:
            item = self._records[record_key].item
            if item not in seen:
                seen.append(item)
        return seen

    def item_state(self, item: str) -> ItemState:
        recs = [self._records[i] for i in self._order if self._records[i].item == item]
        active_id = self._active.get(item)
        active = self._records[active_id] if active_id else None
        previous = None
        if active is not None:
            # Walk back past predecessors with the same value, so "previous" always names a different value.
            candidate = self._records.get(active.previous_active) if active.previous_active else None
            while candidate is not None and candidate.value == active.value:
                candidate = self._records.get(candidate.previous_active) if candidate.previous_active else None
            previous = candidate
        return ItemState(
            item=item,
            active=self._public(active) if active else None,
            proposed=[self._public(r) for r in recs if r.status == "proposed"],
            contested=[self._public(r) for r in recs if r.status == "contested"],
            history=[self._public(r) for r in recs if r.status in ("superseded", "declined")],
            flagged=self._flagged(item),
            previous_active=self._public(previous) if previous else None,
            creating_turns={r.record_id: list(r.creating_turns) for r in recs},
            kept_turns={r.record_id: list(r.kept_turns) for r in recs},
        )

    def fingerprint(self) -> str:
        """Changes whenever the log changes; the harness uses it to prove that answering is read-only."""
        return f"{len(self.ops)}:{len(self._observed)}"

    def upto(self, last_turn_id: str) -> OpLog:
        """An independent log holding only the operations issued at or before ``last_turn_id``."""
        cutoff = self.turn_times[last_turn_id]
        clone = OpLog(self.project_id, {t: w for t, w in self.turn_times.items() if w <= cutoff})
        clone.speakers = {t: s for t, s in self.speakers.items() if t in clone.turn_times}
        for op in self.ops:
            if self.turn_times[op.turn_id] <= cutoff:
                clone.apply(op)
        return clone

    def copy(self) -> OpLog:
        """An independent log with the same history, replayed from the operations."""
        clone = OpLog(self.project_id, self.turn_times)
        clone.speakers = dict(self.speakers)
        for op in self.ops:
            clone.apply(op)
        return clone


def flat_records(project_id: str, candidates: list[Candidate], turn_times: dict[str, datetime]) -> list[Record]:
    """One record per candidate, with no status: the store of every system that has no resolver.

    Similarity, similarity + recency and Timeline read these records; TraceMem
    reads the OpLog projection of the same candidates. The records carry the same
    values, turns and speakers, so the systems differ only in status and filtering.
    """
    records = []
    seen: dict[str, int] = {}
    for cand in candidates:
        turn = cand.source_turn_ids[0]
        rid = record_id(cand.item, turn)
        seen[rid] = seen.get(rid, 0) + 1
        if seen[rid] > 1:
            rid = f"{rid}#{seen[rid]}"
        records.append(
            Record(
                record_id=rid,
                project_id=project_id,
                item=cand.item,
                value=cand.value,
                status=None,
                source_turn_ids=list(cand.source_turn_ids),
                speakers=[cand.speaker],
                created_turn=turn,
                created_at=turn_times[turn],
            )
        )
    return records
