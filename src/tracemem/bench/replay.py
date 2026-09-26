"""Compute the gold standard of a scenario by replaying its script.

Authors label what each turn *does* (an act such as ``decide`` or ``suggest``).
This module turns those acts into the memory operations a perfect system would
issue, applies them with the reference semantics in ``tracemem.ops``, and reads
off the expected answer to every checkpoint question. Nobody writes an expected
answer by hand.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime

from tracemem.bench.load import candidate_bearing, expand_questions
from tracemem.ops import OpLog, record_id
from tracemem.schema import (
    Candidate,
    ExpectedAnswer,
    Operation,
    Question,
    Scenario,
    ScriptEvent,
    PROGRESS_ALIASES,
    normalise,
    session_of,
    turn_time,
)


class ScriptError(ValueError):
    """The script asks for something the rules do not allow (the validator reports these)."""


def event_value(event: ScriptEvent, suggestions: dict[tuple[str, str], str]) -> str | None:
    """The value an event is about: tasks use their progress, `accept` takes the accepted suggestion's value."""
    if event.act == "task_open":
        return "open"
    if event.act == "task_progress":
        return event.progress
    if event.act == "accept":
        return suggestions.get((event.item, event.accepts or ""))
    return event.value


@dataclass
class GoldTimeline:
    scenario: Scenario
    turn_times: dict[str, datetime]
    turn_order: list[str]
    events_by_turn: dict[str, list[ScriptEvent]]
    candidates_by_turn: dict[str, list[Candidate]]
    ops_by_turn: dict[str, list[Operation]]
    log_after_session: dict[str, OpLog]
    questions: list[Question]
    expected: dict[str, ExpectedAnswer] = field(default_factory=dict)
    # A per-replay secret that makes public question ids unguessable; only gold-reading systems hold it.
    salt: str = field(default_factory=lambda: secrets.token_hex(8))

    def public_id(self, question: Question) -> str:
        return question.for_system(self.salt).question_id

    def gold_op_for(self, candidate_id: str) -> Operation | None:
        for ops in self.ops_by_turn.values():
            for op in ops:
                if op.candidate_id == candidate_id:
                    return op
        return None


