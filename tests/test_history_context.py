"""History questions read every record that fits the budget (decision record 0016).

A previous or as_of question is not capped by TRACEMEM_CONTEXT_TOP_K: it gets every
record that fits the byte budget, closest first, shown in time order. When the budget
still leaves records out, the context's last line says how many, and that question's
request alone carries the rule: answer none only when nothing was left out. A current
question's request is byte for byte what the frozen code sent, so its answers and the
reply cache are unaffected.
"""

from __future__ import annotations

import json
import math
import tempfile
from copy import deepcopy
from datetime import timedelta

import pytest

from support import minimal_dict
from test_memory_comparison import HAS_MEM0, OfflineComparisonClient, observe_candidate
from test_model_client import VisibleStateClient
from test_retrieval import (CONFIG, FIXTURE_SETS, LINE, START, KeywordEmbedder, TableEmbedder, _pilot_record_sets,
                            ids, record)
from tracemem.eval import harness
from tracemem.eval.report import comparison_table
from tracemem.resolver import ModelReply
from tracemem.retrieval import SharedRetriever
from tracemem.schema import Scenario, ScenarioMeta, SystemQuestion, Turn
from tracemem.systems import comparison
from tracemem.systems.base import SystemSpec

HISTORY = [pytest.param("previous", None, id="previous"), pytest.param("as_of", "S1", id="as_of")]
RULE_PHRASE = "Answer none only when nothing was left out"


@pytest.fixture(autouse=True)
def native_temp_within_test_workspace(tmp_path, monkeypatch):
    # Mem0's native SDK writes temporary files; keep them in the test's own folder.
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))


class CaptureClient:
    """Abstains from every answer and keeps each request whole: config, messages and format."""

    def __init__(self):
        self.requests = []

    def complete(self, *, config, messages, response_format):
        self.requests.append({"config": config.model_dump(), "messages": deepcopy(messages),
                              "response_format": deepcopy(response_format)})
        return ModelReply(json.dumps({"status": "abstain", "value": None, "cited_turn_ids": [], "text": ""}))


def ask(kind="current", session=None, text="Which model did we use before the current one?"):
    return SystemQuestion(question_id="opaque", scenario_id="synthetic", kind=kind, text=text, session=session)


def payload(request):
    return json.loads(request["messages"][1]["content"])


# Six records of one item, made in order A to F; closeness to the query (axis 1):
# B 0.9, D 0.8, E 0.6, A 0.5, F 0.3, C 0.2. With the default speaker every line is
# 103 bytes, so budgets of three lines or more clear the 256-byte minimum.
CLOSENESS = {"A": 0.5, "B": 0.9, "C": 0.2, "D": 0.8, "E": 0.6, "F": 0.3}


def six(speaker="Speaker" * 8):
    records = [record(f"S1-T{n}", "model.x", value, at=START + timedelta(minutes=n), speaker=speaker)
               for n, value in enumerate("ABCDEF", start=1)]
    table = {f"= {value} ": [score, math.sqrt(1 - score ** 2)] for value, score in CLOSENESS.items()}
    return records, TableEmbedder(table)


def lines_budget(records, count):
    """Room for exactly count of these equal-length lines and the newlines between them."""
    sizes = {len(LINE(r).encode("utf-8")) for r in records}
    assert len(sizes) == 1
    return sizes.pop() * count + count - 1


def answer(kind, session, records, embedder, *, alpha=0.0, budget=12000, top_k=4):
    client = CaptureClient()
    retriever = SharedRetriever(alpha, 7.0, embedder)
    answerer = comparison.SharedAnswerer(CONFIG, client, budget_bytes=budget, retriever=retriever, top_k=top_k)
    answerer.answer(ask(kind, session), records, {}, latest=max(r.created_at for r in records))
    assert len(client.requests) == 1
    return client.requests[0]


