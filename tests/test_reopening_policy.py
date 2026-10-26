"""Offline policy boundaries using scripted replies, not model-accuracy claims."""
from datetime import datetime, timedelta
import json

import pytest

import tracemem.resolver as resolver_module
from tracemem.schema import Record, SystemQuestion
from tracemem.systems import comparison
from test_resolver import ScriptedClient, candidate, decision, log_with, operation, reply, resolver, rid


ITEM = "task.checks"


def memory(turn, value, status, *, item=ITEM, speaker="Planner"):
    session, index = (int(part[1:]) for part in turn.split("-"))
    return Record(record_id=rid(turn, item), project_id="synthetic-project", item=item, value=value,
                  status=status, created_turn=turn, created_at=datetime(2026, 1, session) + timedelta(minutes=index),
                  source_turn_ids=[turn], speakers=[speaker])


@pytest.mark.parametrize("text,op,add_as,value", [
    ("Should we restart the checks now that capacity is available?", "ADD", "proposed", "open"),
    ("There is time again; perhaps we could reopen the checks.", "ADD", "proposed", "open"),
    ("We have decided to reopen the checks, and work has restarted.", "SUPERSEDE", None, "open"),
    ("Following yesterday's cancellation, the checks are already running again today.", "SUPERSEDE", None, "open"),
    ("Please restart the checks today; you are assigned to this task.", "SUPERSEDE", None, "open"),
    ("That cancellation never happened; the checks are still open.", "FLAG", None, "open"),
    ("We are not reopening the checks; they remain cancelled.", "KEEP", None, "cancelled"),
])
def test_scripted_reopening_acts_preserve_history_and_do_not_use_keyword_overrides(text, op, add_as, value):
    log = log_with(operation("ADD", "S1-T1", "open", add_as="active", item=ITEM),
                   operation("SUPERSEDE", "S1-T2", "cancelled", targets=[rid("S1-T1", ITEM)], item=ITEM))
    cand = candidate(item=ITEM, candidate_id=rid("S1-T4", ITEM), text=text, value=value)
    scripted = decision(op, add_as=add_as, targets=[] if op == "ADD" else [rid("S1-T2", ITEM)])
    real, client = resolver(reply(scripted))

    log.apply(real.resolve(cand, log.records()))

    state = log.item_state(ITEM)
    assert state.active.value == ("open" if op == "SUPERSEDE" else "cancelled")
    assert state.flagged is (op == "FLAG")
    assert [record.value for record in state.proposed] == (["open"] if op == "ADD" else [])
    assert next(record for record in log.records() if record.record_id == rid("S1-T1", ITEM)).status == "superseded"
    assert len(client.calls) == real.usage().calls == 1
    prompt = client.calls[0]["messages"][0]["content"]
    assert prompt.endswith(resolver_module.TRANSITION_EVIDENCE_GUIDE)
    assert prompt.index(resolver_module.INTENT_GUIDE) < prompt.index(resolver_module.TRANSITION_EVIDENCE_GUIDE)
    evidence = json.loads(client.calls[0]["messages"][1]["content"])
    assert set(evidence) == {"candidate", "related", "target_constraints"}
    assert evidence["candidate"] == cand.model_dump(mode="json")
    assert set(client.calls[0]["response_format"]["json_schema"]["schema"]["properties"]) == {
        "op", "add_as", "targets", "source_turn_ids", "reason", "rationale",
    }


ANSWER_CASES = [
    pytest.param([memory("S2-T1", "cancelled", "active"), memory("S3-T1", "open", "proposed")],
                 "current", None, "answer", "cancelled", ["S2-T1"], id="cancelled-plus-proposal"),
    pytest.param([memory("S2-T1", "completed", "active"), memory("S3-T1", "open", "proposed")],
                 "current", None, "answer", "completed", ["S2-T1"], id="completed-plus-proposal"),
    pytest.param([memory("S2-T1", "cancelled", "active"), memory("S3-T1", "open", "contested")],
                 "current", None, "conflict", None, ["S2-T1", "S3-T1"], id="genuine-contested-state"),
    pytest.param([memory("S2-T1", "cancelled", "active"), memory("S3-T1", "open", "proposed"),
                  memory("S3-T2", "open", "contested", item="task.other")],
                 "current", None, "answer", "cancelled", ["S2-T1"], id="unrelated-dispute"),
    pytest.param([memory("S2-T1", "cancelled", "superseded"), memory("S3-T1", "open", "active")],
                 "current", None, "answer", "open", ["S3-T1"], id="confirmed-reopening"),
    pytest.param([memory("S1-T1", "open", "superseded"), memory("S2-T1", "cancelled", "active"),
                  memory("S3-T1", "open", "proposed")],
                 "as_of", "S1", "answer", "open", ["S1-T1"], id="as-of-before-cancellation"),
    pytest.param([memory("S1-T1", "open", "superseded"), memory("S2-T1", "cancelled", "active"),
                  memory("S3-T1", "open", "proposed")],
                 "previous", None, "answer", "open", ["S1-T1", "S2-T1"], id="proposal-not-a-new-version"),
    pytest.param([memory("S3-T1", "open", "proposed")],
                 "previous", None, "abstain", None, [], id="missing-history"),
]


