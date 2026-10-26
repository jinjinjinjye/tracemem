"""Hand-derived resolver scoring cases, independent of the scoring implementation.

The small synthetic script has one instance of each of the five decision labels.
Replay supplies its gold operations; expected counts and rates below are manual.
"""

from __future__ import annotations

import copy
import json

import pytest

from tracemem.bench.replay import replay
from tracemem.eval.resolver_metrics import LABELS, score_scenario, summarize
from tracemem.schema import Scenario


ITEM = "model.main"


def timeline(scenario_id="resolver-metrics-fixture"):
    """A confirmed, proposed, adopted, contested, then reaffirmed project choice."""
    script = [
        {"turn": "S1-T1", "act": "decide", "item": ITEM, "value": "A"},
        {"turn": "S1-T2", "act": "suggest", "item": ITEM, "value": "B"},
        {"turn": "S1-T3", "act": "accept", "item": ITEM, "accepts": "S1-T2"},
        {"turn": "S1-T4", "act": "contest", "item": ITEM, "value": "C"},
        {"turn": "S1-T5", "act": "restate", "item": ITEM, "value": "B"},
    ]
    texts = ["We confirm A.", "Could we try B?", "We adopt the earlier suggestion B.",
             "I dispute B and want C.", "We resolved the disagreement and confirm B."]
    scenario = Scenario.model_validate({
        "scenario_id": scenario_id, "title": "Five resolver decisions", "category": "accepted_suggestion",
        "split": "dev", "author": "tests", "project_id": "synthetic-project",
        "items": [{"key": ITEM, "kind": "decision", "description": "the selected classifier",
                   "values": {value: [] for value in ("A", "B", "C")}}],
        "sessions": [{"id": "S1", "date": "2026-01-05", "turns": [
            {"id": f"S1-T{index}", "speaker": "Speaker", "text": text}
            for index, text in enumerate(texts, start=1)
        ]}],
        "script": script, "auto_questions": False,
    })
    return replay(scenario)


def gold_operations(gold):
    return [op for turn in gold.turn_order for op in gold.ops_by_turn[turn]]


def failure_event(op):
    return {"candidate_id": op.candidate_id, "turn_id": op.turn_id, "item": op.item,
            "status": "generation_failed", "operation_id": None, "attempts": 2,
            "usage": {"calls": 2, "input_tokens": 10, "output_tokens": 3},
            "error_type": "ResolverError", "error_detail": "no valid decision"}


def applied_events(operations):
    return [{"candidate_id": op.candidate_id, "turn_id": op.turn_id, "item": op.item,
             "status": "applied", "operation_id": op.op_id, "attempts": 1,
             "usage": {"calls": 1, "input_tokens": 10, "output_tokens": 3},
             "error_type": None, "error_detail": None} for op in operations]


def assert_rate(actual, numerator, denominator):
    assert actual["n"] == denominator
    assert actual["numerator"] == numerator
    if denominator:
        assert actual["value"] == pytest.approx(numerator / denominator)
    else:
        assert actual["value"] is None


def test_perfect_five_label_run_has_hand_derived_counts_and_states():
    gold = timeline()
    operations = gold_operations(gold)
    rows = score_scenario(gold, operations, [])
    result = summarize(rows)
    assert set(LABELS) == {"ADD-active", "ADD-proposed", "KEEP", "SUPERSEDE", "FLAG"}
    assert len(rows) == 5
    assert result["counts"] == {
        "gold_candidates": 5, "emitted_operations": 5, "applied_operations": 5,
        "rejected_operations": 0, "generation_failures": 0, "missing_operations": 0,
        "extra_predictions": 0,
    }
    for metric in ("label_accuracy", "exact_operation_accuracy", "state_accuracy",
                   "targets_accuracy", "sources_accuracy"):
        assert_rate(result["metrics"][metric], 5, 5)
    assert_rate(result["metrics"]["targeted_targets_accuracy"], 3, 3)
    assert result["macro_f1"]["value"] == 1
    assert result["micro_f1"]["value"] == 1
    assert [row["expected_state"] for row in rows] == [
        ["A", False, [], []], ["A", False, ["B"], []], ["B", False, [], []],
        ["B", True, [], ["C"]], ["B", False, [], []],
    ]
    for label in LABELS:
        assert result["labels"][label]["tp"] == 1
        assert result["labels"][label]["fp"] == result["labels"][label]["fn"] == 0
        assert result["confusion"][label][label] == 1
    assert result["confusion_by_act"]["accept"]["SUPERSEDE"] == 1
    assert result["confusion_by_act"]["suggest"]["ADD-proposed"] == 1
    json.dumps(result, allow_nan=False)


