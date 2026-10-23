"""Current-state ablation: retain open memories and provenance, discard versions.

The write decisions and reference operation semantics stay unchanged. An ephemeral
OpLog validates each write against the retained state; it is discarded immediately.
The separate ``ops`` audit supports evaluation and is never used to serve memory.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from tracemem.ops import InvalidOperation, ItemState, OpLog, record_id
from tracemem.schema import Operation, Record


class CurrentOnlyStore:
    """An OpLog-shaped store without closed records, version links or historical reads.

    ``turn_times`` and speaker names retain citation metadata, not dialogue text.
    Previously created record IDs prevent duplicate creation after a version is
    dropped. Neither that identity set nor the audit log stores readable memory
    used by matching, retrieval or answering.
    """

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.turn_times: dict[str, datetime] = {}
        self.speakers: dict[str, str] = {}
        self.ops: list[Operation] = []
        self._live: dict[str, Record] = {}
        self._created_ids: set[str] = set()
        self._creating_turns: dict[str, list[str]] = {}
        self._kept_turns: dict[str, list[str]] = {}

    def observe_turn(self, turn_id: str, when: datetime, speaker: str = "") -> None:
        self.turn_times[turn_id] = when
        self.speakers[turn_id] = speaker

    def _current_log(self) -> OpLog:
        """Reconstruct only open state through public OpLog operations, never audit replay."""
        log = OpLog(self.project_id, self.turn_times)
        log.speakers = dict(self.speakers)
        # A repeated observation can change the metadata clock, but it must not
        # rewrite an existing memory's original creation timestamp.
        for record in self._live.values():
            log.turn_times[record.created_turn] = record.created_at
        for item in self.items():
            records = [record for record in self._live.values() if record.item == item]
            active = next((record for record in records if record.status == "active"), None)
            # Active first makes contested records replayable even if their
            # creation times precede an unrelated item's current active record.
            for status in ("active", "proposed", "contested"):
                for record in records:
                    if record.status != status:
                        continue
                    seed = Operation(
                        op_id=f"seed:{record.record_id}", op="FLAG" if status == "contested" else "ADD",
                        turn_id=record.created_turn, item=item, value=record.value,
                        add_as=status if status in ("active", "proposed") else None,
                        targets=[active.record_id] if status == "contested" else [],
                        source_turn_ids=list(self._creating_turns[record.record_id]), reason=record.reason,
                    )
                    log.apply(seed)
                    for index, source in enumerate(self._kept_turns[record.record_id]):
                        log.apply(Operation(op_id=f"seed-keep:{record.record_id}:{index}", op="KEEP",
                                            turn_id=source, item=item, value=record.value,
                                            targets=[record.record_id], source_turn_ids=[source]))
        log.turn_times = dict(self.turn_times)
        return log

    def apply(self, op: Operation) -> None:
        creates_record = op.op in ("ADD", "SUPERSEDE", "FLAG")
        new_id = record_id(op.item, op.turn_id)
        if creates_record and new_id in self._created_ids:
            raise InvalidOperation(f"{op.op_id}: item {op.item} already had a record created at {op.turn_id}")
        transient = self._current_log()
        transient.apply(op)
        projected = {
            record.record_id: record.model_copy(update={"supersedes": []}, deep=True)
            for record in transient.records() if record.status in ("active", "proposed", "contested")
        }
        # Reconstruction groups by status. Preserve the actual creation order of
        # retained records and append only the newly created record, if any.
        ordered_ids = [rid for rid in self._live if rid in projected]
        ordered_ids.extend(rid for rid in projected if rid not in self._live)
        states = {item: transient.item_state(item) for item in transient.items()}
        self._live = {rid: projected[rid] for rid in ordered_ids}
        self._creating_turns = {rid: list(states[record.item].creating_turns[rid])
                                for rid, record in self._live.items()}
        self._kept_turns = {rid: list(states[record.item].kept_turns[rid])
                            for rid, record in self._live.items()}
        if creates_record:
            self._created_ids.add(new_id)
        self.ops.append(op.model_copy(deep=True))

    def records(self, item: str | None = None) -> list[Record]:
        return [record.model_copy(update={
            "speakers": [self.speakers.get(turn, "") for turn in record.source_turn_ids],
        }, deep=True) for record in self._live.values() if item is None or record.item == item]

    def items(self) -> list[str]:
        return list(dict.fromkeys(record.item for record in self._live.values()))

    def item_state(self, item: str) -> ItemState:
        records = self.records(item)
        contested = [record for record in records if record.status == "contested"]
        return ItemState(
            item=item, active=next((record for record in records if record.status == "active"), None),
            proposed=[record for record in records if record.status == "proposed"],
            contested=contested, history=[], flagged=bool(contested), previous_active=None,
            creating_turns={record.record_id: list(self._creating_turns[record.record_id]) for record in records},
            kept_turns={record.record_id: list(self._kept_turns[record.record_id]) for record in records},
        )

    def fingerprint(self) -> str:
        """Hash memory and citation metadata; audit-log changes cannot affect reads."""
        payload = {
            "records": [record.model_dump(mode="json") for record in self.records()],
            "turn_times": {turn: when.isoformat() for turn, when in self.turn_times.items()},
            "speakers": self.speakers, "created_ids": sorted(self._created_ids),
            "creating_turns": self._creating_turns, "kept_turns": self._kept_turns,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
