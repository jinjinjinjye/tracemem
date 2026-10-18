"""Offline integration of real resolver decisions, failures and pipeline telemetry.

Scripted completions exercise the actual LLMResolver and OpLog. These checks
cover the plumbing; they do not measure a model's semantic decision quality.
"""

from __future__ import annotations

import json

import pytest

from support import pilot, pilot_timeline, turn_clock
from tracemem.components import GoldMatcher, RuleAnswerer
from tracemem.eval.harness import run_scenario
from tracemem.pipeline import TraceMemPipeline
from tracemem.resolver import (
    FatalModelError,
    LLMResolver,
    ModelReply,
    ResolverConfig,
    ResolverConfigError,
    ResolverError,
    ResolverInputError,
    RetryableModelError,
)
from tracemem.schema import Candidate, Operation, ScenarioMeta, Turn, Usage
from tracemem.systems import REGISTRY


ITEM = "model.main"
OTHER_ITEM = "model.tagger"
CLOCK = turn_clock(*(f"S1-T{i}" for i in range(1, 9)))


class ScriptedClient:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = 0

    def complete(self, **kwargs):
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class EmptyExtractor:
    def extract(self, turn, when, meta):
        return []


class EmptyRetriever:
    def retrieve(self, question, store, budget_tokens):
        return []


class RaisingResolver:
    """A resolver without optional telemetry hooks, to check compatibility."""

    def __init__(self, error):
        self.error = error

    def resolve(self, candidate, related):
        raise self.error


def candidate(turn="S1-T1", value="BERT", item=ITEM):
    return Candidate(candidate_id=f"{item}@{turn}", project_id="synthetic-project",
                     item=item, value=value, source_turn_ids=[turn], speaker="Speaker",
                     text=f"We confirm {value}.")


def reply(turn="S1-T1", *, op="ADD", add_as="active", targets=(), sources=None,
          input_tokens=0, output_tokens=0):
    return ModelReply(content=json.dumps({
        "op": op, "add_as": add_as, "targets": list(targets),
        "source_turn_ids": list(sources or [turn]), "reason": None,
        "rationale": "The source establishes this decision state.",
    }), input_tokens=input_tokens, output_tokens=output_tokens)


def pipeline(resolver):
    return TraceMemPipeline(ScenarioMeta(scenario_id="synthetic-resolver", project_id="synthetic-project"),
                            EmptyExtractor(), GoldMatcher(), resolver,
                            EmptyRetriever(), RuleAnswerer())


def real_pipeline(*responses, max_attempts=2):
    client = ScriptedClient(*responses)
    resolver = LLMResolver(ResolverConfig(model="offline-model", max_attempts=max_attempts), client)
    return pipeline(resolver), client


def observe(system, *candidates):
    turn_id = candidates[0].source_turn_ids[0]
    turn = Turn(id=turn_id, speaker="Speaker", text=" ".join(c.text for c in candidates))
    system.observe(turn, CLOCK[turn_id], gold_candidates=list(candidates))


def memory_snapshot(system):
    return system.operations(), system.log.records()


def test_real_resolver_drives_suggestion_adoption_dispute_and_confirmation():
    """All five decision labels cross the pipeline boundary into the real store."""
    initial = f"{ITEM}@S1-T1"  # the confirmed BERT choice
    proposal = f"{ITEM}@S1-T2"  # the suggested DistilBERT choice
    adopted = f"{ITEM}@S1-T3"  # the adopted DistilBERT choice
    system, client = real_pipeline(
        reply(), reply("S1-T2", add_as="proposed"),
        reply("S1-T3", op="SUPERSEDE", add_as=None, targets=[initial, proposal],
              sources=["S1-T3", "S1-T2"]),
        reply("S1-T4", op="FLAG", add_as=None, targets=[adopted]),
        reply("S1-T5", op="KEEP", add_as=None, targets=[adopted]),
    )
    observe(system, candidate())
    observe(system, candidate("S1-T2", "DistilBERT"))
    assert system.log.item_state(ITEM).summary() == ("BERT", False, ("DistilBERT",), ())
    observe(system, candidate("S1-T3", "DistilBERT"))
    state = system.log.item_state(ITEM)
    assert state.active.supersedes == [initial, proposal]
    assert state.previous_active.value == "BERT"
    observe(system, candidate("S1-T4", "RoBERTa"))
    assert system.log.item_state(ITEM).summary() == ("DistilBERT", True, (), ("RoBERTa",))
    observe(system, candidate("S1-T5", "DistilBERT"))
    assert system.log.item_state(ITEM).summary() == ("DistilBERT", False, (), ())
    assert system.rejected_operations() == []
    assert [e["status"] for e in system.resolver_events()] == ["applied"] * 5
    assert [e["operation_id"] for e in system.resolver_events()] == [op.op_id for op in system.operations()]
    assert system.resolver_usage() == Usage(calls=5)
    assert client.calls == 5


