"""Offline request-policy tests: legal targets and bounded correction feedback.

Scripted replies test the resolver boundary, not language-model decision quality.
Real development-run failure fixtures are covered separately.
"""

from __future__ import annotations

import json
import re

import pytest

import tracemem.resolver as resolver_module
from test_resolver import (
    ITEM, ScriptedClient, candidate, decision, log_with, operation, reply, resolver,
    rid, seeded_log,
)
from tracemem.resolver import LLMResolver, ModelReply, ResolverConfig, ResolverError
from tracemem.schema import Usage
from tracemem.systems.comparison import comparison_settings


def _payload(call):
    return json.loads(call["messages"][1]["content"])


def _feedback(call):
    assert len(call["messages"]) == 3
    assert call["messages"][2]["role"] == "user"
    result = json.loads(call["messages"][2]["content"])
    assert result["type"] == "resolver_validation_feedback"
    assert result["instruction"]
    assert result["target_constraints"] == _payload(call)["target_constraints"]
    return result


def _option(op, add_as=None, required=(), optional=()):
    return {"op": op, "add_as": add_as, "required_targets": list(required),
            "optional_targets": list(optional)}


@pytest.mark.parametrize("active_value", [None, "A", "B"])
def test_target_options_distinguish_first_confirmation_reaffirmation_and_revision(active_value):
    # All records belong to the same synthetic item. Closed B history and open C
    # proposals must never be offered as targets for the incoming value B.
    log = log_with(operation("ADD", "S1-T2", "B", add_as="proposed"),
                   operation("ADD", "S1-T3", "C", add_as="proposed"),
                   operation("ADD", "S1-T5", "B", add_as="proposed"),
                   operation("ADD", "S1-T6", "B", add_as="proposed"))
    records = log.records()
    records[2] = records[2].model_copy(update={"status": "superseded"})
    records[3] = records[3].model_copy(update={"status": "declined"})
    expected = [_option("ADD", "proposed")]
    if active_value is None:
        expected.append(_option("ADD", "active", optional=[rid("S1-T2")]))
    else:
        active = seeded_log().records(ITEM)[0].model_copy(update={"value": active_value})
        contested = records[0].model_copy(update={
            "record_id": rid("S1-T7"), "status": "contested",
            "created_turn": "S1-T7", "source_turn_ids": ["S1-T7"],
        })
        records.extend([active, contested])
        if active_value == "B":
            expected.append(_option("KEEP", required=[rid("S1-T1")]))
        else:
            expected.extend([
                _option("SUPERSEDE", required=[rid("S1-T1")],
                        optional=[rid("S1-T2"), rid("S1-T7")]),
                _option("FLAG", required=[rid("S1-T1")]),
            ])
    before = [record.model_dump() for record in records]
    # ADD-proposed remains available even when a settled operation is structurally
    # legal: the constraint list must not itself classify the dialogue's meaning.
    real, client = resolver(reply(decision(add_as="proposed", sources=["S1-T8"])))
    result = real.resolve(candidate(turn="S1-T8"), records)
    constraints = _payload(client.calls[0])["target_constraints"]
    assert constraints == {"active_record_id": rid("S1-T1") if active_value else None,
                           "options": expected}
    assert (result.op, result.add_as, result.targets) == ("ADD", "proposed", [])
    assert [record.model_dump() for record in records] == before


def test_empty_state_offers_add_with_no_targets_for_both_intents():
    real, client = resolver(reply())
    real.resolve(candidate(), [])
    assert _payload(client.calls[0])["target_constraints"] == {
        "active_record_id": None,
        "options": [_option("ADD", "proposed"), _option("ADD", "active")],
    }