def test_two_add_labels_are_distinct_and_confusion_f1_is_hand_calculated():
    gold = timeline()
    initial, proposal, adoption, dispute, confirmation = gold_operations(gold)
    wrong = proposal.model_copy(update={"add_as": "active"})
    # The mistaken ADD is rejected. Later adoption can still replace the initial
    # decision, but it cannot target or cite a proposal that was never saved.
    recovered = adoption.model_copy(update={"targets": [initial.candidate_id],
                                           "source_turn_ids": [adoption.turn_id]})
    rows = score_scenario(gold, [initial, recovered, dispute, confirmation],
                          [(wrong, "An active choice already exists")])
    result = summarize(rows)
    assert_rate(result["metrics"]["label_accuracy"], 4, 5)
    assert result["confusion"]["ADD-proposed"]["ADD-active"] == 1
    assert result["confusion_by_act"]["suggest"]["ADD-active"] == 1
    active = result["labels"]["ADD-active"]
    proposed = result["labels"]["ADD-proposed"]
    assert (active["tp"], active["fp"], active["fn"]) == (1, 1, 0)
    assert (proposed["tp"], proposed["fp"], proposed["fn"]) == (0, 0, 1)
    assert_rate(active["precision"], 1, 2)
    assert_rate(active["recall"], 1, 1)
    assert_rate(active["f1"], 2, 3)
    assert_rate(proposed["precision"], 0, 0)
    assert_rate(proposed["recall"], 0, 1)
    assert_rate(proposed["f1"], 0, 1)
    assert result["macro_f1"]["value"] == pytest.approx(11 / 15)
    assert result["micro_f1"]["value"] == pytest.approx(4 / 5)


@pytest.mark.parametrize("explicit_failures", [False, True])
def test_missing_predictions_remain_false_negatives_and_in_accuracy_denominators(explicit_failures):
    gold = timeline()
    events = [failure_event(op) for op in gold_operations(gold)] if explicit_failures else None
    rows = score_scenario(gold, [], [], events)
    result = summarize(rows)
    assert len(rows) == 5
    assert {row["status"] for row in rows} == {"generation_failed" if explicit_failures else "missing"}
    for metric in ("label_accuracy", "exact_operation_accuracy", "state_accuracy",
                   "targets_accuracy", "sources_accuracy"):
        assert_rate(result["metrics"][metric], 0, 5)
    assert result["macro_f1"]["value"] == result["micro_f1"]["value"] == 0
    assert_rate(result["metrics"]["invalid_operation_rate"], 0, 0)
    for label in LABELS:
        stats = result["labels"][label]
        assert (stats["tp"], stats["fp"], stats["fn"], stats["support"], stats["predicted"]) == (0, 0, 1, 1, 0)
        assert result["confusion"][label]["MISSING"] == 1
    if explicit_failures:
        assert result["counts"]["generation_failures"] == 5
        assert_rate(result["metrics"]["generation_failure_rate"], 5, 5)
    else:
        assert result["counts"]["missing_operations"] == 5
        assert_rate(result["metrics"]["missing_operation_rate"], 5, 5)


def test_rejected_operation_can_match_label_but_receives_no_exact_or_state_credit():
    gold = timeline()
    operations = gold_operations(gold)
    wrong_confirmation = operations[-1].model_copy(update={"value": "C"})
    rows = score_scenario(gold, operations[:-1], [(wrong_confirmation, "KEEP value differs")])
    final = rows[-1]
    assert final["status"] == "rejected"
    assert final["label_correct"] is True
    assert final["exact_operation_correct"] is False
    assert final["state_correct"] is False
    assert final["predicted_state"] == ["B", True, [], ["C"]]
    result = summarize(rows)
    assert_rate(result["metrics"]["label_accuracy"], 5, 5)
    assert_rate(result["metrics"]["exact_operation_accuracy"], 4, 5)
    assert_rate(result["metrics"]["state_accuracy"], 4, 5)
    assert_rate(result["metrics"]["invalid_operation_rate"], 1, 5)
    assert result["micro_f1"]["value"] == 1