@pytest.mark.parametrize("failure", [
    TimeoutError("offline timeout"), RetryableModelError("offline transient failure"),
    ModelReply(content="not valid JSON", input_tokens=11, output_tokens=3),
], ids=["timeout", "transient-provider", "malformed-completion"])
def test_exhausted_generation_preserves_memory_and_never_settles_dispute(failure):
    initial = f"{ITEM}@S1-T1"  # the confirmed BERT choice
    system, _ = real_pipeline(reply(), reply("S1-T2", op="FLAG", add_as=None, targets=[initial]),
                              failure, failure)
    observe(system, candidate())
    observe(system, candidate("S1-T2", "DistilBERT"))
    before = memory_snapshot(system)
    failed = candidate("S1-T3", "BERT")
    observe(system, failed)
    assert memory_snapshot(system) == before
    assert system.log.item_state(ITEM).flagged
    assert system.rejected_operations() == []
    assert system.candidates()[-1] == failed
    event = system.resolver_events()[-1]
    assert event["candidate_id"] == failed.candidate_id
    assert (event["turn_id"], event["item"]) == ("S1-T3", ITEM)
    assert (event["status"], event["operation_id"], event["attempts"]) == ("generation_failed", None, 2)
    assert event["error_type"] == "ResolverError"
    assert event["error_detail"]
    assert event["usage"]["calls"] == 2
    expected_tokens = (22, 6) if isinstance(failure, ModelReply) else (0, 0)
    assert (event["usage"]["input_tokens"], event["usage"]["output_tokens"]) == expected_tokens
    assert system.resolver_usage() == Usage(calls=4, input_tokens=expected_tokens[0],
                                           output_tokens=expected_tokens[1])


def test_failed_candidate_does_not_prevent_later_candidate_in_same_turn():
    system, client = real_pipeline(ModelReply(content="broken"), TimeoutError(), reply())
    failed, succeeding = candidate(), candidate(item=OTHER_ITEM, value="spaCy")
    observe(system, failed, succeeding)
    assert system.log.records(ITEM) == []
    assert system.log.item_state(OTHER_ITEM).active.value == "spaCy"
    assert [op.candidate_id for op in system.operations()] == [succeeding.candidate_id]
    assert system.candidates() == [failed, succeeding]
    assert [e["status"] for e in system.resolver_events()] == ["generation_failed", "applied"]
    assert [e["attempts"] for e in system.resolver_events()] == [2, 1]
    assert client.calls == 3


def test_retry_usage_is_per_candidate_and_cumulative_usage_counts_every_call():
    system, _ = real_pipeline(
        ModelReply(content="broken", input_tokens=10, output_tokens=2),
        reply(input_tokens=20, output_tokens=4), TimeoutError(),
        reply("S1-T2", input_tokens=7, output_tokens=1),
    )
    observe(system, candidate())
    first_usage = system.resolver_usage()
    observe(system, candidate("S1-T2", item=OTHER_ITEM, value="spaCy"))
    events = system.resolver_events()
    assert [e["attempts"] for e in events] == [2, 2]
    assert [e["usage"] for e in events] == [
        {"calls": 2, "input_tokens": 30, "output_tokens": 6},
        {"calls": 2, "input_tokens": 7, "output_tokens": 1},
    ]
    assert first_usage == Usage(calls=2, input_tokens=30, output_tokens=6)
    assert system.resolver_usage() == Usage(calls=4, input_tokens=37, output_tokens=7)


def test_fatal_provider_failure_is_logged_and_aborts_remaining_candidates():
    system, client = real_pipeline(FatalModelError("provider configuration rejected"), reply())
    first, later = candidate(), candidate(item=OTHER_ITEM)
    with pytest.raises(FatalModelError):
        observe(system, first, later)
    assert memory_snapshot(system) == ([], [])
    assert system.candidates() == [first]
    assert client.calls == 1
    event, = system.resolver_events()
    assert event["status"] == "aborted"
    assert event["error_type"] == "FatalModelError"
    assert event["operation_id"] is None
    assert event["usage"] == {"calls": 1, "input_tokens": 0, "output_tokens": 0}


