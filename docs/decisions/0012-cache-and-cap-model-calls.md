---
id: 12
title: Call local and paid models through one client with a reply cache and a spending cap
status: proposed
date: 2026-10-25
decided_by: []
supersedes: []
superseded_by: []
---

# 0012. Call local and paid models through one client with a reply cache and a spending cap

## Context

[Decision 0004](0004-compare-controlled-memory.md) (the controlled comparison)
gives every compared system one shared model client, which was the resolver's
built-in OpenAI client with a fixed endpoint. Development needs a model that costs
nothing to call many times, and the runs the team plans to report use Haiku 5.5
(`anthropic/claude-haiku-5.5`), reached through OpenRouter on a fixed budget. The
[working agreement](../working-agreement.md#1-decisions-live-in-decision-records)
makes the answer model and the API budget team decisions; this record proposes
both. Two failures would change results without notice: a local server that cuts
a long request and answers anyway, and a model tag pulled again with new weights.
[Decision 0002](0002-record-resolver-failures.md) (record resolver failures)
separates retryable from fatal provider errors, and this client keeps that split.

## Decision

Every controlled comparison system gets its model client from
`model_client.from_env()`, chosen by `TRACEMEM_PROVIDER`. Local runs use an Ollama
server whose model has a 16,384-token context, and paid runs use Haiku 5.5
through OpenRouter; the default, `openai`, keeps the built-in client. Each
complete reply is saved under `cache/llm/`, so a repeated request costs nothing,
and paid calls stop once the cost log reaches US$12.

The details follow.

- **One client for every comparison system.** `comparison.make_client()` returns
  `model_client.from_env()`, so `TRACEMEM_PROVIDER` chooses the client of every
  controlled comparison system: `openai`, the default, keeps the built-in client
  unchanged; `openrouter`; or `local`, an Ollama server. Both new targets speak
  the OpenAI Chat Completions API through one adapter, `OpenAICompatibleClient`,
  with the SDK's own retries disabled.
- **Local runs use Ollama.** The server is at `http://127.0.0.1:11434/v1`
  (`TRACEMEM_LOCAL_BASE_URL`), and development runs use `qwen3.5:4b`. The output
  limit is sent as `max_tokens`, which Ollama reads. Thinking is off
  (`reasoning_effort: "none"`); `TRACEMEM_LOCAL_THINKING=on` allows it.
- **The local model gets a 16,384-token context.** Ollama gives each model a
  fixed context and cuts a longer request from the front without refusing it, so
  the server must be started with `OLLAMA_CONTEXT_LENGTH=16384`, the value of
  `TRACEMEM_LOCAL_CONTEXT_TOKENS`. After every reply the client reads the loaded
  model's context from `/api/ps` and stops the run, saving nothing, unless it
  equals that value, or when the server read fewer than one token for every six
  bytes sent.
- **A local model is identified by its digest.** When it is built, the client
  reads the model's digest from `/api/tags` and records it with its settings, so
  weights pulled again under the same tag get new cache keys and cannot be reported
  beside older runs. A model that is not installed stops the run before any call.
- **A dead local server stops the run.** A refused or dropped connection to the
  local server is fatal, so the remaining questions are not scored as failed
  answers; a timeout is retried within `TRACEMEM_RESOLVER_MAX_ATTEMPTS`.
- **Paid runs use OpenRouter.** Requests go to `https://openrouter.ai/api/v1` with
  the key `OPENROUTER_API_KEY`, read from the environment or else from `.env` in
  the folder the command runs from, and with `provider.require_parameters` set, so
  a request never reaches an endpoint that ignores structured output. The output
  limit is sent as `max_completion_tokens`. Only a model in the price table
  (`PRICES_PER_MILLION`: `anthropic/claude-haiku-5.5` and its `:batch` variant) is
  accepted; any other is refused before the first call. A connection failure,
  timeout or status 408, 409, 429 or 5xx is retried; any other status stops the
  run.
- **A reply cache.** `CachedClient` wraps every provider. It saves each complete
  reply (finish reason `stop`, not refused) under `cache/llm/`
  (`TRACEMEM_CACHE_DIR`), keyed by the client's settings, the model settings except
  the timeout and attempt count, and the full request. A saved reply is returned
  with zero tokens and no call. Errors, refusals and cut-off replies are not saved.
  A request repeated within one scenario, such as a retry that resends the same
  feedback, gets its own numbered slot, so it still reaches the model.
  `TRACEMEM_CACHE=off` neither reads nor saves replies. `usage.json` counts each
  scenario's cache calls, hits and misses under `model_cache`.
- **A cost log and a US$12 cap.** Every completed call, a cache hit at zero cost
  included, is appended to `cache/costs.jsonl` (`TRACEMEM_COST_LOG`), outside every
  reply cache folder. A call's cost is OpenRouter's own figure, else the price
  table's, else zero, logged as `unpriced`. Before every paid call the client reads
  the whole log again; once its total reaches `TRACEMEM_BUDGET_USD` (default 12)
  the run stops with `SpendingCapError` instead of calling the model. A call is
  logged before its reply is saved. Local calls are never capped.
- **Manifests.** Each run records the client's settings that change replies. For
  the two new providers these are the provider, endpoint, extra request fields,
  output-limit field and, for a local server, the context and the model digest;
  for the built-in client, its name. The key, the cache folder and the cost log
  are never recorded.

## Consequences

A repeated run with the same settings makes no model calls, costs nothing and
gives the same answers. The cap holds across fresh cache folders and across runs
going on at the same time on one machine, and stops a paid run within one call of
the budget. A cut request or a stopped local server ends the run instead of
producing answers that look valid, and a re-pulled model gets new cache keys.

Saved replies report zero tokens, so token totals count only calls that reached
the provider; call counts include cache hits, and `model_cache` gives the hits and
misses. Token comparisons between systems need `TRACEMEM_CACHE=off` or a
fresh `TRACEMEM_CACHE_DIR` for each system, and repeated runs meant as independent
samples need a fresh cache folder each, or they replay the first run's replies.

The cap counts only calls logged on one machine: each teammate's log is separate,
so the team must agree who runs paid commands and with which budget. It does not
limit other use of the same key, and it does not count calls through the default
`openai` provider, which are logged as unpriced. A new paid model needs its prices
in the table first. The local checks read Ollama's `/api/ps` and `/api/tags`, so
the local provider needs an Ollama server. `tracemem report` refuses to compare runs
with different model settings, so local development runs are never reported beside
Haiku runs.

The `pipeline-resolver-dev` diagnostic is not covered. It still calls
`LLMResolver.from_env()`, which uses the built-in OpenAI client and which existing
tests replace to inject scripted resolvers; moving it to this client needs a new
seam for those tests. Setup, commands and every setting are in
[the local model guide](../local-model.md). The resolver and evaluation owners,
and whoever holds the OpenRouter key, should review this record before
ratification.

Open question for the team. The client runs on this choice until the team decides:

1. **Thinking for the local model.** It is off, so the model answers directly.
   Turning it on changes the cache keys, can change answers, and needs a larger
   `TRACEMEM_RESOLVER_MAX_COMPLETION_TOKENS`. The OpenRouter client sends no
   reasoning setting, so the paid model runs with the provider's default.
