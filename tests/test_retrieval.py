"""Offline checks of the shared retriever, its embedding cache and the shared answer prompt.

A keyword embedder makes similarity known by construction. The cache tests replace
the SDK with a fake module, as test_model_client.py does, so no model server is
needed. The alpha-1 tests compare the retriever with the comparison's original
newest-first reader on every record set saved in the fixtures and on the pilots'
gold stores.
"""

from __future__ import annotations

import json
import math
import random
import sys
from datetime import datetime, timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from support import FIXTURES, PILOT_IDS, pilot, pilot_timeline
from tracemem.model_client import LOCAL_BASE_URL
from tracemem.ops import flat_records
from tracemem.resolver import FatalModelError, ModelReply, ResolverConfig
from tracemem.retrieval import OllamaEmbeddings, SharedRetriever, cosine, recency
from tracemem.schema import Record, SystemQuestion
from tracemem.systems import comparison

START = datetime(2026, 3, 2, 10, 0)
LINE = comparison._line


def record(turn, item, value, *, at=None, status="active", record_id=None, speaker="Ana"):
    return Record(record_id=record_id or f"{item}@{turn}", project_id="retrieval", item=item, value=value,
                  status=status, source_turn_ids=[turn], speakers=[speaker], created_turn=turn,
                  created_at=at if at is not None else START)


def ids(records):
    return [r.record_id for r in records]


class NoEmbedder:
    def embed_query(self, text):
        raise AssertionError("alpha 1 must not embed")

    def embed_documents(self, texts):
        raise AssertionError("alpha 1 must not embed")


class KeywordEmbedder:
    """One axis per keyword, counted in the lower-cased text."""

    def __init__(self, axes=("dataset", "model", "metric")):
        self.axes = axes
        self.queries, self.documents = [], []

    def vector(self, text):
        return [float(text.lower().count(word)) for word in self.axes]

    def embed_query(self, text):
        self.queries.append(text)
        return self.vector(text)

    def embed_documents(self, texts):
        self.documents.append(list(texts))
        return [self.vector(text) for text in texts]


class TableEmbedder:
    """A fixed vector per marker found in the text; the query is always the first axis."""

    def __init__(self, table):
        self.table = table

    def embed_query(self, text):
        return [1.0, 0.0]

    def embed_documents(self, texts):
        return [next(vector for marker, vector in self.table.items() if marker in text) for text in texts]


# Record sets saved in PR #4's fixtures, and the pilots' gold stores after each session.

def _fixture_record_sets():
    found = []

    def walk(node, name):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "records" and isinstance(value, list):
                    found.append(pytest.param([Record.model_validate(row) for row in value],
                                              id=f"{name}-{len(found)}"))
                walk(value, name)
        elif isinstance(node, list):
            for value in node:
                walk(value, name)

    for path in sorted(FIXTURES.glob("*.json")):
        walk(json.loads(path.read_text(encoding="utf-8")), path.stem)
    return found


def _pilot_record_sets():
    found = []
    for sid in PILOT_IDS:
        timeline = pilot_timeline(sid)
        seen = []
        for session in pilot(sid).sessions:
            seen += [candidate for turn in session.turns for candidate in timeline.candidates_by_turn.get(turn.id, [])]
            found.append(pytest.param(timeline.log_after_session[session.id].records(), id=f"{sid}-{session.id}-oplog"))
            found.append(pytest.param(flat_records(timeline.scenario.project_id, list(seen), timeline.turn_times),
                                      id=f"{sid}-{session.id}-flat"))
    return found


FIXTURE_SETS = _fixture_record_sets()


def test_the_fixtures_hold_record_sets():
    assert len(FIXTURE_SETS) >= 10


@pytest.mark.parametrize("budget", [256, 600, 2000, 12000])
@pytest.mark.parametrize("records", FIXTURE_SETS + _pilot_record_sets())
def test_alpha_one_selects_exactly_as_the_newest_first_reader(records, budget):
    expected = comparison._selected_context(records, budget)[2]
    for shuffled in (records, list(reversed(records))):
        selected = SharedRetriever(1, 7, embedder=NoEmbedder()).select(
            "Which dataset are we training on?", shuffled, None, budget, LINE)
        assert selected == comparison._selected_context(shuffled, budget)[2]
        assert ids(selected) == ids(expected)


