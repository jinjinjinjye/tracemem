"""Check scenario files before anyone relies on them (docs/benchmark.md, "Validation").

Errors make ``tracemem validate`` fail; warnings are printed but pass. Every
issue has a stable code, listed in ISSUE_CODES, so tests and reviewers can
refer to it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import ValidationError

from tracemem.bench.load import candidate_bearing
from tracemem.bench.replay import GoldDeriver, ScriptError, accepted_forms, replay
from tracemem.ops import InvalidOperation
from tracemem.schema import ACTS_BY_KIND, CONTROL_CATEGORIES, PROGRESS_VALUES, Scenario, normalise, session_of, turn_time

ISSUE_CODES: dict[str, str] = {
    "E-schema": "the file does not match the scenario format",
    "E-duplicate-id": "a session, turn, item or question id is used twice",
    "E-turn-session": "a turn id does not start with its session id",
    "E-order": "sessions or turns are numbered out of order",
    "E-date": "session dates go backwards",
    "E-unknown-turn": "a script event names a turn that does not exist",
    "E-unknown-item": "a script event or question names an item that does not exist",
    "E-act-kind": "the act is not allowed on this kind of item",
    "E-fields": "the event lacks a field its act needs, or has one it forbids",
    "E-value": "the value is not a canonical value of the item (or not a progress value, for tasks)",
    "E-alias-collision": "two values of one item share a spelling",
    "E-same-item-turn": "one turn has two memory-bearing events on the same item",
    "E-script": "the script breaks an act's rule (for example, revise with no decision to revise)",
    "E-question": "a question's session or kind is inconsistent",
    "E-confusable": "confusable_with names an unknown item or the item itself, or is not listed on both items",
    "E-split-folder": "the split field does not match the folder the file is in",
    "W-no-trap": "a non-control scenario has no trap question",
    "W-leak": "a question's text names a value it could be answered with",
    "W-mention-redundant": "a mention names the item's current value, or sits in a turn that already acts on the item",
    "W-session-length": "a session has fewer than 3 or more than 12 turns",
    "W-alias-shared": "confusable items share a spelling of a value",
    "W-description-leak": "an item description, which systems see, names one of its values",
}

EVENT_FIELDS = {
    # act: (required fields, forbidden fields)
    "decide": ({"value"}, {"accepts", "progress"}),
    "revise": ({"value"}, {"accepts", "progress"}),
    "restate": ({"value"}, {"accepts", "progress"}),
    "suggest": ({"value"}, {"accepts", "progress"}),
    "contest": ({"value"}, {"accepts", "progress"}),
    "mention": ({"value"}, {"accepts", "progress"}),
    "accept": ({"accepts"}, {"value", "progress"}),
    "task_open": (set(), {"value", "accepts", "progress"}),
    "task_progress": ({"progress"}, {"value", "accepts"}),
}


@dataclass(frozen=True)
class Issue:
    level: Literal["error", "warning"]
    code: str
    scenario: str
    message: str

    def render(self, redact: bool = False) -> str:
        text = ISSUE_CODES.get(self.code, "") if redact else self.message
        return f"{self.level}: {self.scenario}: {self.code}: {text}"


@dataclass
class TrapStats:
    scenario: str
    split: str
    current_questions: int = 0
    trap_candidate: int = 0
    trap_mention: int = 0
    trap_confusable: int = 0


def _names(text: str, form: str) -> bool:
    """True if ``form`` (a normalised value) appears in ``text`` as a whole word or phrase."""
    if not form:
        return False
    return re.search(rf"(?<![\w-]){re.escape(form)}(?![\w-])", normalise(text)) is not None


def _issue(level, code, scenario, message) -> Issue:
    return Issue(level, code, scenario, message)


def check_structure(s: Scenario) -> list[Issue]:
    sid = s.scenario_id
    out: list[Issue] = []

    def err(code, msg):
        out.append(_issue("error", code, sid, msg))

    def warn(code, msg):
        out.append(_issue("warning", code, sid, msg))

    # ids, order and dates
    session_ids = [x.id for x in s.sessions]
    if len(set(session_ids)) != len(session_ids):
        err("E-duplicate-id", "duplicate session ids")
    expected_sessions = [f"S{i}" for i in range(1, len(s.sessions) + 1)]
    if session_ids != expected_sessions:
        err("E-order", f"sessions should be numbered {expected_sessions}, found {session_ids}")
    for earlier, later in zip(s.sessions, s.sessions[1:]):
        if later.date < earlier.date:
            err("E-date", f"{later.id} is dated before {earlier.id}")
    turn_ids: list[str] = []
    for session in s.sessions:
        numbers = []
        for turn in session.turns:
            turn_ids.append(turn.id)
            if session_of(turn.id) != session.id:
                err("E-turn-session", f"{turn.id} is inside session {session.id}")
            numbers.append(int(turn.id.split("-T")[1]))
        if numbers != list(range(1, len(numbers) + 1)):
            err("E-order", f"turns of {session.id} should be numbered T1..T{len(numbers)}")
        if not 3 <= len(session.turns) <= 12:
            warn("W-session-length", f"{session.id} has {len(session.turns)} turns")
    if len(set(turn_ids)) != len(turn_ids):
        err("E-duplicate-id", "duplicate turn ids")

    # items
    keys = [i.key for i in s.items]
    if len(set(keys)) != len(keys):
        err("E-duplicate-id", "duplicate item keys")
    items = {i.key: i for i in s.items}
    for item in s.items:
        forms: dict[str, str] = {}
        for canonical, aliases in item.values.items():
            for form in [canonical, *aliases]:
                key = normalise(form)
                if key in forms and forms[key] != canonical:
                    err("E-alias-collision", f"{item.key}: '{form}' spells both {forms[key]} and {canonical}")
                forms[key] = canonical
        if item.kind == "task" and set(item.values) - set(PROGRESS_VALUES):
            err("E-value", f"{item.key}: task values must come from {PROGRESS_VALUES}")
        for form in {normalise(f) for c, a in item.values.items() for f in [c, *a]}:
            if _names(item.description, form):
                warn("W-description-leak", f"{item.key}: the description names the value '{form}'")
        for other in item.confusable_with:
            if other == item.key or other not in items:
                err("E-confusable", f"{item.key}: confusable_with names {other}")
            elif item.key not in items[other].confusable_with:
                err("E-confusable", f"{item.key} lists {other} as confusable, but {other} does not list {item.key}")
            elif other in items:
                shared = ({normalise(f) for c, a in item.values.items() for f in [c, *a]}
                          & {normalise(f) for c, a in items[other].values.items() for f in [c, *a]})
                if shared:
                    warn("W-alias-shared", f"{item.key} and {other} share {sorted(shared)}")

    # script events
    known_turns = set(turn_ids)
    seen_pairs: set[tuple[str, str]] = set()
    for event in s.script:
        where = f"{event.turn} {event.act} {event.item}"
        if event.turn not in known_turns:
            err("E-unknown-turn", f"{where}: no such turn")
            continue
        if event.item not in items:
            err("E-unknown-item", f"{where}: no such item")
            continue
        item = items[event.item]
        if event.act not in ACTS_BY_KIND[item.kind]:
            err("E-act-kind", f"{where}: {event.act} is not allowed on a {item.kind} item")
            continue
        required, forbidden = EVENT_FIELDS[event.act]
        present = {f for f in ("value", "accepts", "progress") if getattr(event, f) is not None}
        if required - present or forbidden & present:
            err("E-fields", f"{where}: needs {sorted(required)}, must not have {sorted(forbidden & present)}")
            continue
        if event.value is not None:
            allowed = PROGRESS_VALUES if item.kind == "task" else tuple(item.values)
            if event.value not in allowed:
                err("E-value", f"{where}: '{event.value}' is not one of {list(allowed)}")
        if event.accepts is not None and event.accepts not in known_turns:
            err("E-unknown-turn", f"{where}: accepts {event.accepts}, which does not exist")
        if candidate_bearing(event):
            pair = (event.turn, event.item)
            if pair in seen_pairs:
                err("E-same-item-turn", f"{where}: a second memory-bearing event on this item in the same turn")
            seen_pairs.add(pair)

    # questions
    qids = [q.id for q in s.questions]
    if len(set(qids)) != len(qids):
        err("E-duplicate-id", "duplicate question ids")
    for q in s.questions:
        if q.item not in items:
            err("E-unknown-item", f"question {q.id} is about unknown item {q.item}")
        if q.after not in session_ids:
            err("E-question", f"question {q.id} is asked after unknown session {q.after}")
        if q.kind == "as_of":
            if q.session is None or q.session not in session_ids:
                err("E-question", f"as_of question {q.id} needs a valid session")
            elif q.after in session_ids and session_ids.index(q.session) > session_ids.index(q.after):
                err("E-question", f"as_of question {q.id} asks about a session after the one it is asked in")
        elif q.session is not None:
            err("E-question", f"question {q.id} has a session but is not as_of")
    return out


def check_scenario(s: Scenario, folder_split: str | None = None) -> tuple[list[Issue], TrapStats | None]:
    issues = check_structure(s)
    if folder_split is not None and folder_split != s.split:
        issues.append(_issue("error", "E-split-folder", s.scenario_id, f"split is {s.split} but the file is in {folder_split}/"))
    if any(i.level == "error" for i in issues):
        return issues, None
    try:
        timeline = replay(s)
    except (ScriptError, InvalidOperation) as error:
        issues.append(_issue("error", "E-script", s.scenario_id, str(error)))
        return issues, None

    stats = TrapStats(s.scenario_id, s.split)
    for q in timeline.questions:
        e = timeline.expected[q.question_id]
        if q.kind == "current":
            stats.current_questions += 1
            stats.trap_candidate += e.trap_candidate
            stats.trap_mention += e.trap_mention
            stats.trap_confusable += e.trap_confusable
        tempting = e.accepted_values + e.stale_values + e.unconfirmed_values + e.confusable_values + e.current_values
        named = [v for v in tempting if _names(q.text, v)]
        if named:
            issues.append(_issue("warning", "W-leak", s.scenario_id, f"question {q.question_id} names {named}"))
    issues += _redundant_mentions(s)
    any_trap = stats.trap_candidate + stats.trap_mention + stats.trap_confusable
    if s.category not in CONTROL_CATEGORIES and any_trap == 0:
        issues.append(_issue("warning", "W-no-trap", s.scenario_id, f"category {s.category} has no trap question"))
    return issues, stats


def _redundant_mentions(s: Scenario) -> list[Issue]:
    """Mentions that can never mislead: of the current, undisputed value, or in a turn that acts on the item."""
    out: list[Issue] = []
    acting = {(e.turn, e.item) for e in s.script if e.act != "mention"}
    deriver = GoldDeriver(s)
    for number, session in enumerate(s.sessions, start=1):
        for index, turn in enumerate(session.turns):
            for e in s.script:
                if e.turn != turn.id or e.act != "mention":
                    continue
                state = deriver.log.item_state(e.item)
                if (turn.id, e.item) in acting:
                    out.append(_issue("warning", "W-mention-redundant", s.scenario_id,
                                      f"{turn.id}: mention of {e.item} in a turn that already acts on it"))
                elif state.active is not None and not state.flagged and state.active.value == e.value:
                    out.append(_issue("warning", "W-mention-redundant", s.scenario_id,
                                      f"{turn.id}: mention of {e.value}, the current value of {e.item}"))
            deriver.observe(turn.id, turn_time(session.date, index, number))
    return out


def check_file(path: str | Path) -> tuple[list[Issue], TrapStats | None]:
    path = Path(path)
    folder = path.parent.name if path.parent.name in ("dev", "test") else None
    try:
        with open(path, encoding="utf-8") as handle:
            scenario = Scenario.model_validate(yaml.safe_load(handle))
    except (ValidationError, yaml.YAMLError, TypeError) as error:
        first = str(error).splitlines()[0] if str(error) else type(error).__name__
        return [_issue("error", "E-schema", path.stem, first)], None
    return check_scenario(scenario, folder)


__all__ = ["ISSUE_CODES", "Issue", "TrapStats", "accepted_forms", "check_file", "check_scenario", "check_structure"]