def test_cumulative_state_replays_own_history_instead_of_resetting_to_gold():
    gold = timeline()
    initial, proposal, adoption, dispute, confirmation = gold_operations(gold)
    # Missing the first decision leaves only a proposal. Each later decision
    # references a record absent from this system's own memory and is rejected.
    rows = score_scenario(gold, [proposal],
                          [(adoption, "missing initial record"), (dispute, "missing adopted record"),
                           (confirmation, "missing adopted record")])
    assert [row["state_correct"] for row in rows] == [False] * 5
    assert [row["state_before_correct"] for row in rows] == [True, False, False, False, False]
    assert rows[-1]["predicted_state"] == [None, False, ["B"], []]
    result = summarize(rows)
    assert_rate(result["metrics"]["label_accuracy"], 4, 5)
    assert_rate(result["metrics"]["exact_operation_accuracy"], 1, 5)
    assert_rate(result["metrics"]["state_accuracy"], 0, 5)
    assert_rate(result["metrics"]["invalid_operation_rate"], 3, 4)
    assert result["micro_f1"]["value"] == pytest.approx(8 / 9)
    assert result["labels"]["ADD-active"]["fn"] == 1


def test_exact_operation_comparison_ignores_set_order_and_explanatory_metadata():
    gold = timeline()
    operations = gold_operations(gold)
    operations[2] = operations[2].model_copy(update={
        "op_id": "different-identifier", "targets": list(reversed(operations[2].targets)),
        "source_turn_ids": list(reversed(operations[2].source_turn_ids)),
        "rationale": "Different wording for the same supported decision.", "reason": "different prose",
    })
    rows = score_scenario(gold, operations, [])
    assert all(row["exact_operation_correct"] for row in rows)
    assert all(row["targets_correct"] and row["sources_correct"] for row in rows)
    assert_rate(summarize(rows)["metrics"]["exact_operation_accuracy"], 5, 5)


@pytest.mark.parametrize("field,correctness", [("targets", "targets_correct"),
                                               ("source_turn_ids", "sources_correct")])
def test_duplicate_set_members_are_not_silently_deduplicated_for_scoring(field, correctness):
    gold = timeline()
    operations = gold_operations(gold)
    value = getattr(operations[2], field)
    operations[2] = operations[2].model_copy(update={field: [*value, value[-1]]})
    rows = score_scenario(gold, operations, [])
    assert rows[2][correctness] is False
    assert rows[2]["exact_operation_correct"] is False
    assert rows[2]["label_correct"] is True
    assert all(row["state_correct"] for row in rows)


def test_missing_acceptance_source_penalizes_evidence_without_fabricating_state_error():
    gold = timeline()
    operations = gold_operations(gold)
    operations[2] = operations[2].model_copy(update={"source_turn_ids": ["S1-T3"]})
    rows = score_scenario(gold, operations, [])
    assert rows[2]["sources_correct"] is False
    assert rows[2]["targets_correct"] is True
    assert rows[2]["exact_operation_correct"] is False
    assert rows[2]["state_correct"] is True
    assert_rate(summarize(rows)["metrics"]["sources_accuracy"], 4, 5)


def test_same_candidate_ids_in_different_scenarios_are_counted_independently():
    first, second = timeline("scenario-first"), timeline("scenario-second")
    first_ops, second_ops = gold_operations(first), gold_operations(second)
    assert [op.candidate_id for op in first_ops] == [op.candidate_id for op in second_ops]
    rows = score_scenario(first, first_ops, []) + score_scenario(second, [], [])
    result = summarize(rows)
    assert len(rows) == 10
    assert {row["scenario_id"] for row in rows} == {"scenario-first", "scenario-second"}
    assert_rate(result["metrics"]["label_accuracy"], 5, 10)
    assert_rate(result["metrics"]["state_accuracy"], 5, 10)
    assert result["micro_f1"]["value"] == pytest.approx(2 / 3)
    for label in LABELS:
        assert result["labels"][label]["support"] == 2
        assert result["labels"][label]["recall"]["value"] == 0.5