def old_request(answerer, question, records, turns, latest):
    """The request the frozen code (0a7c65b) built: k caps every question, nothing else is added."""
    line = (lambda r: comparison._quoted_line(r, turns)) if answerer.quote_source_turns else comparison._line
    visible = answerer.retriever.select(question.text, records, latest, answerer.budget_bytes, line,
                                        top_k=answerer.top_k)
    context = "\n".join(line(r) for r in visible)
    sources = sorted({source for r in visible for source in r.source_turn_ids})
    return {"config": answerer.config.model_dump(), "messages": [
        {"role": "system", "content": comparison.ANSWER_PROMPT},
        {"role": "user", "content": json.dumps({
            "question": {"text": question.text, "kind": question.kind, "session": question.session},
            "context": context, "allowed_source_turn_ids": sources,
        }, ensure_ascii=False)}], "response_format": comparison.ANSWER_FORMAT}


def same_bytes(a, b):
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


# (a) More than k records that all fit: a history question sees them all.

@pytest.mark.parametrize("kind,session", HISTORY)
@pytest.mark.parametrize("alpha", [0.0, 0.3, 1.0])
def test_a_history_question_sees_every_record_that_fits_not_only_k(kind, session, alpha):
    records, embedder = six()
    context = payload(answer(kind, session, records, embedder, alpha=alpha))["context"]
    # All six, in time order, the order the context already uses.
    assert context.splitlines() == [LINE(r) for r in records]


def test_a_current_question_is_still_capped_at_k():
    records, embedder = six()
    context = payload(answer("current", None, records, embedder))["context"]
    # The four closest, B D E A, in time order.
    assert context.splitlines() == [LINE(records[i]) for i in (0, 1, 3, 4)]


# (b) More than the budget holds: what fits, closest first, and the "k of N" line.

@pytest.mark.parametrize("kind,session", HISTORY)
def test_a_history_question_over_the_budget_sees_the_closest_that_fit_and_is_told_how_many(kind, session):
    records, embedder = six()
    request = answer(kind, session, records, embedder, budget=lines_budget(records, 3))
    lines = payload(request)["context"].splitlines()
    # The three closest, B D E, in time order, then the line that says records were left out.
    assert lines[:-1] == [LINE(records[i]) for i in (1, 3, 4)]
    assert lines[-1] == "3 of 6 records shown; 3 left out to fit the context budget."
    assert payload(request)["allowed_source_turn_ids"] == ["S1-T2", "S1-T4", "S1-T5"]


@pytest.mark.parametrize("kind,session", HISTORY)
def test_newest_first_ranking_keeps_the_newest_that_fit_and_counts_the_rest(kind, session):
    records, embedder = six()
    lines = payload(answer(kind, session, records, embedder, alpha=1.0,
                           budget=lines_budget(records, 5)))["context"].splitlines()
    assert lines == [LINE(r) for r in records[1:]] + ["5 of 6 records shown; 1 left out to fit the context budget."]


@pytest.mark.parametrize("kind,session", HISTORY)
def test_a_history_question_with_no_room_for_any_record_is_told_so(kind, session):
    records, embedder = six(speaker="Speaker" * 40)
    assert all(len(LINE(r).encode("utf-8")) > 256 for r in records)
    request = answer(kind, session, records, embedder, budget=256)
    assert payload(request)["context"] == "0 of 6 records shown; 6 left out to fit the context budget."
    assert payload(request)["allowed_source_turn_ids"] == []


# (c) Nothing left out: no line and no rule.

@pytest.mark.parametrize("kind,session", HISTORY)
@pytest.mark.parametrize("top_k", [4, None])
def test_nothing_left_out_adds_no_line_and_no_rule(kind, session, top_k):
    records, embedder = six()
    request = answer(kind, session, records, embedder, top_k=top_k)
    assert payload(request)["context"].splitlines() == [LINE(r) for r in records]
    assert set(payload(request)) == {"question", "context", "allowed_source_turn_ids"}
    assert "records shown" not in json.dumps(request)


