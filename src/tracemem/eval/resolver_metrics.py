"""Scorer-side diagnostics for resolver runs with gold candidates.

No model is called here. Gold operations come from replay; predicted state is
reconstructed independently from the saved applied operations. Classification
scores include rejected decisions, while executed exactness requires application.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from tracemem.bench.load import candidate_bearing
from tracemem.bench.replay import GoldTimeline
from tracemem.ops import InvalidOperation, OpLog
from tracemem.schema import Operation


LABELS = ("ADD-active", "ADD-proposed", "KEEP", "SUPERSEDE", "FLAG")


def _label(op: Operation | dict | None) -> str | None:
    if op is None:
        return None
    data = op.model_dump() if isinstance(op, Operation) else op
    label = f"ADD-{data['add_as']}" if data["op"] == "ADD" else data["op"]
    return label if label in LABELS else "INVALID"


def _same_set(actual: list[str], expected: list[str]) -> bool:
    return len(actual) == len(set(actual)) and set(actual) == set(expected)


def _state(log: OpLog, item: str) -> list:
    active, flagged, proposed, contested = log.item_state(item).summary()
    return [active, flagged, list(proposed), list(contested)]


@dataclass
class _Attempt:
    candidate_id: str | None
    turn_id: str
    status: str
    op: Operation | None = None
    detail: str | None = None
    primary: bool = False


def _attempts(timeline: GoldTimeline, operations: list[Operation],
              rejected: list[tuple[Operation, str]], events: list[dict] | None) -> list[_Attempt]:
    """Use event order when available; otherwise keep a stable, non-best-match order.

    Older logs have separate applied/rejected files. Within the same candidate,
    applied entries precede rejected entries when no event chronology exists.
    """
    entries = [(op, "applied", None) for op in operations]
    entries += [(op, "rejected", reason) for op, reason in rejected]
    by_id = {}
    for op, status, detail in entries:
        if op.op_id in by_id:
            raise ValueError(f"duplicate operation id in resolver artifacts: {op.op_id}")
        by_id[op.op_id] = (op, status, detail)
    attempts = []
    seen = set()
    turn_order = {turn: index for index, turn in enumerate(timeline.turn_order)}
    gold_turns = {op.candidate_id: turn for turn in timeline.turn_order for op in timeline.ops_by_turn[turn]}
    last_turn = -1
    for event in events or []:
        event_turn = event.get("turn_id")
        if event_turn not in turn_order or turn_order[event_turn] < last_turn:
            raise ValueError("resolver event processing turns are unknown or out of order")
        last_turn = turn_order[event_turn]
        gold_turn = gold_turns.get(event.get("candidate_id"))
        if gold_turn is not None and event_turn != gold_turn:
            raise ValueError("resolver event processing turn disagrees with its gold candidate")
        status = event.get("status")
        operation_id = event.get("operation_id")
        if status in ("applied", "rejected"):
            if operation_id not in by_id or operation_id in seen:
                raise ValueError("resolver event does not identify one saved operation")
            op, saved_status, detail = by_id[operation_id]
            if status != saved_status or event.get("candidate_id") != op.candidate_id:
                raise ValueError("resolver event disagrees with its saved operation")
            seen.add(operation_id)
            attempts.append(_Attempt(op.candidate_id, event["turn_id"], status, op, detail))
        elif status == "generation_failed":
            if operation_id is not None:
                raise ValueError("generation failure cannot identify an emitted operation")
            attempts.append(_Attempt(event.get("candidate_id"), event["turn_id"], status,
                                     detail=event.get("error_detail")))
        else:
            raise ValueError("resolver scoring requires completed candidate events")
    if events and len(seen) != len(entries):
        raise ValueError("resolver events omit saved operations")
    if not events:
        attempts = [_Attempt(op.candidate_id, op.turn_id, status, op, detail)
                    for op, status, detail in entries]
        order = {op.candidate_id: index for index, op in enumerate(
            op for turn in timeline.turn_order for op in timeline.ops_by_turn[turn])}
        turns = {turn: index for index, turn in enumerate(timeline.turn_order)}
        # Preserve an unmatched applied operation before the next matched applied
        # operation in its turn, so an extra write can affect that later decision.
        anchors = {}
        next_known = {}
        for index in range(len(attempts) - 1, -1, -1):
            attempt = attempts[index]
            if attempt.candidate_id in order:
                anchors[index] = (order[attempt.candidate_id], 0)
                if attempt.status == "applied":
                    next_known[attempt.turn_id] = order[attempt.candidate_id]
            else:
                anchors[index] = (next_known.get(attempt.turn_id, len(order)), -1)
        attempts = [attempt for index, attempt in sorted(enumerate(attempts), key=lambda pair: (
            turns.get(gold_turns.get(pair[1].candidate_id, pair[1].turn_id), len(turns)),
            *anchors[pair[0]], pair[0]))]
    gold_ids = {op.candidate_id for turn in timeline.turn_order for op in timeline.ops_by_turn[turn]}
    claimed = set()
    for attempt in attempts:
        if attempt.candidate_id in gold_ids and attempt.candidate_id not in claimed:
            attempt.primary = True
            claimed.add(attempt.candidate_id)
    return attempts


def score_scenario(timeline: GoldTimeline, operations: list[Operation],
                   rejected: list[tuple[Operation, str]], events: list[dict] | None = None) -> list[dict]:
    """Score every gold candidate, retaining missing predictions and extra decisions.

    Candidate IDs are the only alignment key. The first attempt owns a gold row;
    repeated/unknown IDs become extras and never improve recall. Applied artifact
    inconsistencies raise ValueError instead of silently changing reconstructed state.
    """
    attempts = _attempts(timeline, operations, rejected, events)
    gold_ops = {op.candidate_id: op for turn in timeline.turn_order for op in timeline.ops_by_turn[turn]}
    candidates = {c.candidate_id: c for turn in timeline.turn_order for c in timeline.candidates_by_turn[turn]}
    acts = {(event.turn, event.item): event.act for event in timeline.scenario.script if candidate_bearing(event)}
    by_turn = defaultdict(list)
    for attempt in attempts:
        # A malformed op.turn_id is a decision error: candidate/event chronology
        # determines when it was attempted, not the operation's claimed source turn.
        current = gold_ops[attempt.candidate_id].turn_id if attempt.candidate_id in gold_ops else attempt.turn_id
        if current not in timeline.turn_times:
            raise ValueError("resolver artifact refers to an unknown processing turn")
        by_turn[current].append(attempt)
    gold_log, actual_log = OpLog(timeline.scenario.project_id), OpLog(timeline.scenario.project_id)
    turns = {turn.id: turn for turn in timeline.scenario.turns()}
    rows = []
    replayed_operations = []

    def apply(attempt: _Attempt) -> None:
        if attempt.status == "applied":
            try:
                actual_log.apply(attempt.op)
                replayed_operations.append(attempt.op.op_id)
            except InvalidOperation as error:
                raise ValueError(f"saved applied operation cannot be replayed: {attempt.op.op_id}: {error}") from None

    def extra(attempt: _Attempt, turn_id: str) -> None:
        apply(attempt)
        item = attempt.op.item if attempt.op else ""
        rows.append({
            "scenario_id": timeline.scenario.scenario_id, "category": timeline.scenario.category,
            "candidate_id": attempt.candidate_id, "turn_id": turn_id, "item": item,
            "act": None, "text": turns[turn_id].text, "expected": None,
            "predicted": attempt.op.model_dump() if attempt.op else None,
            "gold_label": None, "predicted_label": _label(attempt.op),
            "status": "extra", "original_status": attempt.status, "detail": attempt.detail,
            "errors": ["extra_prediction"], "label_correct": None, "exact_operation_correct": None,
            "targets_correct": None, "sources_correct": None, "state_correct": None,
            "state_before_correct": None, "expected_state": None,
            "predicted_state": _state(actual_log, item) if item else None,
        })

    for turn_id in timeline.turn_order:
        when, turn = timeline.turn_times[turn_id], turns[turn_id]
        gold_log.observe_turn(turn_id, when, turn.speaker)
        actual_log.observe_turn(turn_id, when, turn.speaker)
        queue = list(by_turn[turn_id])
        for expected in timeline.ops_by_turn[turn_id]:
            attempt = None
            while queue:
                following = queue[0]
                if following.primary:
                    if following.candidate_id == expected.candidate_id:
                        attempt = queue.pop(0)
                    break
                extra(queue.pop(0), turn_id)
            before = _state(actual_log, expected.item) == _state(gold_log, expected.item)
            gold_log.apply(expected)
            if attempt:
                apply(attempt)
            predicted = attempt.op if attempt else None
            status = attempt.status if attempt else "missing"
            label_correct = predicted is not None and _label(predicted) == _label(expected)
            targets_correct = predicted is not None and _same_set(predicted.targets, expected.targets)
            sources_correct = predicted is not None and _same_set(predicted.source_turn_ids, expected.source_turn_ids)
            same_fields = predicted is not None and all(getattr(predicted, key) == getattr(expected, key)
                                                        for key in ("item", "value", "turn_id"))
            exact = status == "applied" and label_correct and targets_correct and sources_correct and same_fields
            expected_state, predicted_state = _state(gold_log, expected.item), _state(actual_log, expected.item)
            state_correct = expected_state == predicted_state
            errors = []
            if status in ("missing", "generation_failed", "rejected"):
                errors.append(status)
            if predicted:
                if not label_correct:
                    errors.append("wrong_label")
                if not targets_correct:
                    errors.append("wrong_targets")
                if not sources_correct:
                    errors.append("wrong_sources")
                for key in ("item", "value", "turn_id"):
                    if getattr(predicted, key) != getattr(expected, key):
                        errors.append(f"wrong_{key}")
            if not state_correct:
                errors.append("wrong_state")
            candidate = candidates[expected.candidate_id]
            rows.append({
                "scenario_id": timeline.scenario.scenario_id, "category": timeline.scenario.category,
                "candidate_id": expected.candidate_id, "turn_id": turn_id, "item": expected.item,
                "act": acts[(turn_id, expected.item)], "text": candidate.text,
                "expected": expected.model_dump(), "predicted": predicted.model_dump() if predicted else None,
                "gold_label": _label(expected), "predicted_label": _label(predicted),
                "status": status, "original_status": status, "detail": attempt.detail if attempt else None,
                "errors": errors, "label_correct": label_correct, "exact_operation_correct": exact,
                "targets_correct": targets_correct, "sources_correct": sources_correct,
                "state_correct": state_correct, "state_before_correct": before,
                "expected_state": expected_state, "predicted_state": predicted_state,
            })
        for attempt in queue:
            if attempt.primary:
                raise ValueError("resolver attempt order disagrees with gold-candidate processing order")
            extra(attempt, turn_id)
    if replayed_operations != [op.op_id for op in operations]:
        raise ValueError("saved applied operation order disagrees with resolver processing order")
    return rows


def _ratio(numerator: int, denominator: int) -> dict:
    return {"value": numerator / denominator if denominator else None,
            "n": denominator, "numerator": numerator}


def summarize(rows: list[dict]) -> dict:
    """Aggregate candidate-weighted metrics with explicit denominators and abstentions."""
    gold = [row for row in rows if row["expected"] is not None]
    emitted = [row for row in rows if row["predicted"] is not None]
    extras = [row for row in emitted if row["expected"] is None]
    n = len(gold)
    failed = sum(row["status"] == "generation_failed" for row in gold)
    missing = sum(row["predicted"] is None for row in gold)
    rejected = sum(row["original_status"] == "rejected" for row in emitted)
    targeted = [row for row in gold if row["expected"]["targets"]]
    metrics = {
        name: _ratio(sum(bool(row[field]) for row in gold), n)
        for name, field in (
            ("label_accuracy", "label_correct"), ("exact_operation_accuracy", "exact_operation_correct"),
            ("state_accuracy", "state_correct"), ("targets_accuracy", "targets_correct"),
            ("sources_accuracy", "sources_correct"))
    }
    metrics.update({
        "targeted_targets_accuracy": _ratio(sum(bool(row["targets_correct"]) for row in targeted), len(targeted)),
        "generation_failure_rate": _ratio(failed, n), "missing_operation_rate": _ratio(missing, n),
        "invalid_operation_rate": _ratio(rejected, len(emitted)),
    })
    labels = {}
    for label in LABELS:
        support = sum(_label(row["expected"]) == label for row in gold)
        predicted = sum(_label(row["predicted"]) == label for row in emitted)
        tp = sum(_label(row["expected"]) == label == _label(row["predicted"]) for row in gold)
        fp, fn = predicted - tp, support - tp
        labels[label] = {"tp": tp, "fp": fp, "fn": fn, "support": support, "predicted": predicted,
                         "precision": _ratio(tp, tp + fp), "recall": _ratio(tp, tp + fn),
                         "f1": _ratio(2 * tp, 2 * tp + fp + fn)}
    defined = [label for label in LABELS if labels[label]["f1"]["value"] is not None]
    tp = sum(value["tp"] for value in labels.values())
    # Invalid emitted labels are still predictions: retain their false positives
    # instead of letting malformed output improve micro precision.
    fp, fn = len(emitted) - tp, n - tp
    confusion = {label: {predicted: 0 for predicted in (*LABELS, "INVALID", "MISSING")} for label in LABELS}
    by_act = {}
    for row in gold:
        actual = _label(row["predicted"]) or "MISSING"
        confusion[_label(row["expected"])][actual] += 1
        act = by_act.setdefault(row["act"], {label: 0 for label in (*LABELS, "INVALID", "MISSING")})
        act[actual] = act.get(actual, 0) + 1
    return {
        "counts": {"gold_candidates": n, "emitted_operations": len(emitted),
                   "applied_operations": sum(row["original_status"] == "applied" for row in emitted),
                   "rejected_operations": rejected, "generation_failures": failed,
                   "missing_operations": missing, "extra_predictions": len(extras)},
        "metrics": metrics, "labels": labels,
        "macro_f1": {"value": sum(labels[label]["f1"]["value"] for label in defined) / len(defined)
                     if defined else None, "n": len(defined), "labels": defined},
        "micro_f1": _ratio(2 * tp, 2 * tp + fp + fn),
        "confusion": confusion, "confusion_by_act": by_act,
        "error_counts": dict(Counter(error for row in rows for error in row["errors"])),
    }
