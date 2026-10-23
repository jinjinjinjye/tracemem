"""Offline resolver plumbing and state transitions, using scripted model replies.

These tests do not claim to measure a language model's decision quality. Every
accepted decision is also applied to the real OpLog to check the shared contract.
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys

import pytest

from support import turn_clock
from tracemem.ops import OpLog, record_id
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
from tracemem.schema import Candidate, Operation, Usage


ITEM = "model.main"
TURNS = tuple(f"S1-T{i}" for i in range(1, 9))


class ScriptedClient:
    """Record requests and return replies or raise errors without using a network."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def complete(self, *, config, messages, response_format):
        self.calls.append({"config": config, "messages": copy.deepcopy(messages),
                           "response_format": copy.deepcopy(response_format)})
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def candidate(turn="S1-T4", value="B", **changes):
    data = dict(candidate_id=f"{ITEM}@{turn}", project_id="synthetic-project",
                item=ITEM, value=value, source_turn_ids=[turn], speaker="Speaker",
                text=f"We confirm {value} for the main model.")
    data.update(changes)
    return Candidate(**data)


def decision(op="ADD", *, add_as="active", targets=(), sources=("S1-T4",), **changes):
    data = dict(op=op, add_as=add_as, targets=list(targets),
                source_turn_ids=list(sources), reason=None,
                rationale="The statement explicitly confirms the choice.")
    data.update(changes)
    return data


def reply(data=None, *, input_tokens=0, output_tokens=0):
    return ModelReply(content=json.dumps(decision() if data is None else data),
                      input_tokens=input_tokens, output_tokens=output_tokens)


def resolver(*responses, **settings):
    client = ScriptedClient(*responses)
    return LLMResolver(ResolverConfig(model="offline-model", **settings), client), client


def operation(op, turn, value, *, add_as=None, targets=(), sources=None, item=ITEM):
    return Operation(op_id=f"fixture:{item}:{turn}", op=op, turn_id=turn, item=item,
                     value=value, add_as=add_as, targets=list(targets),
                     source_turn_ids=list(sources or [turn]))


def log_with(*operations):
    log = OpLog("synthetic-project", turn_clock(*TURNS))
    for op in operations:
        log.apply(op)
    return log


def rid(turn, item=ITEM):
    return record_id(item, turn)


def seeded_log():
    return log_with(operation("ADD", "S1-T1", "A", add_as="active"),
                    operation("ADD", "S1-T2", "B", add_as="proposed"),
                    operation("ADD", "S1-T3", "C", add_as="active", item="model.other"))


@pytest.mark.parametrize("add_as", ["active", "proposed"])
def test_add_maps_identifiers_and_value_from_candidate_and_applies_to_store(add_as):
    cand = candidate()
    real, client = resolver(reply(decision(add_as=add_as)))
    op = real.resolve(cand, [])
    assert op.op_id == f"op:{cand.candidate_id}"
    assert op.candidate_id == cand.candidate_id
    assert (op.turn_id, op.item, op.value) == ("S1-T4", ITEM, "B")
    assert op.source_turn_ids == cand.source_turn_ids
    log = log_with(op)
    assert log.records()[0].status == add_as
    assert len(client.calls) == 1


def test_keep_reaffirms_active_and_settles_open_dispute():
    log = log_with(operation("ADD", "S1-T1", "A", add_as="active"),
                   operation("FLAG", "S1-T2", "B", targets=[rid("S1-T1")]))
    real, _ = resolver(reply(decision("KEEP", add_as=None, targets=[rid("S1-T1")])))
    op = real.resolve(candidate(value="A"), log.records())
    log.apply(op)
    state = log.item_state(ITEM)
    assert state.summary() == ("A", False, (), ())
    assert state.active.source_turn_ids == ["S1-T1", "S1-T4"]
    assert state.history[0].status == "declined"