@pytest.mark.parametrize("kind,session", HISTORY)
@pytest.mark.parametrize("records", FIXTURE_SETS)
def test_a_history_question_whose_records_all_fit_within_k_sends_the_old_request(kind, session, records):
    # Nothing changes for such a question, so a saved reply still serves it.
    records = records[:4]
    client = CaptureClient()
    answerer = comparison.SharedAnswerer(CONFIG, client, budget_bytes=12000,
                                         retriever=SharedRetriever(0.0, 7.0, KeywordEmbedder()), top_k=4)
    question = ask(kind, session)
    answerer.answer(question, records, {})
    assert same_bytes(client.requests[0], old_request(answerer, question, records, {}, None))


# (d) A current question's request is byte for byte the frozen code's.

@pytest.mark.parametrize("records", FIXTURE_SETS + _pilot_record_sets())
@pytest.mark.parametrize("alpha,top_k,budget", [(1.0, None, 600), (1.0, None, 12000), (0.0, 4, 600),
                                                (0.0, 4, 12000), (0.3, 4, 600), (0.3, 4, 12000)])
def test_a_current_request_is_byte_identical_to_the_frozen_codes(records, alpha, top_k, budget):
    client = CaptureClient()
    answerer = comparison.SharedAnswerer(CONFIG, client, budget_bytes=budget,
                                         retriever=SharedRetriever(alpha, 7.0, KeywordEmbedder()), top_k=top_k)
    question = ask("current", text="Which model are we using?")
    latest = max((r.created_at for r in records), default=None)
    answerer.answer(question, records, {}, latest=latest)
    assert same_bytes(client.requests[0], old_request(answerer, question, records, {}, latest))


def test_a_current_request_quoting_source_turns_is_byte_identical_too():
    records, embedder = six()
    turns = {r.created_turn: Turn(id=r.created_turn, speaker="Ana", text=f"Let's use {r.value}.") for r in records}
    client = CaptureClient()
    answerer = comparison.SharedAnswerer(CONFIG, client, budget_bytes=400, retriever=SharedRetriever(0.0, 7.0, embedder),
                                         quote_source_turns=True, top_k=4)
    question = ask("current")
    answerer.answer(question, records, turns, latest=records[-1].created_at)
    assert same_bytes(client.requests[0], old_request(answerer, question, records, turns, records[-1].created_at))


# (e) The rule reaches history questions with records left out, never current ones.

@pytest.mark.parametrize("kind,session", HISTORY)
def test_the_history_rule_reaches_a_history_question_with_records_left_out(kind, session):
    records, embedder = six()
    request = answer(kind, session, records, embedder, budget=lines_budget(records, 3))
    rule = payload(request).get("history_rule", "")
    assert RULE_PHRASE in rule and "abstain" in rule
    # It travels with the question, not in the shared prompt every question gets.
    assert request["messages"][0]["content"] == comparison.ANSWER_PROMPT
    assert RULE_PHRASE not in comparison.ANSWER_PROMPT


@pytest.mark.parametrize("budget", [12000, 256])
def test_a_current_question_never_gets_the_rule_or_the_line_even_with_records_left_out(budget):
    records, embedder = six()
    request = answer("current", None, records, embedder, budget=budget)
    # Records are left out (by k at 12,000 bytes, by the budget at 256), yet nothing is added.
    assert len(payload(request)["context"].splitlines()) < len(records)
    assert set(payload(request)) == {"question", "context", "allowed_source_turn_ids"}
    assert RULE_PHRASE not in json.dumps(request) and "records shown" not in json.dumps(request)


SIX_SYSTEMS = [pytest.param(name, marks=pytest.mark.skipif(not HAS_MEM0, reason="needs the mem0 extra"))
               if name in comparison.MEM0_NAMES else name for name in comparison.NAMES]


def built(name, monkeypatch, budget):
    monkeypatch.setenv("TRACEMEM_CONTEXT_TOP_K", "4")
    client = OfflineComparisonClient()
    system = comparison.make_system(name, ScenarioMeta(scenario_id="synthetic", project_id="synthetic-project"),
                                    config=CONFIG, client=client, budget_bytes=budget, embedder=KeywordEmbedder())
    for n, value in enumerate(["BERT", "RoBERTa", "DistilBERT", "XLNet", "ALBERT", "ELECTRA"], start=1):
        observe_candidate(system, f"S1-T{n}", value)
    return system, client