@pytest.mark.parametrize("duplicate_candidate", [False, True])
def test_extra_emissions_add_false_positives_without_inflating_recall_or_accuracy(duplicate_candidate):
    gold = timeline()
    operations = gold_operations(gold)
    if duplicate_candidate:
        extra = operations[-1].model_copy(update={"op_id": "duplicate-confirmation"})
        extra_label = "KEEP"
    else:
        extra = operations[0].model_copy(update={"op_id": "extra-item", "item": "model.other",
                                               "candidate_id": "model.other@S1-T1"})
        extra_label = "ADD-active"
    rows = score_scenario(gold, operations, [(extra, "extra emission rejected")])
    result = summarize(rows)
    assert len(rows) == 6
    assert result["counts"]["gold_candidates"] == 5
    assert result["counts"]["emitted_operations"] == 6
    assert result["counts"]["extra_predictions"] == 1
    extra_row, = [row for row in rows if row["status"] == "extra"]
    assert extra_row["original_status"] == "rejected"
    assert extra_row["exact_operation_correct"] is None
    assert extra_row["state_correct"] is None
    assert_rate(result["metrics"]["label_accuracy"], 5, 5)
    assert_rate(result["metrics"]["exact_operation_accuracy"], 5, 5)
    assert_rate(result["metrics"]["invalid_operation_rate"], 1, 6)
    assert result["labels"][extra_label]["fp"] == 1
    assert result["labels"][extra_label]["recall"]["value"] == 1
    assert result["micro_f1"]["value"] == pytest.approx(10 / 11)


def test_duplicate_operation_ids_are_rejected_as_ambiguous_artifacts():
    gold = timeline()
    operations = gold_operations(gold)
    with pytest.raises(ValueError):
        score_scenario(gold, operations, [(operations[0], "same identifier in both files")])


def test_event_order_prevents_a_later_correct_duplicate_from_rescuing_recall():
    gold = timeline()
    operations = gold_operations(gold)
    # The first attempt incorrectly FLAGs the already-active value and is
    # rejected. A second KEEP succeeds, but must be scored as an extra emission.
    wrong = operations[-1].model_copy(update={"op_id": "first-wrong-confirmation", "op": "FLAG"})
    ordered = [(op, "applied") for op in operations[:-1]]
    ordered += [(wrong, "rejected"), (operations[-1], "applied")]
    events = [{"candidate_id": op.candidate_id, "turn_id": op.turn_id, "item": op.item,
               "status": status, "operation_id": op.op_id, "attempts": 1,
               "usage": {"calls": 1, "input_tokens": 10, "output_tokens": 3},
               "error_type": "InvalidOperation" if status == "rejected" else None,
               "error_detail": "FLAG must differ from active" if status == "rejected" else None}
              for op, status in ordered]
    rows = score_scenario(gold, operations, [(wrong, "FLAG must differ from active")], events)
    result = summarize(rows)
    confirmation, = [row for row in rows if row["candidate_id"] == operations[-1].candidate_id
                    and row["status"] != "extra"]
    assert confirmation["predicted"]["op_id"] == wrong.op_id
    assert confirmation["status"] == "rejected"
    assert confirmation["state_correct"] is False
    assert_rate(result["metrics"]["label_accuracy"], 4, 5)
    assert_rate(result["metrics"]["exact_operation_accuracy"], 4, 5)
    assert result["labels"]["KEEP"]["tp"] == 0
    assert result["labels"]["KEEP"]["fn"] == 1
    assert result["labels"]["KEEP"]["fp"] == 1
    assert result["labels"]["KEEP"]["recall"]["value"] == 0
    assert result["micro_f1"]["value"] == pytest.approx(8 / 11)


def test_saved_applied_operations_that_cannot_replay_fail_loudly():
    gold = timeline()
    operations = gold_operations(gold)
    with pytest.raises(ValueError):
        score_scenario(gold, operations[1:], [])


def test_invalid_add_subtype_counts_as_an_emitted_false_positive():
    gold = timeline()
    initial, proposal, adoption, dispute, confirmation = gold_operations(gold)
    malformed = proposal.model_copy(update={"add_as": None})
    recovered = adoption.model_copy(update={"targets": [initial.candidate_id],
                                           "source_turn_ids": [adoption.turn_id]})
    result = summarize(score_scenario(gold, [initial, recovered, dispute, confirmation],
                                      [(malformed, "ADD requires add_as")]))
    assert result["confusion"]["ADD-proposed"]["INVALID"] == 1
    assert result["counts"]["emitted_operations"] == 5
    assert result["labels"]["ADD-proposed"]["fn"] == 1
    # Four true positives, one false negative, and one emitted invalid-class
    # false positive. The invalid label must not disappear from micro precision.
    assert result["micro_f1"]["value"] == pytest.approx(8 / 10)
    assert_rate(result["metrics"]["invalid_operation_rate"], 1, 5)


