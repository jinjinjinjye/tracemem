"""The five component interfaces, and gold stand-ins for each.

Each owner implements one interface. Until the upstream stage exists, an owner
can build against the gold stand-in, which returns what a perfect upstream
stage would. Replacing one stand-in at a time shows which stage a score change
comes from (docs/interfaces.md).

The stand-ins read the benchmark's gold labels, so a system built from them is
registered with ``uses_gold`` and reported as a probe, never as a baseline.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from tracemem.bench.replay import GoldTimeline
from tracemem.ops import ItemState
from tracemem.schema import Answer, Candidate, Operation, Record, ScenarioMeta, SystemQuestion, Turn, session_of


class StoreView(Protocol):
    """Read-only access to a memory store. ``tracemem.ops.OpLog`` implements it.

    ``upto`` returns the store as it stood after a given turn, which a retriever
    needs for "as of session S" questions; ``turn_times`` maps every observed
    turn to its time.
    """

    turn_times: dict[str, datetime]

    def records(self, item: str | None = None) -> list[Record]: ...

    def items(self) -> list[str]: ...

    def item_state(self, item: str) -> ItemState: ...

    def upto(self, last_turn_id: str) -> StoreView: ...


class Extractor(Protocol):
    """Turn -> zero or more candidates. Reads no store, so every system receives identical candidates."""

    def extract(self, turn: Turn, when: datetime, meta: ScenarioMeta) -> list[Candidate]: ...


class Matcher(Protocol):
    """Candidate -> the stored records it may relate to.

    It should search with the same scoring function the retriever uses, so that
    write-time matching and read-time retrieval cannot drift apart.
    """

    def match(self, candidate: Candidate, store: StoreView) -> list[Record]: ...


class Resolver(Protocol):
    """Candidate + related records -> one operation: ADD, KEEP, SUPERSEDE or FLAG."""

    def resolve(self, candidate: Candidate, related: list[Record]) -> Operation: ...


class Retriever(Protocol):
    """Question -> the records to show the answer model, within a token budget."""

    def retrieve(self, question: SystemQuestion, store: StoreView, budget_tokens: int) -> list[Record]: ...


class Answerer(Protocol):
    """Question + records (+ only the turns those records cite) -> a structured answer."""

    def answer(self, question: SystemQuestion, records: list[Record], turns: dict[str, Turn]) -> Answer: ...


# ---------------------------------------------------------------------------
# Gold stand-ins
# ---------------------------------------------------------------------------


class GoldExtractor:
    """Returns the replay's gold candidates for the turn."""

    def __init__(self, gold: GoldTimeline):
        self.gold = gold

    def extract(self, turn: Turn, when: datetime, meta: ScenarioMeta) -> list[Candidate]:
        return list(self.gold.candidates_by_turn.get(turn.id, []))


class GoldMatcher:
    """Returns every stored record of the candidate's item (the gold item key is trusted)."""

    def match(self, candidate: Candidate, store: StoreView) -> list[Record]:
        return store.records(candidate.item)


class GoldResolver:
    """Returns the gold operation for the candidate, looked up by candidate id."""

    def __init__(self, gold: GoldTimeline):
        self.ops = {op.candidate_id: op for ops in gold.ops_by_turn.values() for op in ops}

    def resolve(self, candidate: Candidate, related: list[Record]) -> Operation:
        """The gold operation; a candidate the gold does not contain (over-extraction) is stored as a proposal."""
        if candidate.candidate_id in self.ops:
            return self.ops[candidate.candidate_id]
        turn = candidate.source_turn_ids[0]
        return Operation(op_id=f"extra:{candidate.candidate_id}", op="ADD", add_as="proposed", turn_id=turn,
                         item=candidate.item, value=candidate.value, source_turn_ids=[turn],
                         rationale="not in the gold: kept as a proposal", candidate_id=candidate.candidate_id)


class GoldRetriever:
    """Returns every record of the question's gold item, as the store stood at the question's window.

    It maps the opaque question id back to the gold item, which no real retriever can do.
    """

    def __init__(self, gold: GoldTimeline):
        self.items = {gold.public_id(q): q.item for q in gold.questions}
        self.sessions = [s.id for s in gold.scenario.sessions]

    def retrieve(self, question: SystemQuestion, store, budget_tokens: int) -> list[Record]:
        view = store
        if question.kind == "as_of" and question.session:
            allowed = set(self.sessions[: self.sessions.index(question.session) + 1])
            turns = [t for t in store.turn_times if session_of(t) in allowed]
            if not turns:
                return []
            view = store.upto(max(turns, key=lambda t: store.turn_times[t]))
        return view.records(self.items[question.question_id])


class RuleAnswerer:
    """Deterministic answers from record statuses; proves the wiring, not a real answer model.

    current / as_of: a contested record means conflict; else the active value; else none.
    previous: the value the active record replaced, skipping same-value records.
    """

    def answer(self, question: SystemQuestion, records: list[Record], turns: dict[str, Turn]) -> Answer:
        active = [r for r in records if r.status == "active"]
        contested = [r for r in records if r.status == "contested"]
        if question.kind == "previous":
            if not active:
                return Answer(status="none")
            current = active[0]
            by_id = {r.record_id: r for r in records}
            earlier = [by_id[i] for i in current.supersedes if i in by_id and by_id[i].value != current.value]
            if not earlier:
                return Answer(status="none")
            previous = max(earlier, key=lambda r: r.created_at)
            cited = sorted(set(previous.source_turn_ids) | {current.created_turn})
            return Answer(status="answer", value=previous.value, cited_turn_ids=cited, context_turn_ids=cited)
        if contested and active:
            cited = sorted({t for r in active + contested for t in r.source_turn_ids})
            return Answer(status="conflict", cited_turn_ids=cited, context_turn_ids=cited)
        if active:
            cited = sorted(active[0].source_turn_ids)
            return Answer(status="answer", value=active[0].value, cited_turn_ids=cited, context_turn_ids=cited)
        cited = sorted({t for r in records if r.status == "proposed" for t in r.source_turn_ids})
        return Answer(status="none", cited_turn_ids=cited, context_turn_ids=cited)


# ---------------------------------------------------------------------------
# The shared record renderer
# ---------------------------------------------------------------------------


def render_records(records: list[Record], turns: dict[str, Turn], show_status: bool) -> str:
    """Turn records into the text an answer model reads, identically for every record-based system.

    Every system uses this one function, so that systems differ only in which
    records they select and whether ``show_status`` is on. Records appear in
    time order; each line gives the turn id, speaker, item, value, optional
    status, and the quoted text of the record's first source turn.
    """
    lines = []
    for record in sorted(records, key=lambda r: (r.created_at, r.record_id)):
        turn = turns.get(record.created_turn)
        quote = f' "{turn.text}"' if turn else ""
        speaker = record.speakers[0] if record.speakers else (turn.speaker if turn else "")
        status = f" [{record.status}]" if show_status and record.status else ""
        lines.append(f"{record.created_turn} {speaker}: {record.item} = {record.value}{status}{quote}")
    return "\n".join(lines)
