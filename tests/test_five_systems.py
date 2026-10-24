"""Offline checks of the five compared systems and of the three added to the first two.

The five are similarity, similarity + recency, Mem0 classic, Mem0 with project
instructions and TraceMem. Model replies are scripted as in test_memory_comparison.py;
embeddings come from conftest.py's offline embedder unless a test supplies its own,
so no model or embedding server is needed. Mem0 tests run the real pinned SDK.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
from datetime import datetime, timedelta
from importlib.metadata import PackageNotFoundError, version
from types import ModuleType, SimpleNamespace

import pytest

from support import pilot, pilot_timeline
from test_mem0_baseline import Client, candidate as mem0_candidate, response, time as mem0_time
from test_memory_comparison import OfflineComparisonClient, close, observe_candidate, question
from tracemem import cli, resolver
from tracemem.eval import harness
from tracemem.eval.report import comparison_table
from tracemem.model_client import LOCAL_BASE_URL
from tracemem.resolver import ResolverConfig, ResolverConfigError, ResolverInputError
from tracemem.retrieval import OllamaEmbeddings
from tracemem.schema import Candidate, ScenarioMeta, Turn, Usage
from tracemem.systems import REGISTRY, comparison, mem0_baseline
from tracemem.systems.mem0_baseline import PROJECT_RULES, Mem0Backend

FIVE = ("similarity", "similarity-recency", "mem0-classic", "mem0-instructions", "tracemem-controlled")
NEW = ("similarity", "similarity-recency", "mem0-instructions")
SIMILARITY = ("similarity", "similarity-recency")
CONFIG = ResolverConfig(model="offline-five", max_attempts=2)
# Captured at import, before conftest.py replaces it for each test.
REAL_MAKE_EMBEDDER = comparison.make_embedder
try:
    version("mem0ai")
    HAS_MEM0 = True
except PackageNotFoundError:
    HAS_MEM0 = False
needs_mem0 = pytest.mark.skipif(not HAS_MEM0, reason="install the optional mem0 extra to run the native SDK")


def cases(names):
    return [pytest.param(name, marks=needs_mem0 if name in comparison.MEM0_NAMES else ()) for name in names]


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


@pytest.fixture(autouse=True)
def native_temp_within_test_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))


@pytest.fixture
def offline(monkeypatch):
    clients = []

    def make_client():
        clients.append(OfflineComparisonClient())
        return clients[-1]

    monkeypatch.setattr(ResolverConfig, "from_env", classmethod(lambda cls: CONFIG))
    monkeypatch.setattr(comparison, "make_client", make_client)
    monkeypatch.delenv("TRACEMEM_CONTEXT_BUDGET_BYTES", raising=False)
    return clients


def run_pilot(name, condition="gold_candidates"):
    return harness.run(REGISTRY[name], [pilot("pilot-01")], "dev", condition=condition)


def update_requests(client):
    return [call["messages"] for call in client.calls if call["response_format"]["type"] == "json_object"]


# Registration and inputs

def test_the_five_systems_are_registered_without_gold_and_listing_builds_nothing(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("Listing systems must not build model clients, embedders or settings")

    monkeypatch.setattr(comparison, "make_client", forbidden)
    monkeypatch.setattr(comparison, "make_embedder", forbidden)
    monkeypatch.setattr(ResolverConfig, "from_env", forbidden)
    assert cli.main(["systems"]) == 0
    listed = {line.split()[0] for line in capsys.readouterr().out.splitlines() if line.strip()}
    assert set(FIVE) | {"tracemem-no-versions"} <= listed
    for name in FIVE:
        assert name in comparison.NAMES and REGISTRY[name].uses_gold is False


@pytest.mark.parametrize("name", cases(NEW))
def test_new_systems_refuse_end_to_end_without_calling_a_model(name, offline, offline_embedders):
    with pytest.raises(harness.RunAborted) as caught:
        run_pilot(name, condition="end_to_end")
    assert caught.value.result.failure["error_type"] == "ResolverConfigError"
    assert "gold_candidates" in caught.value.result.failure["message"]
    assert all(not client.calls for client in offline)
    assert all(not embedder.queries and not embedder.documents for embedder in offline_embedders)


@pytest.mark.parametrize("name", NEW)
def test_new_factories_reject_a_gold_timeline(name):
    with pytest.raises(ResolverInputError, match="gold"):
        comparison.factory(name)(pilot("pilot-01").meta(), pilot_timeline("pilot-01"))


@pytest.mark.parametrize("name", cases(NEW))
def test_new_systems_receive_only_candidates_and_public_questions(name, offline, monkeypatch):
    received = []
    create = comparison.make_system

    def spy(system_name, meta, *args, **kwargs):
        received.append((system_name, meta, args, kwargs))
        return create(system_name, meta, *args, **kwargs)

    monkeypatch.setattr(comparison, "make_system", spy)
    result = run_pilot(name)
    # The factory gets the scenario's public description only, never the timeline.
    (system_name, meta, args, kwargs), = received
    assert (system_name, args, kwargs) == (name, (), {}) and meta == pilot("pilot-01").meta()
    expected = [candidate.model_dump() for candidates in pilot_timeline("pilot-01").candidates_by_turn.values()
                for candidate in candidates]
    assert [candidate.model_dump() for candidate in result.candidates["pilot-01"]] == expected
    answers = offline[0].answer_calls()
    assert len(answers) == len(result.rows) == len(pilot_timeline("pilot-01").questions)
    for call in answers:
        payload = json.loads(call["messages"][1]["content"])
        assert set(payload) == {"question", "context", "allowed_source_turn_ids"}
        assert set(payload["question"]) == {"text", "kind", "session"}


# Running pilot-01

@needs_mem0
def test_the_five_systems_run_pilot_01_to_completion_and_can_be_reported_together(offline, tmp_path):
    folders = []
    for name, client_count in zip(FIVE, range(1, len(FIVE) + 1)):
        result = run_pilot(name)
        assert len(offline) == client_count  # one fresh model client per system and scenario
        assert result.status == "completed" and result.uses_gold is False
        assert len(result.rows) == len(pilot_timeline("pilot-01").questions)
        folders.append(harness.write_run(result, tmp_path))
        usage = json.loads((folders[-1] / "usage.json").read_text(encoding="utf-8"))
        assert usage["resolver"]["total"]["calls"] + usage["answer"]["total"]["calls"] == len(offline[-1].calls)
    manifests = [json.loads((folder / "manifest.json").read_text(encoding="utf-8")) for folder in folders]
    assert all(manifest["comparison"] == manifests[0]["comparison"] for manifest in manifests)
    assert [manifest["system_config"]["quote_source_turns"] for manifest in manifests] == [True, True, False, False, False]
    assert [manifest["system_config"]["shared_retriever"]["alpha"] for manifest in manifests] == [0.0, 0.3, 1.0, 1.0, 1.0]
    table = comparison_table(folders, n=10)
    assert all(name in table for name in FIVE) and "uses gold labels" not in table
    # One answer prompt, schema and model configuration for all five.
    answers = [call for client in offline for call in client.answer_calls()]
    assert len({call["messages"][0]["content"] for call in answers}) == 1
    assert all(call["response_format"] == comparison.ANSWER_FORMAT for call in answers)
    assert all(call["config"] == CONFIG.model_dump() for client in offline for call in client.calls)


@pytest.mark.parametrize("name", SIMILARITY)
def test_similarity_systems_make_no_write_calls(name, offline, offline_embedders, tmp_path):
    result = run_pilot(name)
    client, = offline
    assert client.calls and client.answer_calls() == client.calls
    assert result.resolver_usage["pilot-01"] == Usage()
    assert result.answer_usage["pilot-01"].calls == len(client.calls)
    assert "pilot-01" not in result.operations and result.resolver_scores is None
    assert not result.resolver_events and not result.memory_events
    folder = harness.write_run(result, tmp_path)
    assert not (folder / "ops.jsonl").exists() and not (folder / "resolver_events.jsonl").exists()
    # One query and one embedding batch per question, from this scenario's own embedder.
    embedder, = offline_embedders
    assert len(embedder.queries) == len(embedder.documents) == len(result.rows)
    assert result.system_config["write_path"] == "none"
    assert result.system_config["memory_policy"] == "flat_candidate_records"


@pytest.mark.parametrize("name", SIMILARITY)
def test_similarity_store_is_every_candidate_without_status(name, offline):
    run_pilot(name)
    contexts = [json.loads(call["messages"][1]["content"])["context"] for call in offline[0].answer_calls()]
    final = contexts[-1].splitlines()
    candidates = [candidate for candidates in pilot_timeline("pilot-01").candidates_by_turn.values()
                  for candidate in candidates]
    # pilot-01 fits the default budget whole: one line per candidate, quoting its own turn.
    assert sorted(line.split(' "', 1)[0] for line in final) == sorted(
        f"{c.source_turn_ids[0]} {c.speaker}: {c.item} = {c.value}" for c in candidates)
    assert all(f'"{c.text}" | sources={c.source_turn_ids[0]}' in contexts[-1] for c in candidates)
    assert not any(f"[{status}]" in context for context in contexts
                   for status in ("active", "proposed", "contested", "superseded", "declined"))


# Context lines

def test_similarity_lines_quote_the_source_turn_and_the_other_arms_lines_do_not():
    lines = {}
    for name in ("similarity", "tracemem-controlled"):
        client = OfflineComparisonClient()
        system = comparison.make_system(name, pilot("pilot-01").meta(), config=CONFIG, client=client)
        try:
            observe_candidate(system, "S1-T1", "BERT", raw_suffix="QUOTED_SOURCE_SENTINEL")
            system.answer(question())
        finally:
            close(system)
        payload = json.loads(client.answer_calls()[-1]["messages"][1]["content"])
        lines[name] = payload["context"]
        assert payload["allowed_source_turn_ids"] == ["S1-T1"]
    assert lines["similarity"] == ('S1-T1 Planner: model.sentiment = BERT "We confirm BERT. QUOTED_SOURCE_SENTINEL"'
                                   " | sources=S1-T1")
    assert lines["tracemem-controlled"] == "S1-T1 Planner: model.sentiment = BERT [active] | sources=S1-T1"


def test_the_budget_counts_the_quoted_line():
    # Without its quote the line fits 256 bytes; with it, it does not, so it is left out whole.
    contexts = {}
    for name in ("similarity", "tracemem-controlled"):
        client = OfflineComparisonClient()
        system = comparison.make_system(name, pilot("pilot-01").meta(), config=CONFIG, client=client,
                                        budget_bytes=256)
        try:
            observe_candidate(system, "S1-T1", "BERT", raw_suffix="x" * 240)
            answer = system.answer(question())
        finally:
            close(system)
        contexts[name] = json.loads(client.answer_calls()[-1]["messages"][1]["content"])["context"], answer
    assert contexts["similarity"][0] == "" and contexts["similarity"][1].context_turn_ids == []
    assert contexts["tracemem-controlled"][0].startswith("S1-T1 Planner: model.sentiment = BERT")


# The two similarity systems differ only in their retrievers

class MarkerEmbedder:
    """The query on the first axis; a line about BERT scores 1 against it, any other 0.9."""

    def embed_query(self, text):
        return [1.0, 0.0]

    def embed_documents(self, texts):
        return [[1.0, 0.0] if "= BERT " in text else [0.9, math.sqrt(1 - 0.81)] for text in texts]


def selected(name, embedder):
    client = OfflineComparisonClient()
    system = comparison.make_system(name, pilot("pilot-01").meta(), config=CONFIG, client=client,
                                    budget_bytes=256, embedder=embedder)
    start = datetime(2026, 1, 5, 10)
    try:
        for turn, value, when in (("S1-T1", "BERT", start), ("S2-T1", "DistilBERT", start + timedelta(days=30))):
            text = f"We confirm {value}. " + "y" * 120  # one line fits the budget, two do not
            candidate = Candidate(candidate_id=f"model.sentiment@{turn}", project_id=system.meta.project_id,
                                  item="model.sentiment", value=value, source_turn_ids=[turn], speaker="Planner",
                                  text=text)
            system.observe(Turn(id=turn, speaker="Planner", text=text), when, gold_candidates=[candidate])
        return system.answer(question()).context_turn_ids
    finally:
        close(system)


def test_similarity_takes_the_closest_record_and_the_recency_mix_the_newer_one():
    # Alpha 0: 1.0 against 0.9. Alpha 0.3 with a 7-day half-life, 30 days apart:
    # 0.7 * 1.0 + 0.3 * 0.5 ** (30 / 7) = 0.715 against 0.7 * 0.9 + 0.3 = 0.93.
    assert selected("similarity", MarkerEmbedder()) == ["S1-T1"]
    assert selected("similarity-recency", MarkerEmbedder()) == ["S2-T1"]
    assert comparison.SIMILARITY_RETRIEVERS == {"similarity": (0.0, 7.0), "similarity-recency": (0.3, 7.0)}


def test_recency_is_measured_to_the_latest_observed_turn(offline_embedders):
    system = comparison.make_system("similarity-recency", pilot("pilot-01").meta(), config=CONFIG,
                                    client=OfflineComparisonClient())
    seen = []
    select = system.answerer.retriever.select

    def spy(question_text, records, latest, budget_bytes, line):
        seen.append(latest)
        return select(question_text, records, latest, budget_bytes, line)

    system.answerer.retriever.select = spy
    observe_candidate(system, "S1-T1", "BERT")
    # A turn without a candidate is still the latest observed turn.
    system.observe(Turn(id="S1-T2", speaker="Planner", text="No decision here."), datetime(2026, 1, 1, 0, 9),
                   gold_candidates=[])
    system.answer(question())
    assert seen == [datetime(2026, 1, 1, 0, 9)]
    assert system.answerer.retriever.embedder is offline_embedders[-1]


def test_answering_leaves_the_similarity_store_unchanged():
    system = comparison.make_system("similarity", pilot("pilot-01").meta(), config=CONFIG,
                                    client=OfflineComparisonClient())
    empty = system.fingerprint()
    observe_candidate(system, "S1-T1", "BERT")
    before = system.fingerprint()
    system.answer(question())
    assert system.fingerprint() == before != empty


def test_similarity_systems_embed_through_the_local_server_by_default(monkeypatch, tmp_path, offline_embedders):
    system = comparison.make_system("similarity", pilot("pilot-01").meta(), config=CONFIG,
                                    client=OfflineComparisonClient())
    assert system.answerer.retriever.embedder is offline_embedders[0]
    assert comparison.make_system("tracemem-controlled", pilot("pilot-01").meta(), config=CONFIG,
                                  client=OfflineComparisonClient()).answerer.retriever.embedder is None
    assert len(offline_embedders) == 1  # recency alone needs no embedder
    module = ModuleType("openai")
    module.OpenAI = lambda **kwargs: SimpleNamespace(settings=kwargs)
    monkeypatch.setitem(sys.modules, "openai", module)
    for setting in ("TRACEMEM_LOCAL_BASE_URL", "TRACEMEM_EMBED_MODEL", "TRACEMEM_LOCAL_API_KEY"):
        monkeypatch.delenv(setting, raising=False)
    monkeypatch.chdir(tmp_path)
    embedder = REAL_MAKE_EMBEDDER()
    assert isinstance(embedder, OllamaEmbeddings)
    assert (embedder.base_url, embedder.model) == (LOCAL_BASE_URL, "nomic-embed-text")


# Mem0 with project instructions

def test_the_project_rules_are_passages_of_the_resolver_intent_guide():
    header, *rules = PROJECT_RULES.splitlines()
    assert header == ("Project rules. They were written for a memory whose operations are ADD-proposed, "
                      "ADD-active, FLAG, KEEP and SUPERSEDE; apply their intent using ADD, UPDATE, DELETE and NONE.")
    guide = resolver.INTENT_GUIDE.splitlines()
    # Each rule line is a whole guide line, or its start where item 2 stops after a sentence.
    assert all(any(line == source or source.startswith(line + " ") for source in guide) for line in rules)
    assert len(rules) == 18 and PROJECT_RULES.endswith("does not confirm it.\n")


@needs_mem0
def test_mem0_instructions_send_the_default_update_prompt_then_the_rules_and_classic_the_default_alone():
    from mem0.configs.prompts import DEFAULT_UPDATE_MEMORY_PROMPT, get_update_memory_messages

    requests = {}
    for name in comparison.MEM0_NAMES:
        client = OfflineComparisonClient()
        system = comparison.make_system(name, pilot("pilot-01").meta(), config=CONFIG, client=client)
        try:
            first = observe_candidate(system, "S1-T1", "BERT")
            observe_candidate(system, "S1-T2", "DistilBERT")
        finally:
            close(system)
        requests[name] = update_requests(client)
    classic, instructed = requests["mem0-classic"], requests["mem0-instructions"]
    assert len(classic) == len(instructed) == 2
    fact = json.dumps(first.model_dump(), ensure_ascii=False, sort_keys=True)
    assert classic[0] == [{"role": "user", "content": get_update_memory_messages([], [fact])}]
    # The SDK puts the custom prompt where its default would be; the rest is unchanged.
    assert DEFAULT_UPDATE_MEMORY_PROMPT.endswith("\n")
    head = DEFAULT_UPDATE_MEMORY_PROMPT + "\n" + PROJECT_RULES
    for plain, ruled in zip(classic, instructed):
        assert plain[0]["content"].count(DEFAULT_UPDATE_MEMORY_PROMPT) == 1
        assert PROJECT_RULES not in plain[0]["content"]
        assert ruled == [{"role": "user", "content": plain[0]["content"].replace(DEFAULT_UPDATE_MEMORY_PROMPT, head, 1)}]
        assert ruled[0]["content"].startswith(DEFAULT_UPDATE_MEMORY_PROMPT + "\nProject rules. They were written")


@needs_mem0
def test_mem0_descriptions_record_the_rules_hash_and_the_update_prompt_hash():
    from mem0.configs.prompts import DEFAULT_UPDATE_MEMORY_PROMPT, get_update_memory_messages

    described = {}
    for name in comparison.MEM0_NAMES:
        system = comparison.make_system(name, pilot("pilot-01").meta(), config=CONFIG, client=OfflineComparisonClient())
        try:
            described[name] = system.describe()
        finally:
            close(system)
    classic, instructed = described["mem0-classic"], described["mem0-instructions"]
    assert classic["backend"]["update_prompt_hash"] == sha256(get_update_memory_messages([], []))
    assert instructed["backend"]["update_prompt_hash"] == sha256(
        get_update_memory_messages([], [], DEFAULT_UPDATE_MEMORY_PROMPT + "\n" + PROJECT_RULES))
    assert (classic["backend"]["update_prompt"], classic["backend"]["instructions_hash"]) == ("sdk_default", None)
    assert (instructed["backend"]["update_prompt"], instructed["backend"]["instructions_hash"]) == (
        "sdk_default_then_instructions", sha256(PROJECT_RULES))
    assert classic["memory_policy"] == "mem0_classic_with_native_history"
    assert instructed["memory_policy"] == "mem0_classic_with_native_history_and_project_rules"
    assert classic["comparison"] == instructed["comparison"]


@needs_mem0
def test_no_code_enforces_the_project_rules():
    # Replacing a settled choice because of a mere suggestion breaks rule 2; both arms apply it alike.
    outcomes = []
    for instructions in (None, PROJECT_RULES):
        client = Client(response(text="BERT is the chosen model"),
                        response("UPDATE", "DistilBERT is the chosen model", old="BERT is the chosen model"))
        backend = Mem0Backend(ScenarioMeta(scenario_id="fixture", project_id="synthetic-project"), CONFIG, client,
                              instructions=instructions)
        try:
            backend.add(mem0_candidate(1, text="We will use BERT."), mem0_time(1))
            backend.add(mem0_candidate(2, value="DistilBERT", text="Maybe we could try DistilBERT?"), mem0_time(2))
            outcomes.append(([(record.item, record.value, record.source_turn_ids, record.created_turn)
                              for record in backend.records()],
                             [(event["status"], [(action["event"], action.get("memory", action.get("text")))
                                                 for action in event["actions"]]) for event in backend.events()]))
        finally:
            backend.close()
    assert outcomes[0] == outcomes[1]
    assert "Current Mem0 memory: DistilBERT is the chosen model" in [value for _, value, _, _ in outcomes[1][0]]


def test_mem0_instructions_must_be_text():
    meta = ScenarioMeta(scenario_id="fixture", project_id="synthetic-project")
    for instructions in ("  ", 7):
        with pytest.raises(ResolverConfigError, match="instructions"):
            Mem0Backend(meta, CONFIG, Client(), instructions=instructions)
    with pytest.raises(ValueError, match="Mem0"):
        comparison.ControlledMem0(pilot("pilot-01").meta(), CONFIG, Client(), 12000, name="mem0-other")


def test_mem0_classic_registration_is_unchanged():
    assert mem0_baseline.MEM0_VERSION == "1.0.11"
    assert comparison.ControlledMem0.name == "mem0-classic"