def test_event_processing_turn_must_match_its_candidate():
    gold = timeline()
    operations = gold_operations(gold)
    events = applied_events(operations)
    events[0]["turn_id"] = "S1-T2"  # the suggestion's turn, not the initial decision's turn
    with pytest.raises(ValueError):
        score_scenario(gold, operations, [], events)


def test_event_turn_order_is_not_silently_repaired():
    gold = timeline()
    operations = gold_operations(gold)
    events = applied_events(operations)
    events[0], events[1] = events[1], events[0]
    with pytest.raises(ValueError):
        score_scenario(gold, operations, [], events)


@pytest.mark.parametrize("with_events", [False, True])
def test_saved_applied_operation_order_is_not_silently_repaired(with_events):
    gold = timeline()
    operations = gold_operations(gold)
    events = applied_events(operations) if with_events else None
    operations[0], operations[1] = operations[1], operations[0]
    with pytest.raises(ValueError):
        score_scenario(gold, operations, [], events)


def test_wrong_operation_turn_is_a_decision_error_when_processing_event_is_correct():
    gold = timeline()
    operations = gold_operations(gold)
    wrong = operations[-1].model_copy(update={"turn_id": "S1-T4"})
    events = applied_events(operations[:-1])
    events.append({"candidate_id": wrong.candidate_id, "turn_id": "S1-T5", "item": ITEM,
                   "status": "rejected", "operation_id": wrong.op_id, "attempts": 1,
                   "usage": {"calls": 1, "input_tokens": 10, "output_tokens": 3},
                   "error_type": "InvalidOperation", "error_detail": "wrong operation turn"})
    rows = score_scenario(gold, operations[:-1], [(wrong, "wrong operation turn")], events)
    assert rows[-1]["label_correct"] is True
    assert rows[-1]["exact_operation_correct"] is False
    assert "wrong_turn_id" in rows[-1]["errors"]


def test_no_eligible_denominator_is_null_instead_of_perfect_or_zero():
    result = summarize([])
    assert all(count == 0 for count in result["counts"].values())
    assert all(rate["value"] is None and rate["n"] == 0 for rate in result["metrics"].values())
    assert result["macro_f1"]["value"] is None
    assert result["micro_f1"]["value"] is None
    for label in LABELS:
        assert result["labels"][label]["precision"]["value"] is None
        assert result["labels"][label]["recall"]["value"] is None
        assert result["labels"][label]["f1"]["value"] is None
    # A single first decision has no target-selection opportunities. Its
    # empty target set still matches under the all-candidate target metric.
    gold = timeline()
    data = gold.scenario.model_dump()
    data["script"] = data["script"][:1]
    data["sessions"][0]["turns"] = data["sessions"][0]["turns"][:1]
    one = replay(Scenario.model_validate(data))
    result = summarize(score_scenario(one, gold_operations(one), []))
    assert_rate(result["metrics"]["targeted_targets_accuracy"], 0, 0)
    assert_rate(result["metrics"]["targets_accuracy"], 1, 1)
    assert result["macro_f1"]["n"] == 1
    assert result["macro_f1"]["value"] == 1


def test_scoring_does_not_mutate_saved_operations_or_events():
    gold = timeline()
    operations = gold_operations(gold)
    events = [{"candidate_id": op.candidate_id, "turn_id": op.turn_id, "item": op.item,
               "status": "applied", "operation_id": op.op_id, "attempts": 1,
               "usage": {"calls": 1, "input_tokens": 10, "output_tokens": 3},
               "error_type": None, "error_detail": None} for op in operations[:-1]]
    events.append(failure_event(operations[-1]))
    before = copy.deepcopy(([op.model_dump() for op in operations], events))
    score_scenario(gold, operations[:-1], [], events)
    assert ([op.model_dump() for op in operations], events) == before