def asked(system, client, kind):
    before = len(client.answer_calls())
    system.answer(SystemQuestion(question_id="opaque", scenario_id="synthetic", kind=kind,
                                 text="Which sentiment model was selected?", session="S1" if kind == "as_of" else None))
    return client.answer_calls()[before]


@pytest.mark.parametrize("name", SIX_SYSTEMS)
def test_every_system_shows_a_history_question_more_than_k_records_and_a_current_one_k(name, monkeypatch):
    system, client = built(name, monkeypatch, 12000)
    try:
        history = payload(asked(system, client, "previous"))["context"].splitlines()
        current = payload(asked(system, client, "current"))["context"].splitlines()
    finally:
        getattr(system, "close", lambda: None)()
    assert len(current) <= 4
    # Only the diagnostic without versions keeps too few records to need more than k.
    assert len(history) > 4 or name == "tracemem-no-versions"
    assert len(history) >= len(current)


@pytest.mark.parametrize("name", SIX_SYSTEMS)
def test_in_every_system_the_rule_reaches_only_history_questions(name, monkeypatch):
    system, client = built(name, monkeypatch, 256)
    try:
        requests = {kind: asked(system, client, kind) for kind in ("previous", "as_of", "current")}
    finally:
        getattr(system, "close", lambda: None)()
    for kind, request in requests.items():
        assert request["messages"][0]["content"] == comparison.ANSWER_PROMPT
        body = payload(request)
        left_out = "left out to fit the context budget" in body["context"]
        if kind == "current":
            assert not left_out and "history_rule" not in body
        else:
            # The rule comes exactly with the line, and only when the budget left records out.
            assert bool(left_out) == ("history_rule" in body)
    assert any("history_rule" in payload(requests[kind]) for kind in ("previous", "as_of")) \
        or name == "tracemem-no-versions"


# (f) The run records the rule, and the report will not mix runs before and after it.

def test_comparison_settings_record_the_history_policy_and_its_text():
    settings = comparison.comparison_settings(CONFIG, 12000, CaptureClient())
    assert settings["history_context_policy"] == "history_questions_all_that_fit_closest_first_left_out_line_v1"
    assert len(settings["history_rule_hash"]) == 64


@pytest.mark.parametrize("name,new_text", [("HISTORY_LEFT_OUT_RULE", "Other rule."),
                                           ("HISTORY_LEFT_OUT_LINE", "{shown}/{total} shown, {left_out} not.")])
def test_the_rule_and_line_text_change_only_their_own_fingerprint(name, new_text, monkeypatch):
    before = comparison.comparison_settings(CONFIG, 12000, CaptureClient())
    monkeypatch.setattr(comparison, name, new_text)
    after = comparison.comparison_settings(CONFIG, 12000, CaptureClient())
    assert {key for key in before if before[key] != after[key]} == {"history_rule_hash"}


def test_the_manifest_records_the_rule_and_the_report_refuses_a_run_from_before_it(tmp_path, monkeypatch):
    monkeypatch.setattr(harness, "_git", lambda *args: None)
    scenario = Scenario.model_validate(minimal_dict())

    def run(name):
        spec = SystemSpec(name, lambda meta, gold: comparison.make_system(
            name, meta, config=CONFIG, client=VisibleStateClient()), False, "offline history test")
        return harness.write_run(harness.run(spec, [scenario], "dev", condition="gold_candidates"), tmp_path / "runs")

    first, second = run("tracemem-controlled"), run("tracemem-no-versions")
    manifest = json.loads((second / "manifest.json").read_text(encoding="utf-8"))
    expected = comparison.comparison_settings(CONFIG, 12000, VisibleStateClient())
    assert manifest["comparison"]["history_context_policy"] == expected["history_context_policy"]
    assert manifest["comparison"]["history_rule_hash"] == expected["history_rule_hash"]
    assert comparison_table([first, second], n=20)
    # A run made before the change has neither key; it cannot be reported beside one made after.
    for key in ("history_context_policy", "history_rule_hash"):
        del manifest["comparison"][key]
    (second / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="shared inputs and models are required"):
        comparison_table([first, second], n=20)
