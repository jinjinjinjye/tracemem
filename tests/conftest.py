"""Safeguards that apply to every test.

No test reaches an embedding server. The similarity systems get their embedder from
comparison.make_embedder, which every test sees replaced by OfflineEmbedder: letter
and digit counts as embeddings, describing itself as the model TRACEMEM_EMBED_MODEL
selects, so that its runs can be reported beside the other systems' runs. A test that
checks the real factory, or supplies its own embedder, does so explicitly.

Without the optional mem0 extra, tests parametrized with mem0-instructions are
skipped, as the tests of mem0-classic skip themselves.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

import pytest

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


def pytest_collection_modifyitems(config, items):
    try:
        version("mem0ai")
        return
    except PackageNotFoundError:
        pass
    skip = pytest.mark.skip(reason="install the optional mem0 extra to run the native SDK")
    for item in items:
        callspec = getattr(item, "callspec", None)
        if callspec is not None and any(value == "mem0-instructions" for value in callspec.params.values()
                                        if isinstance(value, str)):
            item.add_marker(skip)
