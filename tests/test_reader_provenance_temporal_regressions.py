"""Replay actual reader failures after successful adoption-target repair.

The saved requests/responses are real development artifacts. Corrections below
are scripted transport replies: these tests validate retry and temporal data
flow, not a claim about how a live model will answer after the change.
"""
from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path

import pytest

from support import pilot_timeline
from tracemem.ops import OpLog
from tracemem.resolver import ModelReply, ResolverConfig
from tracemem.schema import Operation, SystemQuestion, Turn
from tracemem.systems import comparison


CAPTURE = json.loads((Path(__file__).parent / "fixtures" /
                      "reader_provenance_temporal_failures.json").read_text(encoding="utf-8"))
CASES = CAPTURE["cases"]
REPAIRED_CASES = [case for case in CASES if case["id"] != "dataset_previous_none_boundary"]
CONFIG = ResolverConfig(model="offline-reader-provenance-temporal", max_attempts=2)


class ScriptedClient:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def complete(self, **request):
        self.calls.append(copy.deepcopy(request))
        return ModelReply(content=next(self.replies), input_tokens=7, output_tokens=3)


def make_question(case):
    # IDs deliberately do not reveal the benchmark item, checkpoint or answer.
    return SystemQuestion(question_id="opaque-question", scenario_id="opaque-scenario",
                          **case["request"]["question"])


def replay_saved(case):
    """Replay actual Resolver output; never use the scenario's gold operations."""
    store = OpLog(case["project_id"])
    for observation in case["observations"]:
        store.observe_turn(observation["turn_id"], datetime.fromisoformat(observation["when"]),
                           observation["speaker"])
        for row in case["prefix_operations"]:
            if row["turn_id"] == observation["turn_id"]:
                store.apply(Operation.model_validate(row))
    return store


def dump_records(records):
    return [record.model_dump(mode="json") for record in records]


def reader_records(case):
    store = replay_saved(case)
    before = store.fingerprint()
    records = comparison._AllMemory().retrieve(make_question(case), store, 4096)
    assert store.fingerprint() == before
    return records


def ask(case, replies):
    records = reader_records(case)
    before = dump_records(records)
    client = ScriptedClient(replies)
    reader = comparison.SharedAnswerer(CONFIG, client, 12000)
    result = reader.answer(make_question(case), records, {
        "S9-T9": Turn(id="S9-T9", speaker="Analyst", text="UNSUPPLIED_RAW_TURN_MARKER"),
    })
    assert dump_records(records) == before
    assert result.usage == reader.usage()
    assert result.usage.calls == len(client.calls)
    assert result.usage.input_tokens == 7 * len(client.calls)
    assert result.usage.output_tokens == 3 * len(client.calls)
    context, sources = comparison.answer_context(records, 12000)
    payloads = [json.loads(call["messages"][1]["content"]) for call in client.calls]
    for index, (call, payload) in enumerate(zip(client.calls, payloads)):
        assert call["messages"][0] == {"role": "system", "content": comparison.ANSWER_PROMPT}
        assert call["response_format"] == comparison.ANSWER_FORMAT
        assert payload["question"] == case["request"]["question"]
        assert payload["context"] == context
        assert payload["allowed_source_turn_ids"] == sources
        assert "UNSUPPLIED_RAW_TURN_MARKER" not in payload["context"]
        assert "opaque-question" not in call["messages"][1]["content"]
        assert "opaque-scenario" not in call["messages"][1]["content"]
        assert not {"expected", "expected_value", "required_support", "question_id", "item"} & payload.keys()
        if index == 0:
            assert len(call["messages"]) == 2
        else:
            assert len(call["messages"]) == 3
            assert call["messages"][:2] == client.calls[0]["messages"]
            assert call["messages"][2]["role"] == "user"
            feedback = json.loads(call["messages"][2]["content"])
            assert feedback["validation_error"]
    assert result.context_turn_ids == sources
    return result, payloads


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_capture_preserves_original_request_response_hashes_and_original_score(case):
    provenance = case["provenance"]
    assert provenance["split"] == "dev"
    assert provenance["run"] == "20261019T041030Z-adoption-retry-rerun"
    assert hashlib.sha256(json.dumps(case["model_request"], sort_keys=True).encode()).hexdigest() == provenance["request_hash"]
    assert hashlib.sha256(case["raw_response"].encode()).hexdigest() == provenance["raw_response_sha256"]
    assert json.loads(case["raw_response"]) == case["observed_decision"]
    assert json.loads(case["model_request"]["messages"][1]["content"]) == case["request"]
    expected = pilot_timeline(case["scenario_id"]).expected[case["question_id"]]
    assert expected.model_dump(mode="json") == case["observed_score"]["expected"]
    assert set(expected.required_support) - set(case["observed_decision"]["cited_turn_ids"]) == set(
        case["observed_score"]["missing_required_citations"])


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_saved_operations_still_reproduce_the_old_terminal_context(case):
    store = replay_saved(case)
    assert dump_records(store.records()) == case["records"]
    context, sources = comparison.answer_context(store.records(), 12000)
    assert context == case["request"]["context"]
    assert sources == case["request"]["allowed_source_turn_ids"]