def test_alpha_one_breaks_ties_newest_first_by_turn_item_value_and_id():
    # Equal times, as when two records come from one turn, then equal turns and items.
    tied = [record("S1-T2", "model.ner", "spaCy"), record("S1-T2", "model.ner", "Flair"),
            record("S1-T1", "model.ner", "spaCy"), record("S1-T2", "metric.primary", "F1"),
            record("S1-T2", "model.ner", "spaCy", record_id="model.ner@S1-T2#2")]
    budget = sum(len(LINE(r).encode()) for r in tied[:3]) + 2
    for seed in range(20):
        shuffled = random.Random(seed).sample(tied, len(tied))
        for size in (budget, 12000):
            expected = comparison._selected_context(shuffled, size)[2]
            assert SharedRetriever(1, 7).select("q", shuffled, None, size, LINE) == expected


def test_alpha_zero_ranks_by_similarity_not_age():
    records = [record("S1-T1", "dataset.train", "IMDB", at=START),
               record("S2-T1", "model.sentiment", "BERT", at=START + timedelta(days=7)),
               record("S3-T1", "metric.primary", "accuracy", at=START + timedelta(days=14))]
    embedder = KeywordEmbedder()
    one = len(LINE(records[0]).encode())
    selected = SharedRetriever(0, 7, embedder=embedder).select(
        "Which dataset are we training on?", records, None, one, LINE)
    assert ids(selected) == ["dataset.train@S1-T1"]  # The oldest record, but the only similar one.
    assert embedder.queries == ["Which dataset are we training on?"]
    assert embedder.documents == [[LINE(r) for r in records]]  # The record text is its context line.


def test_equal_scores_go_to_the_newest_record():
    records = [record(f"S1-T{n}", "model.sentiment", "BERT", at=START + timedelta(minutes=n)) for n in (1, 2, 3)]
    budget = len(LINE(records[0]).encode()) * 2 + 1
    selected = SharedRetriever(0, 7, embedder=KeywordEmbedder()).select("Which model?", records, None, budget, LINE)
    assert ids(selected) == ["model.sentiment@S1-T2", "model.sentiment@S1-T3"]


def test_recency_halves_at_each_half_life():
    latest = START + timedelta(days=30)
    assert recency(latest, latest, 7) == 1.0
    assert recency(latest - timedelta(days=7), latest, 7) == pytest.approx(0.5)
    assert recency(latest - timedelta(days=14), latest, 7) == pytest.approx(0.25)
    assert recency(latest - timedelta(days=3), latest, 3) == pytest.approx(0.5)
    assert recency(latest - timedelta(hours=12), latest, 0.5) == pytest.approx(0.5)


@pytest.mark.parametrize("newer_similarity,winner", [(0.6, "newer"), (0.4, "older")])
def test_score_mixes_similarity_and_recency_by_alpha(newer_similarity, winner):
    # alpha 0.5, half-life 7: the older record (similarity 1, age 7 days) scores 0.75;
    # the newer one (age 0) scores 0.5 * similarity + 0.5.
    latest = START + timedelta(days=7)
    records = [record("S1-T1", "model.sentiment", "older", at=START),
               record("S2-T1", "model.sentiment", "newer", at=latest)]
    other = math.sqrt(1 - newer_similarity ** 2)
    embedder = TableEmbedder({"older": [1.0, 0.0], "newer": [newer_similarity, other]})
    budget = max(len(LINE(r).encode()) for r in records)
    selected = SharedRetriever(0.5, 7, embedder=embedder).select("q", records, latest, budget, LINE)
    assert [r.value for r in selected] == [winner]


def test_recency_is_measured_to_the_latest_observed_turn():
    # Moving the latest turn on by one half-life halves both recencies, so a
    # similarity gap that lost by recency now wins.
    records = [record("S1-T1", "model.sentiment", "older", at=START),
               record("S2-T1", "model.sentiment", "newer", at=START + timedelta(days=7))]
    embedder = TableEmbedder({"older": [1.0, 0.0], "newer": [0.6, 0.8]})
    budget = max(len(LINE(r).encode()) for r in records)
    retriever = SharedRetriever(0.5, 7, embedder=embedder)
    assert [r.value for r in retriever.select("q", records, START + timedelta(days=7), budget, LINE)] == ["newer"]
    assert [r.value for r in retriever.select("q", records, START + timedelta(days=21), budget, LINE)] == ["older"]