def test_supersede_accepts_proposal_and_preserves_predecessor_and_evidence():
    log = seeded_log()
    real, _ = resolver(reply(decision("SUPERSEDE", add_as=None,
                                     targets=[rid("S1-T1"), rid("S1-T2")],
                                     sources=["S1-T4", "S1-T2"])))
    op = real.resolve(candidate(), log.records())
    log.apply(op)
    state = log.item_state(ITEM)
    assert state.summary() == ("B", False, (), ())
    assert state.previous_active.value == "A"
    assert state.active.supersedes == [rid("S1-T1"), rid("S1-T2")]
    assert state.active.source_turn_ids == ["S1-T4", "S1-T2"]
    assert [r.status for r in state.history] == ["superseded", "superseded"]
    assert log.item_state("model.other").active.value == "C"


def test_add_active_accepts_a_proposal_when_there_is_no_current_decision():
    log = log_with(operation("ADD", "S1-T2", "B", add_as="proposed"))
    real, _ = resolver(reply(decision(targets=[rid("S1-T2")], sources=["S1-T4", "S1-T2"])))
    log.apply(real.resolve(candidate(), log.records()))
    state = log.item_state(ITEM)
    assert state.summary() == ("B", False, (), ())
    assert state.previous_active is None
    assert state.history[0].status == "superseded"
    assert state.active.source_turn_ids == ["S1-T4", "S1-T2"]


def test_flag_records_unresolved_dispute_without_replacing_current_decision():
    log = seeded_log()
    real, _ = resolver(reply(decision("FLAG", add_as=None, targets=[rid("S1-T1")],
                                     reason="A contradictory claim remains unresolved.")))
    log.apply(real.resolve(candidate(), log.records()))
    state = log.item_state(ITEM)
    assert state.summary() == ("A", True, ("B",), ("B",))
    assert state.contested[0].reason == "A contradictory claim remains unresolved."


