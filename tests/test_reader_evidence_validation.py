"""Behavioral boundaries for the shared reader's visible-evidence retry checks.

Synthetic records and scripted completions exercise validation, budget boundaries,
and accounting. They make no claim that an online model will obey the feedback.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timedelta

import pytest

from tracemem.resolver import ModelReply, ResolverConfig, RetryableModelError
from tracemem.schema import Record, SystemQuestion, Turn, Usage
from tracemem.systems.comparison import SharedAnswerer, answer_context


CONFIG = ResolverConfig(model="offline-reader-evidence", max_attempts=2)


class SequenceClient:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, **request):
        self.calls.append(copy.deepcopy(request))
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply


def completion(value=None, sources=(), *, status="answer", input_tokens=7, output_tokens=3):
    return ModelReply(json.dumps({
        "status": status, "value": value, "cited_turn_ids": list(sources),
        "text": "Scripted answer using the visible evidence.",
    }), input_tokens=input_tokens, output_tokens=output_tokens)


def question(kind="current", session=None):
    return SystemQuestion(question_id="opaque-reader-question", scenario_id="synthetic-reader",
                          kind=kind, session=session, text="What choice was settled at the requested time?")


def record(turn, value="option Y", status="active", *, item="choice", sources=None):
    session, number = (int(part[1:]) for part in turn.split("-"))
    return Record(record_id=f"private:{item}:{turn}", project_id="synthetic-project", item=item,
                  value=value, status=status, source_turn_ids=list(sources or [turn]),
                  speakers=["Analyst"], created_turn=turn,
                  created_at=datetime(2026, 1, 1) + timedelta(days=session, minutes=number))


def adoption():
    # S2-T1 is the now-closed suggestion; S3-T1 adopts it; S4-T1 reaffirms it.
    return [record("S1-T1", "option X", "superseded"),
            record("S2-T1", status="superseded"),
            record("S3-T1", sources=["S3-T1", "S2-T1", "S4-T1"])]


def run(records, *replies, asked=None, budget=12000, config=CONFIG):
    before = [row.model_dump() for row in records]
    client = SequenceClient(*replies)
    reader = SharedAnswerer(config, client, budget)
    result = reader.answer(asked or question(), records, {
        "S9-T9": Turn(id="S9-T9", speaker="Analyst", text="RAW_TEXT_MUST_STAY_OUT"),
    })
    assert [row.model_dump() for row in records] == before
    context, sources = answer_context(records, budget)
    assert result.context_turn_ids == sources
    assert "RAW_TEXT_MUST_STAY_OUT" not in json.dumps([call["messages"] for call in client.calls])
    for request in client.calls:
        payload = json.loads(request["messages"][1]["content"])
        assert payload["context"] == context
        assert payload["allowed_source_turn_ids"] == sources
    return result, reader, client


def feedback(client):
    messages = client.calls[1]["messages"]
    payload = json.loads(messages[1]["content"])
    error = json.loads(messages[-1]["content"])
    assert error["validation_error"]
    serialized = json.dumps(error, ensure_ascii=False)
    assert serialized and len(serialized) <= 4096
    assert set(re.findall(r"S\d+-T\d+", serialized)).issubset(payload["allowed_source_turn_ids"])
    assert "private:" not in serialized
    return serialized


@pytest.mark.parametrize("incomplete", [["S3-T1"], ["S2-T1"], ["S4-T1"]],
                         ids=["missing-origin", "missing-adoption", "reaffirmation-only"])
def test_incomplete_current_adoption_retries_and_preserves_complete_model_answer(incomplete):
    result, reader, client = run(adoption(), completion("option Y", incomplete),
                                 completion("option Y", ["S2-T1", "S3-T1"]))
    assert result.status == "answer" and result.value == "option Y"
    assert result.cited_turn_ids == ["S2-T1", "S3-T1"]
    assert result.usage == reader.usage() == Usage(calls=2, input_tokens=14, output_tokens=6)
    assert len(client.calls) == 2
    error = feedback(client)
    assert all(source in error for source in {"S2-T1", "S3-T1"} - set(incomplete))


@pytest.mark.parametrize("attempts", [1, 2, 3])
def test_incomplete_adoption_exhaustion_abstains_without_silently_adding_citations(attempts):
    result, reader, client = run(adoption(), *[completion("option Y", ["S3-T1"])] * attempts,
                                 config=CONFIG.model_copy(update={"max_attempts": attempts}))
    assert result.status == "abstain" and result.value is None and result.cited_turn_ids == []
    assert result.usage == reader.usage() == Usage(calls=attempts, input_tokens=7 * attempts,
                                                output_tokens=3 * attempts)
    assert len(client.calls) == attempts


def test_feedback_and_accounting_do_not_leak_into_the_next_question():
    client = SequenceClient(completion("option Y", ["S3-T1"]),
                            completion("option Y", ["S2-T1", "S3-T1"]),
                            completion("option Y", ["S2-T1", "S3-T1"], input_tokens=5, output_tokens=2))
    reader = SharedAnswerer(CONFIG, client)
    first = reader.answer(question(), adoption(), {})
    first_usage = reader.usage()
    second = reader.answer(question(), adoption(), {})
    assert first.usage == first_usage == Usage(calls=2, input_tokens=14, output_tokens=6)
    assert second.usage == Usage(calls=1, input_tokens=5, output_tokens=2)
    assert reader.usage() == Usage(calls=3, input_tokens=19, output_tokens=8)
    assert all("validation_error" not in json.loads(message["content"])
               for message in client.calls[2]["messages"] if message["role"] == "user")
    feedback(client)


@pytest.mark.parametrize("intermediate", [
    ModelReply("not JSON", input_tokens=4, output_tokens=1),
    ModelReply("", refused=True, input_tokens=4, output_tokens=1),
    ModelReply("{}", finish_reason="length", input_tokens=4, output_tokens=1),
    RetryableModelError("offline transient failure"),
], ids=["malformed", "refusal", "truncated", "transient"])
def test_other_invalid_attempt_does_not_make_an_incomplete_adoption_valid(intermediate):
    result, reader, client = run(adoption(), intermediate, completion("option Y", ["S3-T1"]))
    assert result.status == "abstain" and result.cited_turn_ids == []
    expected_input = 7 + (4 if isinstance(intermediate, ModelReply) else 0)
    expected_output = 3 + (1 if isinstance(intermediate, ModelReply) else 0)
    assert result.usage == reader.usage() == Usage(calls=2, input_tokens=expected_input,
                                                output_tokens=expected_output)
    assert len(client.calls) == 2


@pytest.mark.parametrize("origin", [
    record("S2-T1", status="proposed"),
    record("S2-T1", status="declined"),
    record("S2-T1", status="superseded", item="another-choice"),
    record("S2-T1", "different option", "superseded"),
    record("S1-T2", status="superseded"),
    record("S4-T1", status="superseded"),
], ids=["open-proposal", "declined", "other-item", "other-value", "unlinked-origin", "later-origin"])
def test_only_a_visible_earlier_closed_same_value_link_requires_origin(origin):
    records = [origin, record("S3-T1", sources=["S3-T1", "S2-T1", "S4-T1"])]
    result, _, client = run(records, completion("option Y", ["S3-T1"]))
    assert result.status == "answer" and result.cited_turn_ids == ["S3-T1"]
    assert len(client.calls) == 1


def test_a_source_id_without_its_origin_record_does_not_prove_adoption():
    result, _, client = run([adoption()[-1]], completion("option Y", ["S3-T1"]))
    assert "S2-T1" in result.context_turn_ids
    assert result.status == "answer" and len(client.calls) == 1


def test_origin_omitted_by_context_budget_does_not_supply_hidden_evidence():
    origin = record("S2-T1", status="superseded", sources=["S2-T1"] * 60)
    records = [origin, adoption()[-1]]
    context, _ = answer_context(records, 256)
    assert "[superseded]" not in context and "[active]" in context
    result, _, client = run(records, completion("option Y", ["S3-T1"]), budget=256)
    assert result.status == "answer" and len(client.calls) == 1


@pytest.mark.parametrize("kind", ["current", "as_of"])
def test_same_value_across_items_is_not_used_to_guess_the_question_item(kind):
    records = adoption() + [record("S1-T2", item="another-choice"),
                            record("S2-T2", "option Z", "contested")]
    result, _, client = run(records, completion("option Y", ["S3-T1"]),
                            asked=question(kind, "S3" if kind == "as_of" else None))
    assert result.status == "answer" and len(client.calls) == 1


def test_a_paraphrased_value_is_not_semantically_matched_by_the_validator():
    result, _, client = run(adoption(), completion("The choice is option Y", ["S3-T1"]))
    assert result.value == "The choice is option Y" and len(client.calls) == 1


@pytest.mark.parametrize(("kind", "session"), [("current", None), ("as_of", "S2"), ("as_of", "S10")])
def test_relevant_dispute_rejects_certainty_at_the_requested_time(kind, session):
    records = [record("S1-T1", "option X"), record("S2-T1", "option Y", "contested")]
    result, reader, client = run(records, completion("option X", ["S1-T1"]),
                                 completion(sources=["S1-T1", "S2-T1"], status="conflict"),
                                 asked=question(kind, session))
    assert result.status == "conflict" and result.value is None
    assert result.cited_turn_ids == ["S1-T1", "S2-T1"]
    assert result.usage == reader.usage() == Usage(calls=2, input_tokens=14, output_tokens=6)
    feedback(client)


def test_historical_conflict_stays_abstention_if_model_repeats_certain_answer():
    records = [record("S1-T1", "option X"), record("S2-T1", "option Y", "contested")]
    result, _, client = run(records, completion("option X", ["S1-T1"]),
                            completion("option X", ["S1-T1"]), asked=question("as_of", "S2"))
    assert result.status == "abstain" and result.value is None and result.cited_turn_ids == []
    assert len(client.calls) == 2


@pytest.mark.parametrize(("turn", "session"), [("S2-T1", "S1"), ("S10-T1", "S2")])
def test_a_future_dispute_does_not_change_an_earlier_settled_answer(turn, session):
    records = [record("S1-T1", "option X"), record(turn, "option Y", "contested")]
    result, _, client = run(records, completion("option X", ["S1-T1"]),
                            asked=question("as_of", session))
    assert result.status == "answer" and len(client.calls) == 1


@pytest.mark.parametrize("other", [
    record("S2-T1", "option Y", "proposed"),
    record("S2-T1", "option Y", "declined"),
    record("S2-T1", "option Y", "superseded"),
    record("S2-T1", "option Y", "contested", item="another-choice"),
], ids=["proposal", "declined", "closed-history", "other-item"])
def test_non_disputes_do_not_block_a_settled_answer(other):
    result, _, client = run([record("S1-T1", "option X"), other],
                            completion("option X", ["S1-T1"]))
    assert result.status == "answer" and len(client.calls) == 1


def test_a_dispute_omitted_by_context_budget_does_not_leak_into_validation():
    disputed = record("S2-T1", "option Y" * 150, "contested")
    records = [record("S1-T1", "option X"), disputed]
    context, _ = answer_context(records, 256)
    assert "contested" not in context
    result, _, client = run(records, completion("option X", ["S1-T1"]), budget=256)
    assert result.status == "answer" and len(client.calls) == 1


def test_previous_keeps_original_and_replacement_without_current_adoption_rule():
    # S1-T1 is the initial formal LR decision; S3-T1 formally replaces it with SVM.
    records = [record("S1-T1", "logistic regression", "superseded"),
               record("S2-T1", "SVM", "superseded"),
               record("S3-T1", "SVM", sources=["S3-T1", "S2-T1", "S4-T1"])]
    result, _, client = run(records, completion("logistic regression", ["S1-T1", "S3-T1"]),
                            asked=question("previous"))
    assert result.status == "answer" and result.cited_turn_ids == ["S1-T1", "S3-T1"]
    assert len(client.calls) == 1


def test_a_formal_first_decision_needs_no_invented_proposal_source():
    result, _, client = run([record("S1-T1", "spaCy")], completion("spaCy", ["S1-T1"]))
    assert result.status == "answer" and result.cited_turn_ids == ["S1-T1"]
    assert len(client.calls) == 1


def test_cancelled_with_reopening_proposal_remains_a_settled_cancellation():
    records = [record("S3-T1", "cancelled", item="task"),
               record("S4-T1", "open", "proposed", item="task")]
    result, _, client = run(records, completion("cancelled", ["S3-T1"]))
    assert result.status == "answer" and len(client.calls) == 1


@pytest.mark.parametrize("status", ["none", "conflict", "abstain"])
def test_non_answer_status_does_not_trigger_settled_adoption_requirements(status):
    result, _, client = run(adoption(), completion(status=status))
    assert result.status == status and len(client.calls) == 1


def test_native_text_is_not_assigned_hidden_structured_statuses():
    records = [record("S1-T1", "The team chose option X.", None),
               record("S2-T1", "Some participants disagree and recall option Y.", None)]
    result, _, client = run(records, completion("option X", ["S1-T1"]))
    assert result.status == "answer" and len(client.calls) == 1
    # Native text still relies on the shared model prompt; this validator does not
    # pretend a substring in prose is a structured active/contested state.


@pytest.mark.parametrize("complete_second_reply", [False, True])
def test_bounded_feedback_does_not_drop_requirements_beyond_its_preview(complete_second_reply):
    origins = [record(f"S2-T{number}", status="superseded") for number in range(1, 31)]
    sources = ["S3-T1", *(origin.created_turn for origin in origins)]
    records = [*origins, record("S3-T1", sources=sources)]
    second_sources = sources if complete_second_reply else sources[:-1]
    result, _, client = run(records, completion("option Y", ["S3-T1"]),
                            completion("option Y", second_sources))
    preview = feedback(client)
    assert len(set(re.findall(r"S\d+-T\d+", preview))) < len(sources)
    assert result.status == ("answer" if complete_second_reply else "abstain")
    assert result.cited_turn_ids == (sources if complete_second_reply else [])
    assert len(client.calls) == 2


@pytest.mark.parametrize("bad_sources", [["S2-T1", "S3-T1", "S9-T9"],
                                         ["S2-T1", "S3-T1", "S3-T1"]],
                         ids=["unseen-source", "duplicate-source"])
def test_origin_retry_does_not_relax_the_allowed_citation_contract(bad_sources):
    result, _, client = run(adoption(), completion("option Y", ["S3-T1"]),
                            completion("option Y", bad_sources))
    assert result.status == "abstain" and result.cited_turn_ids == []
    assert "S9-T9" not in feedback(client)
    assert len(client.calls) == 2


def test_equal_hidden_timestamps_cannot_change_validation_of_identical_visible_evidence():
    ordinary = adoption()
    equal_timestamps = copy.deepcopy(ordinary)
    equal_timestamps[1] = equal_timestamps[1].model_copy(update={"created_at": equal_timestamps[2].created_at})
    assert answer_context(ordinary, 12000) == answer_context(equal_timestamps, 12000)
    for records in (ordinary, equal_timestamps):
        result, _, client = run(records, completion("option Y", ["S3-T1"]),
                                completion("option Y", ["S2-T1", "S3-T1"]))
        assert result.status == "answer" and result.cited_turn_ids == ["S2-T1", "S3-T1"]
        assert len(client.calls) == 2


@pytest.mark.parametrize(("origin_turn", "adoption_turn"), [("S2-T1", "S10-T1"), ("S2-T2", "S2-T10")])
def test_visible_origin_turn_order_is_numeric_not_lexicographic(origin_turn, adoption_turn):
    records = [record(origin_turn, status="superseded"),
               record(adoption_turn, sources=[adoption_turn, origin_turn])]
    result, _, client = run(records, completion("option Y", [adoption_turn]),
                            completion("option Y", [origin_turn, adoption_turn]))
    assert result.status == "answer" and result.cited_turn_ids == [origin_turn, adoption_turn]
    assert len(client.calls) == 2


def test_unparseable_origin_turn_does_not_invent_a_temporal_relationship():
    origin = record("S2-T1", status="superseded").model_copy(update={
        "created_turn": "unknown-origin", "source_turn_ids": ["unknown-origin"],
    })
    records = [origin, record("S3-T1", sources=["S3-T1", "unknown-origin"])]
    result, _, client = run(records, completion("option Y", ["S3-T1"]))
    assert result.status == "answer" and len(client.calls) == 1


def test_long_source_preview_never_invents_a_truncated_citation_identifier():
    long_source = "S2-T" + "1" * 70
    origin = record("S2-T1", status="superseded").model_copy(update={
        "created_turn": long_source, "source_turn_ids": [long_source],
    })
    records = [origin, record("S3-T1", sources=["S3-T1", long_source])]
    result, _, client = run(records, completion("option Y", ["S3-T1"]),
                            completion("option Y", [long_source, "S3-T1"]))
    assert result.status == "answer" and result.cited_turn_ids == [long_source, "S3-T1"]
    assert len(client.calls) == 2
    feedback(client)
    error = json.loads(client.calls[1]["messages"][-1]["content"])
    assert set(error["required_source_turn_ids"]).issubset(result.context_turn_ids)
    assert error["truncated"] is True
