"""Safeguards that apply to every test.

No test reaches an embedding server. The similarity systems get their embedder from
comparison.make_embedder, which every test sees replaced by OfflineEmbedder: letter
and digit counts as embeddings, describing itself as the model TRACEMEM_EMBED_MODEL
selects, so that its runs can be reported beside the other systems' runs. A test that
checks the real factory, or supplies its own embedder, does so explicitly. Nor does
any test read a local model server's list of loaded or installed models: a test of
the local client replaces model_client.server_context_length and
model_client.model_digest itself.

Without the optional mem0 extra, a test that runs mem0-classic and skips it itself,
such as one parametrized with every registered system, skips mem0-instructions too.
Tests that never run mem0-classic, such as those of test_five_systems.py, mark their
own Mem0 cases, so a mem0-instructions case that builds nothing still runs.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

import pytest

from tracemem import model_client
from tracemem.retrieval import embed_model, embedding_settings
from tracemem.systems import comparison

SYMBOLS = "abcdefghijklmnopqrstuvwxyz0123456789"


class OfflineEmbedder:
    """Deterministic embeddings that record every text they are asked for."""

    def __init__(self):
        self.queries: list[str] = []
        self.documents: list[list[str]] = []

    @staticmethod
    def vector(text: str) -> list[float]:
        lower = text.lower()
        return [float(lower.count(symbol)) for symbol in SYMBOLS]

    def describe(self) -> dict:
        return {**embedding_settings(embed_model()), "base_url": "offline"}

    def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return self.vector(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.documents.append(list(texts))
        return [self.vector(text) for text in texts]


@pytest.fixture(autouse=True)
def offline_embedders(monkeypatch):
    """Every embedder the similarity systems made during the test, in order."""
    made: list[OfflineEmbedder] = []

    def make() -> OfflineEmbedder:
        made.append(OfflineEmbedder())
        return made[-1]

    monkeypatch.setattr(comparison, "make_embedder", make)
    return made


@pytest.fixture(autouse=True)
def no_model_server(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("tests must not read a model server's loaded or installed models")

    monkeypatch.setattr(model_client, "server_context_length", forbidden)
    monkeypatch.setattr(model_client, "model_digest", forbidden)


def _cases(item, value: str) -> set[tuple]:
    # (test, argument) pairs for which this item runs the given system name.
    params = getattr(getattr(item, "callspec", None), "params", {})
    return {(item.parent.nodeid, item.originalname, name) for name, given in params.items()
            if isinstance(given, str) and given == value}


def pytest_collection_modifyitems(config, items):
    try:
        version("mem0ai")
        return
    except PackageNotFoundError:
        pass
    skip = pytest.mark.skip(reason="install the optional mem0 extra to run the native SDK")
    classic = set().union(*(_cases(item, "mem0-classic") for item in items))
    for item in items:
        if _cases(item, "mem0-instructions") & classic:
            item.add_marker(skip)