@pytest.mark.parametrize("alpha", [0, 0.3, 1])
def test_the_byte_budget_counts_whole_lines_and_newlines(alpha):
    records = [record(f"S1-T{n}", "model.sentiment", f"value-{n}", at=START + timedelta(minutes=n))
               for n in range(1, 4)]
    sizes = [len(LINE(r).encode()) for r in records]
    retriever = SharedRetriever(alpha, 7, embedder=KeywordEmbedder())
    latest = records[-1].created_at
    exact = retriever.select("Which model?", records, latest, sizes[2] + 1 + sizes[1], LINE)
    assert ids(exact) == ids(records[1:])  # Two lines and the newline between them fit exactly.
    short = retriever.select("Which model?", records, latest, sizes[2] + sizes[1], LINE)
    assert ids(short) == ids(records[2:])
    assert retriever.select("Which model?", records, latest, sizes[2] - 1, LINE) == []


@pytest.mark.parametrize("alpha", [0, 0.3, 1])
def test_a_line_too_long_is_skipped_whole_and_smaller_ones_still_fit(alpha):
    records = [record("S1-T1", "model.sentiment", "BERT", at=START),
               record("S1-T2", "model.sentiment", "x" * 500, at=START + timedelta(minutes=1)),
               record("S1-T3", "model.sentiment", "DistilBERT", at=START + timedelta(minutes=2))]
    budget = len(LINE(records[0]).encode()) + 1 + len(LINE(records[2]).encode())
    selected = SharedRetriever(alpha, 7, embedder=KeywordEmbedder()).select(
        "Which model?", records, records[-1].created_at, budget, LINE)
    assert ids(selected) == ["model.sentiment@S1-T1", "model.sentiment@S1-T3"]


@pytest.mark.parametrize("seed", range(10))
@pytest.mark.parametrize("alpha", [0, 0.3, 1])
def test_selection_fits_the_budget_and_comes_back_in_time_order(seed, alpha):
    rng = random.Random(seed)
    items = ["dataset.train", "model.sentiment", "metric.primary"]
    records = [record(f"S{n // 5 + 1}-T{n % 5 + 1}", rng.choice(items), "v" * rng.randint(1, 80),
                      at=START + timedelta(hours=rng.randint(0, 400))) for n in range(25)]
    budget = rng.randint(200, 1500)
    selected = SharedRetriever(alpha, 3, embedder=KeywordEmbedder()).select(
        "Which metric is primary?", records, max(r.created_at for r in records), budget, LINE)
    assert selected
    assert len("\n".join(LINE(r) for r in selected).encode("utf-8")) <= budget
    keys = [(r.created_at, r.created_turn, r.item, r.value, r.record_id) for r in selected]
    assert keys == sorted(keys)


def test_alpha_zero_returns_the_similar_records_in_time_order():
    records = [record("S1-T1", "metric.primary", "accuracy", at=START),
               record("S2-T1", "dataset.train", "IMDB", at=START + timedelta(days=1)),
               record("S3-T1", "metric.primary", "macro-F1", at=START + timedelta(days=2))]
    budget = len(LINE(records[0]).encode()) + 1 + len(LINE(records[2]).encode())
    selected = SharedRetriever(0, 7, embedder=KeywordEmbedder()).select(
        "Which metric is primary?", list(reversed(records)), None, budget, LINE)
    assert ids(selected) == ["metric.primary@S1-T1", "metric.primary@S3-T1"]


def test_cosine_handles_zero_vectors_and_rejects_mismatched_lengths():
    assert cosine([1.0, 0.0], [2.0, 0.0]) == pytest.approx(1.0)
    assert cosine([1.0, 0.0], [0.0, 3.0]) == pytest.approx(0.0)
    assert cosine([0.0, 0.0], [1.0, 1.0]) == 0.0
    with pytest.raises(ValueError):
        cosine([1.0], [1.0, 0.0])


@pytest.mark.parametrize("alpha,half_life", [(-0.1, 7), (1.5, 7), (math.nan, 7), (True, 7), ("1", 7),
                                             (0.5, 0), (0.5, -1), (0.5, math.inf)])
def test_invalid_settings_are_rejected(alpha, half_life):
    with pytest.raises(ValueError):
        SharedRetriever(alpha, half_life, embedder=KeywordEmbedder())


def test_a_recency_mix_needs_the_latest_turn_but_pure_similarity_does_not():
    records = [record("S1-T1", "model.sentiment", "BERT")]
    with pytest.raises(ValueError, match="latest observed turn"):
        SharedRetriever(0.3, 7, embedder=KeywordEmbedder()).select("q", records, None, 12000, LINE)
    assert SharedRetriever(0, 7, embedder=KeywordEmbedder()).select("q", records, None, 12000, LINE) == records