class GoldDeriver:
    """Derives gold candidates and operations turn by turn, never looking ahead."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.log = OpLog(scenario.project_id)
        self.events_by_turn: dict[str, list[ScriptEvent]] = {}
        for event in scenario.script:
            self.events_by_turn.setdefault(event.turn, []).append(event)
        self.text = {turn.id: turn.text for turn in scenario.turns()}
        self.speaker = {turn.id: turn.speaker for turn in scenario.turns()}
        self.suggestions: dict[tuple[str, str], str] = {}  # (item, turn) -> suggested value

    def observe(self, turn_id: str, when: datetime) -> tuple[list[Candidate], list[Operation]]:
        self.log.observe_turn(turn_id, when, self.speaker.get(turn_id, ""))
        candidates: list[Candidate] = []
        ops: list[Operation] = []
        for event in self.events_by_turn.get(turn_id, []):
            if not candidate_bearing(event):
                continue
            op = self._operation(event)
            self.log.apply(op)
            # A gold candidate cites only the turn it comes from, even for an acceptance:
            # linking "ok, let's do that" to its suggestion is the resolver's job.
            candidates.append(
                Candidate(
                    candidate_id=op.candidate_id,
                    project_id=self.scenario.project_id,
                    item=event.item,
                    value=op.value,
                    source_turn_ids=[turn_id],
                    speaker=self.speaker.get(turn_id, ""),
                    text=self.text[turn_id],
                )
            )
            ops.append(op)
            if event.act == "suggest":
                self.suggestions[(event.item, event.turn)] = event.value
        return candidates, ops

    def _operation(self, event: ScriptEvent) -> Operation:
        state = self.log.item_state(event.item)
        active = state.active
        value = event_value(event, self.suggestions)
        if value is None:
            raise ScriptError(f"{event.turn}: {event.act} on {event.item} has no value")
        same_value_open = [r.record_id for r in state.proposed + state.contested if r.value == value]
        cid = record_id(event.item, event.turn)
        base = dict(
            op_id=f"op:{cid}",
            turn_id=event.turn,
            item=event.item,
            candidate_id=cid,
            reason=event.reason,
        )
        act = event.act
        if act in ("decide", "task_open"):
            if active is not None:
                raise ScriptError(f"{event.turn}: {act} on {event.item}, which already has an active value")
            return Operation(op="ADD", add_as="active", value=value, targets=same_value_open,
                             source_turn_ids=[event.turn], **base)
        if act == "suggest":
            if active is not None and active.value == value:
                raise ScriptError(f"{event.turn}: suggests the value that is already active; label it restate")
            return Operation(op="ADD", add_as="proposed", value=value, source_turn_ids=[event.turn], **base)
        if act == "restate":
            if active is None or active.value != value:
                raise ScriptError(f"{event.turn}: restate on {event.item} must repeat the active value")
            return Operation(op="KEEP", targets=[active.record_id], value=value, source_turn_ids=[event.turn], **base)
        if act in ("revise", "task_progress"):
            if active is None:
                raise ScriptError(f"{event.turn}: {act} on {event.item}, which has no active value")
            if active.value == value:
                raise ScriptError(f"{event.turn}: {act} on {event.item} repeats the active value")
            return Operation(op="SUPERSEDE", value=value, targets=[active.record_id] + same_value_open,
                             source_turn_ids=[event.turn], **base)
        if act == "accept":
            suggestion_id = record_id(event.item, event.accepts or "")
            if suggestion_id not in [r.record_id for r in state.proposed]:
                raise ScriptError(f"{event.turn}: accepts {event.accepts}, which is not an open suggestion on {event.item}")
            if active is not None and active.value == value:
                raise ScriptError(f"{event.turn}: accepts a suggestion equal to the active value; label it restate")
            sources = [event.turn, event.accepts]
            if active is None:
                return Operation(op="ADD", add_as="active", value=value, targets=same_value_open,
                                 source_turn_ids=sources, **base)
            return Operation(op="SUPERSEDE", value=value, targets=[active.record_id] + same_value_open,
                             source_turn_ids=sources, **base)
        if act == "contest":
            if active is None or active.value == value:
                raise ScriptError(f"{event.turn}: contest on {event.item} needs an active value that differs")
            return Operation(op="FLAG", value=value, targets=[active.record_id], source_turn_ids=[event.turn], **base)
        raise ScriptError(f"{event.turn}: unknown act {act}")


def replay(scenario: Scenario) -> GoldTimeline:
    deriver = GoldDeriver(scenario)
    turn_times: dict[str, datetime] = {}
    turn_order: list[str] = []
    candidates_by_turn: dict[str, list[Candidate]] = {}
    ops_by_turn: dict[str, list[Operation]] = {}
    log_after: dict[str, OpLog] = {}
    for number, session in enumerate(scenario.sessions, start=1):
        for index, turn in enumerate(session.turns):
            when = turn_time(session.date, index, number)
            turn_times[turn.id] = when
            turn_order.append(turn.id)
            candidates, ops = deriver.observe(turn.id, when)
            candidates_by_turn[turn.id] = candidates
            ops_by_turn[turn.id] = ops
        log_after[session.id] = deriver.log.copy()

    timeline = GoldTimeline(
        scenario=scenario,
        turn_times=turn_times,
        turn_order=turn_order,
        events_by_turn=deriver.events_by_turn,
        candidates_by_turn=candidates_by_turn,
        ops_by_turn=ops_by_turn,
        log_after_session=log_after,
        questions=expand_questions(scenario),
    )
    for question in timeline.questions:
        timeline.expected[question.question_id] = expected_answer(timeline, question)
    _assign_episodes(timeline)
    return timeline


def _assign_episodes(timeline: GoldTimeline) -> None:
    """Group repeated checkpoint questions that ask about the same unchanged gold state.

    Automatic questions repeat every session, so one trap would otherwise be
    counted once per remaining session. Metrics can weight each episode once.
    """
    last_key: dict[tuple[str, str], tuple] = {}
    counter: dict[tuple[str, str], int] = {}
    for question in timeline.questions:
        e = timeline.expected[question.question_id]
        state = (
            e.expected_status, e.expected_value, tuple(e.stale_values), tuple(e.unconfirmed_values),
            tuple(e.confusable_values), e.trap_candidate, e.trap_mention, e.trap_confusable,
        )
        key = (question.item, question.kind if question.kind == "current" else question.question_id)
        if last_key.get(key) != state:
            counter[key] = counter.get(key, 0) + 1
            last_key[key] = state
        suffix = "" if question.kind == "current" else f"#{question.question_id}"
        episode = f"{question.item}#{question.kind}{suffix}#{counter[key]}"
        timeline.expected[question.question_id] = e.model_copy(update={"episode": episode})


# ---------------------------------------------------------------------------
# Expected answers
# ---------------------------------------------------------------------------


def accepted_forms(scenario: Scenario, item: str, value: str | None) -> list[str]:
    """The normalised forms that count as ``value`` for ``item``: the canonical value and its aliases."""
    if value is None:
        return []
    spec = scenario.item(item)
    forms = [value] + list(spec.values.get(value, []))
    if spec.kind == "task":
        forms += PROGRESS_ALIASES.get(value, [])
    return sorted({normalise(form) for form in forms})


def _forms(scenario: Scenario, item: str, values) -> set[str]:
    out: set[str] = set()
    for value in values:
        out |= set(accepted_forms(scenario, item, value))
    return out


def _session_turns(timeline: GoldTimeline, session_id: str) -> list[str]:
    """Every turn up to and including the end of the given session (which may have no turns)."""
    order = [s.id for s in timeline.scenario.sessions]
    upto = set(order[: order.index(session_id) + 1])
    return [t for t in timeline.turn_order if session_of(t) in upto]


def _events_until(timeline: GoldTimeline, session_id: str) -> list[ScriptEvent]:
    seen = _session_turns(timeline, session_id)
    return [event for turn in seen for event in timeline.events_by_turn.get(turn, [])]


def expected_answer(timeline: GoldTimeline, question: Question) -> ExpectedAnswer:
    scenario = timeline.scenario
    window = question.session if question.kind == "as_of" else question.after
    log = timeline.log_after_session[window]
    state = log.item_state(question.item)
    common = dict(
        question_id=question.question_id,
        scenario_id=scenario.scenario_id,
        kind=question.kind,
        item=question.item,
        after=question.after,
    )

    if question.kind == "previous":
        prev = state.previous_active
        now = state.active.value if state.active else None
        current_forms = sorted(set(accepted_forms(scenario, question.item, now)))
        if prev is None:
            return ExpectedAnswer(expected_status="none", current_values=current_forms, **common)
        accepted = accepted_forms(scenario, question.item, prev.value)
        return ExpectedAnswer(
            expected_status="answer",
            expected_value=prev.value,
            accepted_values=accepted,
            current_values=sorted(set(current_forms) - set(accepted)),
            required_support=sorted(set(state.creating_turns[prev.record_id]) | {state.active.created_turn}),
            additional_support=sorted(state.kept_turns[prev.record_id]),
            **common,
        )

    # current and as_of questions read the item's state at the end of the window.
    if state.flagged:
        status, value = "conflict", None
        required = set(state.creating_turns[state.active.record_id])
        for rec in state.contested:
            required |= set(state.creating_turns[rec.record_id])
        additional: set[str] = set()
    elif state.active is not None:
        status, value = "answer", state.active.value
        required = set(state.creating_turns[state.active.record_id])
        additional = set(state.kept_turns[state.active.record_id])
    else:
        status, value = "none", None
        required = {t for rec in state.proposed for t in state.creating_turns[rec.record_id]}
        additional = set()

    accepted = set(accepted_forms(scenario, question.item, value))
    # Precedence when a form sits in several sets: accepted > stale > unconfirmed > confusable.
    stale = _forms(scenario, question.item, [r.value for r in state.history if r.status == "superseded"]) - accepted
    unconfirmed_records = state.proposed + state.contested + [r for r in state.history if r.status == "declined"]
    unconfirmed = _forms(scenario, question.item, [r.value for r in unconfirmed_records]) - accepted - stale
    confusable: set[str] = set()
    for other in scenario.item(question.item).confusable_with:
        confusable |= _forms(scenario, other, [rec.value for rec in log.records(other)])
    confusable = confusable - accepted - stale - unconfirmed

    current_forms: list[str] = []
    if question.kind == "as_of":
        now = timeline.log_after_session[question.after].item_state(question.item).active
        current_forms = sorted(set(accepted_forms(scenario, question.item, now.value if now else None)) - accepted)
        stale, unconfirmed, confusable = set(), set(), set()

    traps = trap_flags(timeline, question, status, sorted(accepted), window)
    return ExpectedAnswer(
        expected_status=status,
        expected_value=value,
        accepted_values=sorted(accepted),
        stale_values=sorted(stale),
        unconfirmed_values=sorted(unconfirmed),
        confusable_values=sorted(confusable),
        current_values=current_forms,
        required_support=sorted(required),
        additional_support=sorted(additional - required),
        **traps,
        **common,
    )


# ---------------------------------------------------------------------------
# Trap flags: would a recency rule get this question wrong?
# ---------------------------------------------------------------------------


def latest_value(events: list[ScriptEvent], item: str, include_mentions: bool, suggestions: dict) -> str | None:
    for event in reversed(events):
        if event.item != item:
            continue
        if not include_mentions and not candidate_bearing(event):
            continue
        return event_value(event, suggestions)
    return None


def suggestion_map(events: list[ScriptEvent]) -> dict[tuple[str, str], str]:
    return {(e.item, e.turn): e.value for e in events if e.act == "suggest"}


def trap_flags(timeline: GoldTimeline, question: Question, status: str, accepted: list[str], window: str) -> dict:
    """Three reasons a recency rule could get this question wrong.

    The newer-record and newer-mention traps never coincide; a similar-item trap
    can coincide with either.

    * trap_candidate: the item's newest memory-bearing statement is not the answer
      (fools recency over extracted records).
    * trap_mention: the newest record is right, but a later mention (question,
      hypothetical, recollection) names a different value (fools raw-turn systems).
    * trap_confusable: the answer is a settled value, and a confusable item has a
      newer record with a different value (fools topic-based ranking).
    """
    # Events are ordered by turn; within one turn, mentions come first, so a mention in the same
    # turn as a decision never counts as newer than it (the order the author listed them is irrelevant).
    position = {turn: i for i, turn in enumerate(timeline.turn_order)}
    events = sorted(_events_until(timeline, window), key=lambda e: (position[e.turn], candidate_bearing(e)))
    suggestions = suggestion_map(events)

    def wrong(value: str | None) -> bool:
        if value is None:
            return status != "none"
        return status != "answer" or normalise(value) not in accepted

    by_candidate = latest_value(events, question.item, include_mentions=False, suggestions=suggestions)
    trap_candidate = wrong(by_candidate)

    own = [position[e.turn] for e in events if e.item == question.item and candidate_bearing(e)]
    last_own_turn = own[-1] if own else -1
    later = [e for e in events if position[e.turn] > last_own_turn]
    later_mentions = [e for e in later if e.item == question.item and e.act == "mention" and e.value is not None]
    trap_mention = (not trap_candidate) and any(normalise(e.value) not in accepted for e in later_mentions)

    trap_confusable = False
    if status == "answer":
        others = set(timeline.scenario.item(question.item).confusable_with)
        for event in later:
            if event.item in others and candidate_bearing(event):
                value = event_value(event, suggestions)
                if value is not None and normalise(value) not in accepted:
                    trap_confusable = True
    return {"trap_candidate": trap_candidate, "trap_mention": trap_mention, "trap_confusable": trap_confusable}
