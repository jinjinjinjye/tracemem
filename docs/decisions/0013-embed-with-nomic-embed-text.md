---
id: 13
title: Embed records with nomic-embed-text on the local model server
status: proposed
date: 2026-10-25
decided_by: []
supersedes: []
superseded_by: []
---

# 0013. Embed records with nomic-embed-text on the local model server

## Context

The two similarity systems of [decision 0011](0011-compare-five-memory-systems.md)
(the five-system comparison) rank records by their similarity to the question, so
they need an embedding model. The
[working agreement](../working-agreement.md#1-decisions-live-in-decision-records)
lists the embedding model as a team decision. Every compared system must share it,
because another model would rank the same records differently.
[Decision 0004](0004-compare-controlled-memory.md) (the controlled comparison)
named no embedding model and does not measure production retrieval. Teammates
already install an Ollama server for local runs
([decision 0012](0012-cache-and-cap-model-calls.md)), and an embedding library run
inside Python, such as sentence-transformers, would add PyTorch to the project's
dependencies.

## Decision

- **The model.** Records are embedded with `nomic-embed-text`, the default of
  `TRACEMEM_EMBED_MODEL`, through the OpenAI-compatible `/v1/embeddings` endpoint
  of the local server (`TRACEMEM_LOCAL_BASE_URL`), whichever provider answers the
  questions. Paid runs therefore embed locally too.
- **Task prefixes.** The question is sent as `search_query: ` followed by its text,
  and each record as `search_document: ` followed by its context line, exactly as
  the answer model reads it, quote included. Another model named in
  `TRACEMEM_EMBED_MODEL` embeds the bare text.
- **A disk cache.** Every embedding is saved under `cache/emb/`, keyed by model and
  prefixed text, so a text already embedded is never sent again. Only missing
  texts are sent, in batches of 64. A failed request saves nothing. A connection
  failure, timeout or status 408, 409, 429 or 5xx is retried, up to three attempts
  in all, and then stops the run; any other status stops it at once.
  `TRACEMEM_CACHE` does not apply to embeddings, and they are not counted in usage.
- **Only ranking by similarity embeds.** A system with `alpha=1` makes no
  embedding call. Every system still records the embedding model and its prefixes
  under `comparison.retriever`; one that ranks by recency alone records the model
  `TRACEMEM_EMBED_MODEL` names, the one a similarity system run beside it uses. So
  `tracemem report` refuses to compare runs embedded with different models.

## Consequences

The embedder adds no Python dependency: it uses the `openai` SDK of the `llm`
extra. The model is a pull of about 0.3 GB beside the chat model. Offline tests
replace the embedder with a deterministic one (`tests/conftest.py`), so no test
reaches a server. Every run of a similarity system needs a running Ollama server
with the model pulled, including runs that answer through OpenRouter.

The model is identified by its name only. Unlike the chat model of decision 0012,
its digest is neither in the cache key nor in the manifest, so after
`nomic-embed-text` is pulled again with new weights, saved embeddings are reused
and new runs can be reported beside old ones. Clear `cache/emb/` after pulling it
again.

On every development scenario in the repository, the default byte budget holds all
of a similarity system's records (decision 0011), so the embedding model does not
yet change any selection. Its quality starts to matter once retrieval drops
records. The team should revisit this record if retrieval becomes selective and
the model ranks poorly on development scenarios, or if embeddings move to a hosted
service. Setup is in [the local model guide](../local-model.md). The retrieval and
evaluation owners should review this record before ratification.

Open question for the team. The similarity systems run on this choice until the
team decides:

1. **The embedding model.** Whether to keep `nomic-embed-text` served by Ollama,
   which needs no extra Python packages, or to embed with an in-process library or
   another model. A change alters `comparison.retriever`, so every system must be
   rerun before runs can be reported together.