@pytest.mark.parametrize("case", REPAIRED_CASES, ids=lambda case: case["id"])
def test_actual_failure_is_retried_then_scripted_complete_answer_is_accepted(case):
    result, payloads = ask(case, [case["raw_response"], json.dumps(case["corrected_decision"])])
    assert result.usage.calls == 2
    assert "validation_error" not in payloads[0]
    assert payloads[1] == payloads[0]
    expected = pilot_timeline(case["scenario_id"]).expected[case["question_id"]]
    assert result.status == expected.expected_status
    assert result.value == expected.expected_value
    assert set(result.cited_turn_ids) == set(expected.required_support)
    assert result.text == case["corrected_decision"]["text"]
    # No test gold, hidden link or changed citation is supplied to the model.
    if case["request"]["question"]["kind"] == "current":
        assert payloads[0] == case["request"]
    else:
        assert payloads[0]["context"] != case["request"]["context"]


@pytest.mark.parametrize("case", REPAIRED_CASES, ids=lambda case: case["id"])
def test_repeated_actual_failure_exhausts_instead_of_returning_false_certainty_or_missing_origin(case):
    result, payloads = ask(case, [case["raw_response"], case["raw_response"]])
    assert result.usage.calls == CONFIG.max_attempts == 2
    assert payloads[1] == payloads[0]
    assert result.status == "abstain" and result.value is None
    assert result.cited_turn_ids == []


def test_historical_dispute_uses_saved_prefix_at_requested_time_without_future_resolution_sources():
    case = next(case for case in CASES if case["id"] == "dataset_dispute_as_of")
    store = replay_saved(case)
    before = store.fingerprint()
    # S2-T1 ('I thought we agreed on SST-2 ... not IMDB') was unresolved then;
    # S3-T1 ('I checked the notes: IMDB ...') later closes that claim.
    current = store.item_state("dataset.train")
    assert not current.flagged
    assert any(record.value == "SST-2" and record.status == "declined" for record in current.history)
    cutoff = max((entry for entry in case["observations"] if entry["turn_id"].startswith("S2-")),
                 key=lambda entry: entry["when"])["turn_id"]
    snapshot = store.upto(cutoff)
    assert snapshot.item_state("dataset.train").flagged
    records = comparison._AllMemory().retrieve(make_question(case), store, 4096)
    assert dump_records(records) == dump_records(snapshot.records())
    assert any(record.value == "SST-2" and record.status == "contested" for record in records)
    context, sources = comparison.answer_context(records, 12000)
    assert {"S1-T1", "S2-T1"} <= set(sources)
    assert not any(source.startswith(("S3-", "S4-")) for source in sources)
    assert "[declined]" not in context and "Yelp" not in context
    assert store.fingerprint() == before
    current_question = SystemQuestion(question_id="opaque-current", scenario_id="opaque-scenario",
                                      kind="current", text="What dataset is current?")
    assert dump_records(comparison._AllMemory().retrieve(current_question, store, 4096)) == case["records"]


def test_real_successful_adoptions_and_later_confirmation_remain_intact_when_reader_retries():
    case = next(case for case in CASES if case["id"] == "distilbert_current_followup")
    store = replay_saved(case)
    # S3-T2 ('switch ... to DistilBERT') adopts the S2-T3 suggestion;
    # S3-T4 ('Agreed ... macro-F1') adopts the S3-T3 metric suggestion.
    for item, origin, acceptance, old in [
        ("model.sentiment", "S2-T3", "S3-T2", "S1-T1"),
        ("metric.primary", "S3-T3", "S3-T4", "S1-T3"),
    ]:
        operation = next(row for row in case["prefix_operations"]
                         if row["item"] == item and row["turn_id"] == acceptance)
        assert set(operation["targets"]) == {f"{item}@{old}", f"{item}@{origin}"}
        assert set(operation["source_turn_ids"]) == {origin, acceptance}
        state = store.item_state(item)
        assert state.active is not None and not state.proposed
        assert {origin, acceptance} <= set(state.active.source_turn_ids)
        assert f"{item}@{origin}" in state.active.supersedes
        assert any(record.created_turn == origin and record.status == "superseded" for record in state.history)
    sentiment = store.item_state("model.sentiment")
    assert sentiment.active.created_turn == "S3-T2"
    assert "S4-T1" in sentiment.active.source_turn_ids  # Later DistilBERT confirmation.
    before = store.fingerprint()
    answerer = comparison.SharedAnswerer(CONFIG, ScriptedClient([case["raw_response"]] * 2), 12000)
    assert answerer.answer(make_question(case), store.records(), {}).status == "abstain"
    assert store.fingerprint() == before


def test_previous_current_as_history_failure_remains_an_explicit_unrepaired_boundary():
    case = next(case for case in CASES if case["id"] == "dataset_previous_none_boundary")
    result, payloads = ask(case, [case["raw_response"]])
    assert result.usage.calls == 1 and payloads == [case["request"]]
    assert result.status == "answer" and result.value == "IMDB"
    assert case["observed_score"]["outcome"] == "current_as_historical"
    assert pilot_timeline(case["scenario_id"]).expected[case["question_id"]].expected_status == "none"