def test_invalid_resolver_input_aborts_without_a_model_call():
    system, client = real_pipeline()
    malformed = candidate().model_copy(update={"candidate_id": "inconsistent-candidate"})
    with pytest.raises(ResolverInputError):
        observe(system, malformed)
    assert memory_snapshot(system) == ([], [])
    assert client.calls == 0
    event, = system.resolver_events()
    assert (event["status"], event["error_type"]) == ("aborted", "ResolverInputError")
    assert event["usage"] == {"calls": 0, "input_tokens": 0, "output_tokens": 0}


@pytest.mark.parametrize("error", [ResolverConfigError("missing model"),
                                 ResolverInputError("invalid matched state"),
                                 FatalModelError("provider unavailable for this account")])
def test_abort_errors_from_legacy_resolver_are_logged_and_reraised(error):
    system = pipeline(RaisingResolver(error))
    with pytest.raises(type(error)) as caught:
        observe(system, candidate())
    assert caught.value is error
    event, = system.resolver_events()
    assert event["status"] == "aborted"
    assert event["error_type"] == type(error).__name__
    assert event["usage"] is None
    assert system.resolver_usage() is None


def test_generation_failure_without_usage_hook_keeps_attempt_count():
    system = pipeline(RaisingResolver(ResolverError(f"{ITEM}@S1-T1", 3, "no valid decision")))
    observe(system, candidate())
    event, = system.resolver_events()
    assert (event["status"], event["attempts"], event["usage"]) == ("generation_failed", 3, None)
    assert system.resolver_usage() is None
    assert memory_snapshot(system) == ([], [])


@pytest.mark.parametrize("error", [RuntimeError("programming defect"), ValueError("unexpected defect")])
def test_unexpected_errors_are_not_converted_into_recoverable_generation_failures(error):
    system = pipeline(RaisingResolver(error))
    with pytest.raises(type(error)) as caught:
        observe(system, candidate())
    assert caught.value is error
    assert memory_snapshot(system) == ([], [])
    assert system.rejected_operations() == []
    assert not any(event["status"] == "generation_failed" for event in system.resolver_events())


def test_store_rejection_has_its_own_event_and_preserves_existing_rejection_hook():
    class UnseenSourceResolver:
        def resolve(self, cand, related):
            return Operation(op_id="offline-rejected", op="ADD", add_as="active", turn_id="S1-T1",
                             item=cand.item, value=cand.value, source_turn_ids=["S1-T8"],
                             candidate_id=cand.candidate_id)

    system = pipeline(UnseenSourceResolver())
    observe(system, candidate())
    assert memory_snapshot(system) == ([], [])
    (rejected, reason), = system.rejected_operations()
    assert rejected.op_id == "offline-rejected"
    assert reason
    event, = system.resolver_events()
    assert (event["status"], event["operation_id"]) == ("rejected", rejected.op_id)
    assert event["error_type"] == "InvalidOperation"
    assert event["usage"] is None


def test_resolver_event_snapshots_cannot_mutate_pipeline_nested_usage():
    system, _ = real_pipeline(reply(input_tokens=9, output_tokens=2))
    observe(system, candidate())
    snapshot = system.resolver_events()
    snapshot[0]["usage"]["calls"] = 999
    snapshot[0]["status"] = "generation_failed"
    snapshot.append({"status": "invented"})
    fresh, = system.resolver_events()
    assert fresh["status"] == "applied"
    assert fresh["usage"] == {"calls": 1, "input_tokens": 9, "output_tokens": 2}
    assert system.resolver_usage() == Usage(calls=1, input_tokens=9, output_tokens=2)


def test_pipeline_describes_real_resolver_configuration_without_calling_model():
    system, client = real_pipeline()
    description = system.describe()
    assert description["resolver"] == "LLMResolver"
    assert description["resolver_config"] == system.resolver.describe()
    assert description["resolver_config"]["model"] == "offline-model"
    assert description["resolver_config"]["prompt_hash"]
    assert description["resolver_config"]["output_schema_hash"]
    assert client.calls == 0


def test_legacy_gold_pipeline_has_no_resolver_telemetry_and_unchanged_description():
    gold = pilot_timeline("pilot-01")
    _, system = run_scenario(REGISTRY["pipeline-gold"], pilot("pilot-01"), gold)
    assert system.resolver_events() == []
    assert system.resolver_usage() is None
    assert system.describe() == {
        "extractor": "GoldExtractor", "matcher": "GoldMatcher", "resolver": "GoldResolver",
        "retriever": "GoldRetriever", "answerer": "RuleAnswerer", "budget_tokens": 2000,
    }
    assert system.rejected_operations() == []