@pytest.mark.parametrize("records,kind,session,status,value,cited", ANSWER_CASES)
def test_scripted_answers_distinguish_record_state_from_task_value_and_requested_time(
    records, kind, session, status, value, cited,
):
    question = SystemQuestion(question_id="opaque", scenario_id="synthetic", kind=kind, session=session,
                              text="What is the requested status of the checks?")
    client = ScriptedClient(reply({"status": status, "value": value, "cited_turn_ids": cited, "text": "Scripted boundary case."}))
    answerer = comparison.SharedAnswerer(resolver_module.ResolverConfig(model="offline-model"), client)
    before = [record.model_dump() for record in records]

    answer = answerer.answer(question, records, {"S9-T9": "UNRETRIEVED_TRANSCRIPT_SENTINEL"})

    assert (answer.status, answer.value, answer.cited_turn_ids) == (status, value, cited)
    assert len(client.calls) == answerer.usage().calls == 1
    assert [record.model_dump() for record in records] == before
    prompt = client.calls[0]["messages"][0]["content"]
    assert prompt == comparison.ANSWER_PROMPT
    assert comparison.ANSWER_STATE_GUIDE in prompt
    assert prompt.index(comparison.ANSWER_STATE_GUIDE) < prompt.index("Return a JSON object")
    payload = json.loads(client.calls[0]["messages"][1]["content"])
    assert set(payload) == {"question", "context", "allowed_source_turn_ids"}
    assert payload["question"] == {"text": question.text, "kind": kind, "session": session}
    context, sources = comparison.answer_context(records, 12000)
    assert (payload["context"], payload["allowed_source_turn_ids"]) == (context, sources)
    assert "UNRETRIEVED_TRANSCRIPT_SENTINEL" not in json.dumps(payload)
    assert set(client.calls[0]["response_format"]["json_schema"]["schema"]["properties"]) == {
        "status", "value", "cited_turn_ids", "text",
    }


def test_budget_omitted_cancellation_is_not_reintroduced_by_state_guidance():
    records = [memory("S2-T1", "cancelled", "active", speaker="X" * 400),
               memory("S3-T1", "open", "proposed")]
    client = ScriptedClient(reply({"status": "abstain", "value": None, "cited_turn_ids": [], "text": "Missing settled evidence."}))
    answerer = comparison.SharedAnswerer(resolver_module.ResolverConfig(model="offline-model"), client, budget_bytes=256)
    question = SystemQuestion(question_id="opaque", scenario_id="synthetic", kind="current", text="What is the checks status?")

    answer = answerer.answer(question, records, {})

    payload = json.loads(client.calls[0]["messages"][1]["content"])
    assert len(payload["context"].encode("utf-8")) <= 256
    assert "cancelled" not in payload["context"]
    assert "open [proposed]" in payload["context"]
    assert payload["allowed_source_turn_ids"] == answer.context_turn_ids == ["S3-T1"]
    assert answer.status == "abstain" and answer.value is None


def test_shared_state_guide_keeps_native_mem0_text_without_inventing_statuses():
    records = [memory("S2-T1", "Current Mem0 memory: The checks are cancelled; reopening was only suggested.", None)]
    client = ScriptedClient(reply({"status": "answer", "value": "cancelled", "cited_turn_ids": ["S2-T1"], "text": "Scripted native evidence."}))
    answerer = comparison.SharedAnswerer(resolver_module.ResolverConfig(model="offline-model"), client)
    question = SystemQuestion(question_id="opaque", scenario_id="synthetic", kind="current", text="What is the checks status?")

    assert answerer.answer(question, records, {}).value == "cancelled"

    assert client.calls[0]["messages"][0]["content"] == comparison.ANSWER_PROMPT
    context = json.loads(client.calls[0]["messages"][1]["content"])["context"]
    assert records[0].value in context
    assert all(f"[{status}]" not in context for status in ("active", "proposed", "contested"))
    assert records[0].status is None


@pytest.mark.parametrize("module,key,hash_key", [
    (resolver_module, "SYSTEM_PROMPT", "resolver_reference_prompt_hash"),
    (comparison, "ANSWER_PROMPT", "answer_prompt_hash"),
])
def test_reopening_write_and_read_guides_have_independent_comparison_fingerprints(monkeypatch, module, key, hash_key):
    config = resolver_module.ResolverConfig(model="offline-model")
    client = ScriptedClient()
    before = comparison.comparison_settings(config, 12000, client)

    monkeypatch.setattr(module, key, getattr(module, key) + "\nAlternate offline guide.")

    after = comparison.comparison_settings(config, 12000, client)
    assert {name for name in before if before[name] != after[name]} == {hash_key}
    assert client.calls == []