def test_target_options_use_only_same_project_and_item_even_for_invalid_outside_records():
    records = seeded_log().records()
    foreign = records[0].model_copy(update={
        "project_id": "foreign-project", "record_id": "foreign-record",
        "status": None, "created_turn": "invalid-foreign-turn",
    })
    real, client = resolver(reply(decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1")])))
    real.resolve(candidate(), [foreign, *records])
    payload = _payload(client.calls[0])
    assert {r["record_id"] for r in payload["related"]} == {rid("S1-T1"), rid("S1-T2")}
    assert payload["target_constraints"] == {
        "active_record_id": rid("S1-T1"),
        "options": [
            _option("ADD", "proposed"),
            _option("SUPERSEDE", required=[rid("S1-T1")], optional=[rid("S1-T2")]),
            _option("FLAG", required=[rid("S1-T1")]),
        ],
    }
    assert "foreign-record" not in json.dumps(client.calls[0]["messages"])
    assert "model.other" not in json.dumps(client.calls[0]["messages"])


def test_retry_retains_structural_mistake_without_replaying_reason_or_rationale():
    marker = "rejected-free-text-must-not-be-replayed"
    invalid = decision("KEEP", add_as=None, targets=[rid("S1-T2")],
                       reason=marker * 2000, rationale=marker * 2000)
    corrected = decision("SUPERSEDE", add_as=None, targets=[rid("S1-T1")])
    real, client = resolver(reply(invalid), reply(corrected))
    assert real.resolve(candidate(), seeded_log().records()).op == "SUPERSEDE"
    feedback = _feedback(client.calls[1])
    assert client.calls[1]["messages"][:2] == client.calls[0]["messages"]
    assert feedback["error"] == "KEEP and FLAG must target exactly the active record"
    assert feedback["rejected_decision"] == {
        key: invalid[key] for key in ("op", "add_as", "targets", "source_turn_ids")
    }
    assert feedback["rejected_decision_truncated"] is False
    assert marker not in json.dumps(client.calls[1]["messages"])


@pytest.mark.parametrize("kind", ["malformed", "schema-invalid", "refused", "truncated"])
def test_untrusted_or_incomplete_response_never_becomes_rejected_decision(kind):
    marker = "unparsed-provider-content-must-not-be-replayed"
    content = json.dumps(decision(rationale=marker))
    if kind == "malformed":
        bad = ModelReply(content=marker * 2000)
    elif kind == "schema-invalid":
        bad = reply(decision(rationale=marker, unexpected_field=marker))
    elif kind == "refused":
        bad = ModelReply(content=content, refused=True)
    else:
        bad = ModelReply(content=content, finish_reason="length")
    real, client = resolver(bad, reply())
    real.resolve(candidate(), [])
    feedback = _feedback(client.calls[1])
    assert feedback["rejected_decision"] is None
    assert feedback["rejected_decision_truncated"] is False
    assert marker not in json.dumps(client.calls[1]["messages"])


def test_rejected_identifier_lists_and_strings_are_bounded_and_marked():
    invalid = decision(targets=["x" * 300, *[f"unknown-record-{i}" for i in range(40)]],
                       sources=["S1-T4", "y" * 300, *[f"S2-T{i}" for i in range(40)]])
    real, client = resolver(reply(invalid), reply())
    real.resolve(candidate(), [])
    feedback = _feedback(client.calls[1])
    rejected = feedback["rejected_decision"]
    assert feedback["rejected_decision_truncated"] is True
    assert set(rejected) == {"op", "add_as", "targets", "source_turn_ids"}
    for name in ("targets", "source_turn_ids"):
        assert len(rejected[name]) == 32
        assert all(len(identifier) <= 256 for identifier in rejected[name])
        assert rejected[name] == [identifier[:256] for identifier in invalid[name][:32]]


def test_five_attempts_keep_only_current_feedback_and_count_every_call():
    provider_marker = "private-transient-provider-error"
    invalid = decision(targets=["unknown-record"])
    real, client = resolver(
        reply(invalid, input_tokens=11, output_tokens=3),
        ModelReply(content="malformed-response-marker", input_tokens=13, output_tokens=5),
        ModelReply(content=json.dumps(decision()), refused=True, input_tokens=17, output_tokens=7),
        TimeoutError(provider_marker),
        reply(input_tokens=19, output_tokens=11),
        max_attempts=5,
    )
    assert real.resolve(candidate(), []).op == "ADD"
    assert real.usage() == Usage(calls=5, input_tokens=60, output_tokens=26)
    assert [len(call["messages"]) for call in client.calls] == [2, 3, 3, 3, 3]
    assert all(call["messages"][:2] == client.calls[0]["messages"] for call in client.calls)
    assert _feedback(client.calls[1])["rejected_decision"]["targets"] == ["unknown-record"]
    assert _feedback(client.calls[2])["rejected_decision"] is None
    assert _feedback(client.calls[3])["rejected_decision"] is None
    # A transient transport failure retries the exact pending correction request.
    assert client.calls[4]["messages"] == client.calls[3]["messages"]
    assert "unknown-record" not in json.dumps(client.calls[2]["messages"])
    all_messages = json.dumps([call["messages"] for call in client.calls])
    assert provider_marker not in all_messages
    assert "malformed-response-marker" not in all_messages


def test_five_invalid_attempts_fail_without_changing_storage_or_exceeding_budget():
    log = seeded_log()
    before = [record.model_dump() for record in log.records()]
    bad = reply(decision("KEEP", add_as=None, targets=[rid("S1-T2")]),
                input_tokens=2, output_tokens=3)
    real, client = resolver(*[bad] * 5, max_attempts=5)
    with pytest.raises(ResolverError) as caught:
        real.resolve(candidate(), log.records())
    assert caught.value.attempts == 5
    assert real.usage() == Usage(calls=5, input_tokens=10, output_tokens=15)
    assert len(client.calls) == 5
    assert [record.model_dump() for record in log.records()] == before
    assert all(len(call["messages"]) <= 3 for call in client.calls)


@pytest.mark.parametrize("first_fails", [False, True])
def test_feedback_does_not_leak_to_next_candidate_after_success_or_exhaustion(first_fails):
    bad = reply(decision(targets=["previous-candidate-only-record"]))
    real, client = resolver(bad, bad if first_fails else reply(),
                            reply(decision(sources=["S1-T5"])))
    if first_fails:
        with pytest.raises(ResolverError):
            real.resolve(candidate(), [])
    else:
        real.resolve(candidate(), [])
    next_candidate = candidate(turn="S1-T5")
    assert real.resolve(next_candidate, []).candidate_id == next_candidate.candidate_id
    assert len(client.calls[2]["messages"]) == 2
    assert _payload(client.calls[2])["candidate"]["candidate_id"] == next_candidate.candidate_id
    assert "previous-candidate-only-record" not in json.dumps(client.calls[2]["messages"])


@pytest.mark.parametrize("name,new_value", [
    ("RETRY_INSTRUCTION", "A changed offline feedback policy."),
    ("TARGET_POLICY_VERSION", "offline-target-policy-v2"),
    ("SOURCE_POLICY_VERSION", "offline-source-policy-v2"),
    ("FEEDBACK_MAX_IDS", 16),
    ("FEEDBACK_MAX_ID_CHARS", 128),
])
def test_manifest_fingerprint_tracks_feedback_policy_separately_from_prompt(monkeypatch, name, new_value):
    config = ResolverConfig(model="offline-model")
    client = ScriptedClient()
    real = LLMResolver(config, client)
    before = real.describe()
    assert re.fullmatch(r"[0-9a-f]{64}", before["decision_policy_hash"])
    assert LLMResolver(config, ScriptedClient()).describe() == before == real.describe()
    old_comparison = comparison_settings(config, 12000, client)
    assert old_comparison["resolver_reference_policy_hash"] == before["decision_policy_hash"]
    monkeypatch.setattr(resolver_module, name, new_value)
    after = real.describe()
    new_comparison = comparison_settings(config, 12000, client)
    assert after["decision_policy_hash"] != before["decision_policy_hash"]
    assert after["prompt_hash"] == before["prompt_hash"]
    assert after["output_schema_hash"] == before["output_schema_hash"]
    assert new_comparison["resolver_reference_policy_hash"] == after["decision_policy_hash"]
    assert client.calls == []
