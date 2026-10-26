"""A fixed number of records per answer (decision record 0011, question 4).

With TRACEMEM_CONTEXT_TOP_K set, every compared system shows the answering model
at most k records: the k closest to the question, with recency added for
similarity + recency only. Unset, every system selects exactly as before.
"""
from __future__ import annotations

import json
from datetime import timedelta

import pytest

from support import pilot
from test_retrieval import (ABSTAIN, CONFIG, FIXTURE_SETS, LINE, START, KeywordEmbedder, ScriptedClient,
                            TableEmbedder, ask, ids, record)
from tracemem.resolver import ResolverConfigError
from tracemem.retrieval import SharedRetriever
from tracemem.systems import comparison

FIVE = ("similarity", "similarity-recency", "mem0-classic", "mem0-instructions", "tracemem-controlled")


def scored_records():
    # Scores against the query (axis 1): c 0.9, a 0.6, d 0.3, b 0.1; created a, b, c, d.
    table = {"= A ": [0.6, 0.8], "= B ": [0.1, 0.995], "= C ": [0.9, 0.436], "= D ": [0.3, 0.954]}
    records = [record(f"S1-T{n}", "model.x", value, at=START + timedelta(minutes=n))
               for n, value in enumerate(["A", "B", "C", "D"], start=1)]
    return records, TableEmbedder(table)


def test_top_k_keeps_the_k_closest_records_in_time_order():
    records, embedder = scored_records()
    retriever = SharedRetriever(0.0, 7.0, embedder)
    chosen = retriever.select("q", records, None, 12000, LINE, top_k=2)
    # The two closest are C (0.9) and A (0.6); they are shown in time order.
    assert ids(chosen) == ["model.x@S1-T1", "model.x@S1-T3"]


@pytest.mark.parametrize("k", [1, 2, 3, 4, 10])
def test_top_k_never_returns_more_than_k_records(k):
    records, embedder = scored_records()
    chosen = SharedRetriever(0.0, 7.0, embedder).select("q", records, None, 12000, LINE, top_k=k)
    assert len(chosen) == min(k, len(records))


@pytest.mark.parametrize("records", FIXTURE_SETS)
@pytest.mark.parametrize("alpha", [0.0, 0.3, 1.0])
def test_no_top_k_selects_exactly_as_before(records, alpha):
    latest = max(r.created_at for r in records) if records else None
    retriever = SharedRetriever(alpha, 7.0, KeywordEmbedder())
    before = retriever.select("Which model are we using?", records, latest, 600, LINE)
    assert ids(retriever.select("Which model are we using?", records, latest, 600, LINE, top_k=None)) == ids(before)


def test_top_k_still_respects_the_byte_budget():
    records, embedder = scored_records()
    one_line = len(LINE(records[0]).encode("utf-8"))
    # Room for one line only: k=3 still yields the single closest record that fits.
    chosen = SharedRetriever(0.0, 7.0, embedder).select("q", records, None, one_line, LINE, top_k=3)
    assert ids(chosen) == ["model.x@S1-T3"]


@pytest.mark.parametrize("bad", [0, -1, True, 2.0, "3"])
def test_top_k_must_be_a_positive_integer(bad):
    records, embedder = scored_records()
    with pytest.raises(ValueError):
        SharedRetriever(0.0, 7.0, embedder).select("q", records, None, 12000, LINE, top_k=bad)


def test_the_shared_answerer_shows_the_model_only_k_lines():
    records, embedder = scored_records()
    client = ScriptedClient(ABSTAIN)
    answerer = comparison.SharedAnswerer(CONFIG, client, retriever=SharedRetriever(0.0, 7.0, embedder), top_k=1)
    answerer.answer(ask(), records, {})
    context = json.loads(client.calls[0][1]["content"])["context"]
    assert context.splitlines() == [LINE(records[2])]


def build(name, monkeypatch, k):
    if k is None:
        monkeypatch.delenv("TRACEMEM_CONTEXT_TOP_K", raising=False)
    else:
        monkeypatch.setenv("TRACEMEM_CONTEXT_TOP_K", str(k))
    return comparison.make_system(name, pilot("pilot-01").meta(), config=CONFIG, client=ScriptedClient(ABSTAIN),
                                  embedder=KeywordEmbedder())


@pytest.mark.parametrize("name", FIVE)
def test_unset_every_system_selects_as_before(name, monkeypatch):
    system = build(name, monkeypatch, None)
    expected_alpha = {"similarity": 0.0, "similarity-recency": 0.3}.get(name, 1.0)
    assert system.answerer.top_k is None
    assert system.answerer.retriever.alpha == expected_alpha
    assert system.comparison["context_top_k"] is None


@pytest.mark.parametrize("name", FIVE)
def test_set_every_system_takes_the_k_closest(name, monkeypatch):
    system = build(name, monkeypatch, 4)
    # Recency stays the one difference of similarity + recency; the others rank by closeness alone.
    assert system.answerer.retriever.alpha == (0.3 if name == "similarity-recency" else 0.0)
    assert system.answerer.top_k == 4
    assert system.comparison["context_top_k"] == 4
    assert system.describe()["shared_retriever"]["ranking"] in ("similarity", "similarity_and_recency")


def test_every_system_records_the_same_k(monkeypatch):
    settings = [build(name, monkeypatch, 5).comparison for name in FIVE]
    assert {s["context_top_k"] for s in settings} == {5}
    assert len({json.dumps(s["retriever"], sort_keys=True) for s in settings}) == 1


@pytest.mark.parametrize("bad", ["0", "-2", "two", "1.5", "1001"])
def test_a_bad_setting_is_refused(bad, monkeypatch):
    monkeypatch.setenv("TRACEMEM_CONTEXT_TOP_K", bad)
    with pytest.raises(ResolverConfigError):
        comparison.make_system("similarity", pilot("pilot-01").meta(), config=CONFIG,
                               client=ScriptedClient(ABSTAIN), embedder=KeywordEmbedder())


def test_an_empty_setting_means_unset(monkeypatch):
    monkeypatch.setenv("TRACEMEM_CONTEXT_TOP_K", "")
    system = comparison.make_system("tracemem-controlled", pilot("pilot-01").meta(), config=CONFIG,
                                    client=ScriptedClient(ABSTAIN), embedder=KeywordEmbedder())
    assert system.answerer.top_k is None and system.answerer.retriever.alpha == 1.0