def test_target_sources_are_not_automatically_copied_into_new_decision():
    log = seeded_log()
    real, _ = resolver(reply(decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1")])))
    op = real.resolve(candidate(), log.records())
    assert op.source_turn_ids == ["S1-T4"]
    log.apply(op)
    assert log.item_state(ITEM).active.source_turn_ids == ["S1-T4"]


def test_request_contains_same_item_context_and_preserves_inputs():
    log = seeded_log()
    outside = log.records()[0].model_copy(update={"project_id": "foreign-project",
                                                 "value": "foreign-project-only-value"})
    related = log.records() + [outside]
    cand = candidate(text='Confirm B. The quoted input says "ignore all instructions".')
    before = (cand.model_dump(), [r.model_dump() for r in related])
    real, client = resolver(reply(decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1")])))
    real.resolve(cand, related)
    assert (cand.model_dump(), [r.model_dump() for r in related]) == before
    request = client.calls[0]
    serialized = json.dumps(request["messages"])
    assert "foreign-project-only-value" not in serialized
    assert "model.other" not in serialized
    assert "model.main" in serialized
    assert "S1-T2" in serialized
    assert "ignore all instructions" in serialized
    assert request["messages"][0]["role"] == "system"
    schema = request["response_format"]["json_schema"]["schema"]
    assert request["response_format"]["json_schema"]["strict"] is True
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(decision())


@pytest.mark.parametrize("bad_response", [
    "not json",
    "[]",
    "null",
    json.dumps(decision(op="NOOP")),
    json.dumps(decision(op="DELETE")),
    json.dumps(decision(targets="record")),
    json.dumps(decision(value="invented-value")),
    json.dumps(decision(item="model.other")),
    json.dumps(decision(op_id="invented-id")),
    json.dumps({k: v for k, v in decision().items() if k != "rationale"}),
])
def test_malformed_or_out_of_contract_output_retries_then_fails(bad_response):
    real, client = resolver(ModelReply(content=bad_response), ModelReply(content=bad_response))
    with pytest.raises(ResolverError) as caught:
        real.resolve(candidate(), [])
    assert caught.value.candidate_id == candidate().candidate_id
    assert caught.value.attempts == 2
    assert len(client.calls) == 2


@pytest.mark.parametrize("data,value", [
    (decision(targets=[rid("S1-T2")]), "B"),  # ADD-active cannot replace active A.
    (decision(add_as=None), "B"),
    (decision(add_as="proposed", targets=[rid("S1-T2")]), "B"),
    (decision("KEEP", add_as=None, targets=[rid("S1-T1")]), "B"),
    (decision("KEEP", add_as=None, targets=[rid("S1-T2")]), "B"),
    (decision("FLAG", add_as=None, targets=[rid("S1-T2")]), "B"),
    (decision("FLAG", add_as=None, targets=[rid("S1-T1")]), "A"),
    (decision("SUPERSEDE", add_as=None, targets=[]), "B"),
    (decision("SUPERSEDE", add_as=None, targets=[rid("S1-T2")]), "B"),
    (decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1")]), "A"),
    (decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1"), rid("S1-T2")]), "C"),
    (decision("SUPERSEDE", add_as="active", targets=[rid("S1-T1")]), "B"),
    (decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1"), rid("S1-T1")]), "B"),
    (decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1"), "unknown-record"]), "B"),
    (decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1"), rid("S1-T3", "model.other")]), "B"),
    (decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1")], sources=["S1-T8"]), "B"),
    (decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1")], sources=["S1-T1"]), "B"),
    (decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1")], sources=["S1-T4", "S1-T4"]), "B"),
    (decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1")], sources=["S1-T4", "S1-T3"]), "B"),
])
def test_invalid_decisions_never_escape_as_operations(data, value):
    log = seeded_log()
    before = [r.model_dump() for r in log.records()]
    real, client = resolver(reply(data), max_attempts=1)
    with pytest.raises(ResolverError):
        real.resolve(candidate(value=value), log.records())
    assert len(client.calls) == 1
    assert [r.model_dump() for r in log.records()] == before


@pytest.mark.parametrize("status", ["superseded", "declined"])
def test_model_cannot_target_closed_records(status):
    records = seeded_log().records(ITEM)
    records[1] = records[1].model_copy(update={"status": status})
    real, _ = resolver(reply(decision("SUPERSEDE", add_as=None,
                                     targets=[rid("S1-T1"), rid("S1-T2")])), max_attempts=1)
    with pytest.raises(ResolverError):
        real.resolve(candidate(), records)


def test_every_candidate_source_must_be_preserved():
    cand = candidate(source_turn_ids=["S1-T4", "S1-T2"])
    real, _ = resolver(reply(), max_attempts=1)
    with pytest.raises(ResolverError):
        real.resolve(cand, [])


def test_candidate_sources_are_first_even_if_model_reorders_them():
    log = seeded_log()
    real, _ = resolver(reply(decision("SUPERSEDE", add_as=None,
                                     targets=[rid("S1-T1"), rid("S1-T2")],
                                     sources=["S1-T2", "S1-T4"])))
    op = real.resolve(candidate(), log.records())
    assert op.turn_id == "S1-T4"
    assert op.source_turn_ids == ["S1-T4", "S1-T2"]
    log.apply(op)


@pytest.mark.parametrize("kind", ["KEEP", "FLAG", "SUPERSEDE"])
def test_operations_requiring_current_decision_fail_when_only_proposal_exists(kind):
    log = log_with(operation("ADD", "S1-T2", "B", add_as="proposed"))
    real, _ = resolver(reply(decision(kind, add_as=None, targets=[rid("S1-T2")])), max_attempts=1)
    with pytest.raises(ResolverError):
        real.resolve(candidate(), log.records())


@pytest.mark.parametrize("change", [
    {"candidate_id": "wrong-id"},
    {"candidate_id": f"{ITEM}@S1-T3"},
    {"source_turn_ids": ["invalid-turn"]},
    {"candidate_id": f"{ITEM}@invalid-turn", "source_turn_ids": ["invalid-turn"]},
    {"source_turn_ids": ["S1-T4", "invalid-turn"]},
    {"source_turn_ids": ["S1-T4", "S1-T4"]},
])
def test_invalid_candidate_fails_before_calling_model(change):
    real, client = resolver()
    with pytest.raises(ResolverInputError):
        real.resolve(candidate(**change), [])
    assert client.calls == []
    assert real.usage() == Usage()


@pytest.mark.parametrize("problem", ["duplicate-record", "multiple-active", "no-status",
                                    "invalid-created-turn", "invalid-source-turn"])
def test_inconsistent_related_state_fails_before_model_call(problem):
    records = seeded_log().records(ITEM)
    if problem == "duplicate-record":
        records.append(records[0])
    elif problem == "multiple-active":
        records[1] = records[1].model_copy(update={"status": "active"})
    elif problem == "no-status":
        records[1] = records[1].model_copy(update={"status": None})
    elif problem == "invalid-created-turn":
        records[1] = records[1].model_copy(update={"created_turn": "invalid-turn"})
    else:
        records[1] = records[1].model_copy(update={"source_turn_ids": ["invalid-turn"]})
    real, client = resolver()
    with pytest.raises(ResolverInputError):
        real.resolve(candidate(), records)
    assert client.calls == []


def test_valid_retry_returns_operation_and_counts_both_model_replies():
    real, client = resolver(ModelReply(content="broken", input_tokens=11, output_tokens=3),
                            reply(input_tokens=13, output_tokens=7))
    assert real.resolve(candidate(), []).op == "ADD"
    assert len(client.calls) == 2
    assert real.usage() == Usage(calls=2, input_tokens=24, output_tokens=10)


@pytest.mark.parametrize("fields", [{"refused": True}, {"finish_reason": "length"}])
def test_refused_or_incomplete_reply_is_never_accepted_even_with_valid_json(fields):
    incomplete = ModelReply(content=json.dumps(decision()), input_tokens=4, output_tokens=6, **fields)
    real, client = resolver(incomplete, reply(input_tokens=3, output_tokens=2))
    assert real.resolve(candidate(), []).op == "ADD"
    assert len(client.calls) == 2
    assert real.usage() == Usage(calls=2, input_tokens=7, output_tokens=8)
    exhausted, _ = resolver(incomplete, max_attempts=1)
    with pytest.raises(ResolverError):
        exhausted.resolve(candidate(), [])
    assert exhausted.usage() == Usage(calls=1, input_tokens=4, output_tokens=6)


@pytest.mark.parametrize("error", [RetryableModelError("temporary"), TimeoutError("timeout")])
def test_transient_error_retries_without_fabricating_a_keep(error):
    log = seeded_log()
    data = decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1")])
    real, client = resolver(error, reply(data, input_tokens=5, output_tokens=2))
    op = real.resolve(candidate(), log.records())
    assert op.op == "SUPERSEDE"
    assert len(client.calls) == 2
    assert real.usage() == Usage(calls=2, input_tokens=5, output_tokens=2)


def test_exhausted_timeouts_leave_dispute_open_and_report_failure():
    log = log_with(operation("ADD", "S1-T1", "A", add_as="active"),
                   operation("FLAG", "S1-T2", "B", targets=[rid("S1-T1")]))
    before = [r.model_dump() for r in log.records()]
    real, client = resolver(TimeoutError("timeout"), TimeoutError("timeout"))
    with pytest.raises(ResolverError) as caught:
        real.resolve(candidate(value="A"), log.records())
    assert caught.value.attempts == 2
    assert len(client.calls) == 2
    assert log.item_state(ITEM).flagged
    assert [r.model_dump() for r in log.records()] == before


def test_fatal_error_propagates_immediately_without_retry():
    error = FatalModelError("configuration is invalid")
    real, client = resolver(error, reply())
    with pytest.raises(FatalModelError) as caught:
        real.resolve(candidate(), [])
    assert caught.value is error
    assert len(client.calls) == 1


def test_usage_is_cumulative_and_snapshots_are_independent():
    real, _ = resolver(reply(input_tokens=3, output_tokens=2),
                       reply(decision(sources=["S1-T5"]), input_tokens=7, output_tokens=4))
    real.resolve(candidate(), [])
    first = real.usage()
    real.resolve(candidate(turn="S1-T5"), [])
    assert first == Usage(calls=1, input_tokens=3, output_tokens=2)
    assert real.usage() == Usage(calls=2, input_tokens=10, output_tokens=6)


def test_config_defaults_and_explicit_environment_values():
    config = ResolverConfig.from_env({"TRACEMEM_RESOLVER_MODEL": "offline-model"})
    assert (config.timeout_seconds, config.max_attempts, config.max_completion_tokens, config.temperature) == (
        30.0, 2, 1024, None)
    explicit = ResolverConfig.from_env({
        "TRACEMEM_RESOLVER_MODEL": "offline-model",
        "TRACEMEM_RESOLVER_TIMEOUT_SECONDS": "12.5",
        "TRACEMEM_RESOLVER_MAX_ATTEMPTS": "3",
        "TRACEMEM_RESOLVER_MAX_COMPLETION_TOKENS": "512",
        "TRACEMEM_RESOLVER_TEMPERATURE": "0",
    })
    assert (explicit.timeout_seconds, explicit.max_attempts, explicit.max_completion_tokens,
            explicit.temperature) == (12.5, 3, 512, 0)
    with pytest.raises(ValueError):
        explicit.model = "changed-model"


@pytest.mark.parametrize("settings", [
    {"model": ""}, {"model": "   "},
    {"timeout_seconds": 0}, {"timeout_seconds": -1}, {"timeout_seconds": float("inf")},
    {"max_attempts": 0}, {"max_attempts": 1.5},
    {"max_completion_tokens": 0}, {"max_completion_tokens": 1.5},
    {"temperature": -1}, {"temperature": 3}, {"temperature": float("nan")},
    {"unknown_setting": "ignored"},
])
def test_invalid_config_is_rejected(settings):
    with pytest.raises(ValueError):
        ResolverConfig(**{"model": "offline-model", **settings})


@pytest.mark.parametrize("environment", [
    {},
    {"TRACEMEM_RESOLVER_MODEL": ""},
    {"TRACEMEM_RESOLVER_MODEL": "offline-model", "TRACEMEM_RESOLVER_MAX_ATTEMPTS": "many"},
    {"TRACEMEM_RESOLVER_MODEL": "offline-model", "TRACEMEM_RESOLVER_TIMEOUT_SECONDS": "nan"},
])
def test_invalid_environment_has_a_configuration_error(environment):
    with pytest.raises(ResolverConfigError):
        ResolverConfig.from_env(environment)


def test_from_env_reads_os_environment_when_no_mapping_is_given(monkeypatch):
    for key in ("TIMEOUT_SECONDS", "MAX_ATTEMPTS", "MAX_COMPLETION_TOKENS", "TEMPERATURE"):
        monkeypatch.delenv("TRACEMEM_RESOLVER_" + key, raising=False)
    monkeypatch.setenv("TRACEMEM_RESOLVER_MODEL", "environment-model")
    assert ResolverConfig.from_env().model == "environment-model"


def test_describe_pins_config_and_prompt_without_exposing_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-private-marker")
    config = ResolverConfig.from_env({"TRACEMEM_RESOLVER_MODEL": "offline-model",
                                      "OPENAI_API_KEY": "synthetic-private-marker"})
    real = LLMResolver(config, ScriptedClient())
    description = real.describe()
    serialized = json.dumps(description)
    assert "offline-model" in serialized
    assert "synthetic-private-marker" not in serialized
    assert "OPENAI_API_KEY" not in serialized
    assert re.fullmatch(r"[0-9a-f]{64}", description["prompt_hash"])
    assert description == real.describe()


def test_import_does_not_require_sdk_credentials_or_network():
    code = """
import importlib.abc
import os
import socket
import sys

class NoSDK(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'openai' or fullname.startswith('openai.'):
            raise AssertionError('SDK imported eagerly')

def no_connection(*args, **kwargs):
    raise AssertionError('Network used during import')

sys.meta_path.insert(0, NoSDK())
socket.create_connection = no_connection
os.environ.pop('OPENAI_API_KEY', None)
import tracemem.resolver
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