def test_no_records_need_no_embedding():
    assert SharedRetriever(0, 7, embedder=NoEmbedder()).select("q", [], None, 12000, LINE) == []


def test_describe_records_the_settings_and_the_embedder_only_when_used():
    assert SharedRetriever(1, 7, embedder=KeywordEmbedder()).describe() == {
        "policy": "similarity_recency_newest_tiebreak_whole_lines_v1", "ranking": "newest_first",
        "alpha": 1.0, "half_life_days": 7.0, "recency_age": "record_created_at_to_latest_observed_turn",
        "document_text": "context_line", "embedder": None,
    }
    assert SharedRetriever(0, 7, embedder=KeywordEmbedder()).describe()["ranking"] == "similarity"
    mixed = SharedRetriever(0.3, 7, embedder=KeywordEmbedder()).describe()
    assert (mixed["ranking"], mixed["alpha"], mixed["embedder"]) == ("similarity_and_recency", 0.3, "KeywordEmbedder")


# The embedding client and its cache

@pytest.fixture
def sdk(monkeypatch, tmp_path):
    """Replace the SDK: each text embeds as [its length, 1], returned out of order."""
    module = ModuleType("openai")

    class APIConnectionError(Exception):
        pass

    class APIStatusError(Exception):
        def __init__(self, status_code, message):
            self.status_code = status_code
            super().__init__(message)

    def create(*, model, input, encoding_format, timeout):
        rows = [SimpleNamespace(index=index, embedding=[float(len(text)), 1.0]) for index, text in enumerate(input)]
        return SimpleNamespace(data=list(reversed(rows)))

    module.APIConnectionError = APIConnectionError
    module.APIStatusError = APIStatusError
    module.create = Mock(side_effect=create)
    module.OpenAI = Mock(return_value=SimpleNamespace(embeddings=SimpleNamespace(create=module.create)))
    monkeypatch.setitem(sys.modules, "openai", module)
    for name in ("TRACEMEM_LOCAL_BASE_URL", "TRACEMEM_EMBED_MODEL", "TRACEMEM_LOCAL_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    return module


def sent(module):
    return [call.kwargs["input"] for call in module.create.call_args_list]


def test_defaults_reach_the_local_server_with_the_model_prefixes(sdk, tmp_path):
    embedder = OllamaEmbeddings.from_env()
    assert sdk.OpenAI.call_args.kwargs == {"api_key": "local", "base_url": LOCAL_BASE_URL, "max_retries": 0}
    assert embedder.embed_documents(["abc", "de"]) == [[20.0, 1.0], [19.0, 1.0]]  # Returned in input order.
    assert embedder.embed_query("q") == [15.0, 1.0]
    assert sent(sdk) == [["search_document: abc", "search_document: de"], ["search_query: q"]]
    call = sdk.create.call_args.kwargs
    assert (call["model"], call["encoding_format"], call["timeout"]) == ("nomic-embed-text", "float", 120.0)
    assert len(list((tmp_path / "cache" / "emb").rglob("*.json"))) == 3
    assert embedder.describe() == {"api": "openai_compatible_embeddings", "base_url": LOCAL_BASE_URL,
                                   "model": "nomic-embed-text", "query_prefix": "search_query: ",
                                   "document_prefix": "search_document: "}


def test_settings_come_from_the_environment(sdk):
    embedder = OllamaEmbeddings.from_env({"TRACEMEM_LOCAL_BASE_URL": "http://gpu-box:11434/v1",
                                          "TRACEMEM_EMBED_MODEL": "other-embedder", "TRACEMEM_LOCAL_API_KEY": "k"})
    assert sdk.OpenAI.call_args.kwargs["base_url"] == "http://gpu-box:11434/v1"
    assert sdk.OpenAI.call_args.kwargs["api_key"] == "k"
    embedder.embed_documents(["abc"])
    assert sent(sdk) == [["abc"]]  # Only models known to need prefixes get them.
    assert sdk.create.call_args.kwargs["model"] == "other-embedder"
    tagged = OllamaEmbeddings.from_env({"TRACEMEM_EMBED_MODEL": "nomic-embed-text:v1.5"})
    assert (tagged.query_prefix, tagged.document_prefix) == ("search_query: ", "search_document: ")


def test_the_cache_avoids_a_second_call(sdk, tmp_path):
    first = OllamaEmbeddings.from_env()
    vectors = first.embed_documents(["abc", "de"])
    assert first.embed_documents(["abc", "de"]) == vectors
    assert OllamaEmbeddings.from_env().embed_documents(["de", "abc"]) == list(reversed(vectors))
    assert sdk.create.call_count == 1


def test_only_missing_texts_are_sent_once_each(sdk):
    embedder = OllamaEmbeddings.from_env()
    embedder.embed_documents(["abc"])
    assert embedder.embed_documents(["abc", "de", "de", "fgh"]) == [[20.0, 1.0], [19.0, 1.0], [19.0, 1.0],
                                                                  [20.0, 1.0]]
    assert sent(sdk) == [["search_document: abc"], ["search_document: de", "search_document: fgh"]]


def test_the_key_covers_the_model_and_the_text_with_its_prefix(sdk):
    embedder = OllamaEmbeddings.from_env()
    embedder.embed_documents(["abc"])
    embedder.embed_query("abc")  # Same text, query prefix: a different entry.
    OllamaEmbeddings.from_env({"TRACEMEM_EMBED_MODEL": "other-embedder"}).embed_documents(["search_document: abc"])
    assert sdk.create.call_count == 3
    assert embedder.key("abc") != OllamaEmbeddings.from_env({"TRACEMEM_EMBED_MODEL": "other"}).key("abc")
    # The address does not change an embedding, so it is not part of the key.
    elsewhere = OllamaEmbeddings.from_env({"TRACEMEM_LOCAL_BASE_URL": "http://gpu-box:11434/v1"})
    assert elsewhere.embed_documents(["abc"]) == [[20.0, 1.0]]
    assert sdk.create.call_count == 3


def test_large_requests_are_sent_in_batches(sdk):
    embedder = OllamaEmbeddings(batch_size=2)
    assert len(embedder.embed_documents(["a", "b", "c", "d", "e"])) == 5
    assert [len(batch) for batch in sent(sdk)] == [2, 2, 1]


def test_transient_failures_are_retried_and_nothing_failed_is_saved(sdk, tmp_path):
    succeed = sdk.create.side_effect
    failures = [sdk.APIConnectionError("down"), sdk.APIStatusError(503, "busy")]

    def flaky(**kwargs):
        if failures:
            raise failures.pop(0)
        return succeed(**kwargs)

    sdk.create.side_effect = flaky
    assert OllamaEmbeddings.from_env().embed_documents(["abc"]) == [[20.0, 1.0]]
    assert sdk.create.call_count == 3
    assert len(list((tmp_path / "cache" / "emb").rglob("*.json"))) == 1


def test_exhausted_or_rejected_requests_stop_the_run_and_save_nothing(sdk, tmp_path):
    sdk.create.side_effect = sdk.APIConnectionError("down")
    with pytest.raises(FatalModelError, match="after 3 attempts"):
        OllamaEmbeddings.from_env().embed_documents(["abc"])
    assert sdk.create.call_count == 3
    sdk.create.side_effect = sdk.APIStatusError(404, "model not found")
    with pytest.raises(FatalModelError, match="status 404"):
        OllamaEmbeddings.from_env().embed_documents(["abc"])
    assert sdk.create.call_count == 4  # A rejected request is not retried.
    sdk.create.side_effect = lambda **kwargs: SimpleNamespace(data=[])
    with pytest.raises(FatalModelError, match="wrong number"):
        OllamaEmbeddings.from_env().embed_documents(["abc"])
    assert not (tmp_path / "cache" / "emb").exists()


def test_a_malformed_cache_file_is_a_miss_and_is_replaced(sdk):
    embedder = OllamaEmbeddings.from_env()
    path = embedder._path("search_document: abc")
    path.parent.mkdir(parents=True)
    path.write_text('{"embedding": "broken"}', encoding="utf-8")
    assert embedder.embed_documents(["abc"]) == [[20.0, 1.0]]
    assert json.loads(path.read_text(encoding="utf-8")) == {"model": "nomic-embed-text", "embedding": [20.0, 1.0]}


def test_a_similarity_retriever_embeds_through_the_local_server_by_default(sdk):
    retriever = SharedRetriever(0, 7)
    assert retriever.describe()["embedder"]["model"] == "nomic-embed-text"
    records = [record("S1-T1", "model.sentiment", "BERT"), record("S1-T2", "dataset.train", "IMDB")]
    first = retriever.select("Which model?", records, None, 12000, LINE)
    assert retriever.select("Which model?", records, None, 12000, LINE) == first == records
    assert sdk.create.call_count == 2  # The query once and the lines once; the repeat is all saved.
    assert SharedRetriever(1, 7).embedder is None


# The shared answerer

class ScriptedClient:
    def __init__(self, decision):
        self.decision = decision
        self.calls = []

    def complete(self, *, config, messages, response_format):
        self.calls.append(messages)
        return ModelReply(json.dumps(self.decision), input_tokens=3, output_tokens=1)


ABSTAIN = {"status": "abstain", "value": None, "cited_turn_ids": [], "text": ""}
CONFIG = ResolverConfig(model="offline-retrieval")


def ask(text="Which dataset are we training on?"):
    return SystemQuestion(question_id="opaque", scenario_id="synthetic", kind="current", text=text)


@pytest.mark.parametrize("records", FIXTURE_SETS)
def test_the_shared_answerer_defaults_to_the_newest_first_selection(records):
    client = ScriptedClient(ABSTAIN)
    answerer = comparison.SharedAnswerer(CONFIG, client, budget_bytes=600)
    answer = answerer.answer(ask(), records, {})
    payload = json.loads(client.calls[0][1]["content"])
    assert answerer.retriever.alpha == 1.0
    assert (payload["context"], payload["allowed_source_turn_ids"]) == comparison.answer_context(records, 600)
    assert answer.context_turn_ids == payload["allowed_source_turn_ids"]


def test_the_shared_answerer_reads_what_its_retriever_selects():
    # Each line is over 128 bytes, so the smallest budget holds only one.
    speaker = "Speaker" * 18
    records = [record("S1-T1", "dataset.train", "IMDB", at=START, speaker=speaker),
               record("S2-T1", "model.sentiment", "BERT", at=START + timedelta(days=1), speaker=speaker),
               record("S3-T1", "metric.primary", "accuracy", at=START + timedelta(days=2), speaker=speaker)]
    assert all(128 < len(LINE(r).encode()) <= 256 for r in records)
    client = ScriptedClient({"status": "answer", "value": "IMDB", "cited_turn_ids": ["S1-T1"], "text": ""})
    retriever = SharedRetriever(0.3, 7, embedder=KeywordEmbedder())
    answerer = comparison.SharedAnswerer(CONFIG, client, budget_bytes=256, retriever=retriever)
    answer = answerer.answer(ask(), records, {}, latest=records[-1].created_at)
    payload = json.loads(client.calls[0][1]["content"])
    assert payload["context"] == LINE(records[0])
    assert payload["allowed_source_turn_ids"] == answer.context_turn_ids == ["S1-T1"]
    assert (answer.status, answer.value) == ("answer", "IMDB")


def test_every_controlled_arm_records_its_retriever_outside_the_shared_settings():
    for name in comparison.NAMES:
        system = comparison.make_system(name, pilot("pilot-01").meta(), config=CONFIG, client=ScriptedClient(ABSTAIN))
        try:
            description = system.describe()
        finally:
            getattr(system, "close", lambda: None)()
        assert description["shared_retriever"] == SharedRetriever(1, 7).describe()
        # Later arms differ in their retriever, and the report requires equal shared settings.
        assert "shared_retriever" not in description["comparison"]


# The shared answer prompt

def test_the_answer_prompt_states_the_benchmark_conventions_once_before_the_state_guide():
    prompt = comparison.ANSWER_PROMPT
    assert prompt.count(comparison.ANSWER_CONVENTIONS) == 1
    assert prompt.index(comparison.ANSWER_CONVENTIONS) < prompt.index(comparison.ANSWER_STATE_GUIDE)
    assert prompt.endswith("\n" + comparison.ANSWER_EVIDENCE_CHECK)
    conventions = " ".join(comparison.ANSWER_CONVENTIONS.split())
    for phrase in ("suggestion, even when it is phrased as a question", "is a mention",
                   "A dispute is settled only when", "even one made sessions before",
                   "progress changes when someone announces the change"):
        assert phrase in conventions


def test_the_conventions_change_only_the_answer_prompt_fingerprint(monkeypatch):
    current = comparison.comparison_settings(CONFIG, 12000, ScriptedClient(ABSTAIN))
    monkeypatch.setattr(comparison, "ANSWER_PROMPT",
                        comparison.ANSWER_PROMPT.replace(comparison.ANSWER_CONVENTIONS + "\n", ""))
    without = comparison.comparison_settings(CONFIG, 12000, ScriptedClient(ABSTAIN))
    assert {key for key in current if current[key] != without[key]} == {"answer_prompt_hash"}
