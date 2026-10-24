# Running the comparison on a local model

The controlled comparison systems (`similarity`, `similarity-recency`, `mem0-classic`,
`mem0-instructions`, `tracemem-controlled` and the `tracemem-no-versions` diagnostic,
see [the comparison guide](memory-comparison.md)) can call a model on
your own machine through [Ollama](https://ollama.com) instead of a paid API. Local runs
cost nothing and are meant for development. The Haiku runs use OpenRouter with a
capped budget; see [Paid runs](#paid-runs-haiku-through-openrouter) below.

## 1. Install Ollama

- **Windows**: download and run the installer from <https://ollama.com/download>.
  Ollama then runs in the background.
- **macOS**: download the app from <https://ollama.com/download>, move it to
  Applications and open it once. It then runs in the background.
- **Linux, with administrator rights**: run the official install script, which also
  starts Ollama as a service:

  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

- **Linux, without administrator rights**: download the Linux release archive for
  your processor (`ollama-linux-amd64` on most machines, `ollama-linux-arm64` on ARM)
  from <https://github.com/ollama/ollama/releases>, unpack it into your home folder and
  start the server yourself. Leave it running in its own terminal.

  ```bash
  mkdir -p ~/ollama
  tar -xf <downloaded archive> -C ~/ollama
  ~/ollama/bin/ollama serve
  ```

  In the commands below, write `~/ollama/bin/ollama` where they say `ollama`.

Ollama uses a supported GPU when it finds one, and the CPU otherwise; a small model
works on either, but is much slower on the CPU. Check that the server is up with
`ollama list`.

## 2. Pull the two models

```bash
ollama pull qwen3.5:4b          # the chat model, about 3.3 GB
ollama pull nomic-embed-text    # the embedding model for similarity retrieval, about 0.3 GB
```

## 3. Give the model a long enough context

The shared answer prompt alone is about 2,700 tokens, and a full context budget adds
several thousand more. Ollama gives each model a fixed context, for example 4,096
tokens, and does not refuse a longer request: it cuts the request down from the
front, dropping the instructions, reports only the tokens it kept, and the model
answers anyway. With a 4,096-token context such a request is cut to about 2,050
tokens. Start the server with a 16,384-token context instead:

- **Linux or macOS, server started by hand**: `OLLAMA_CONTEXT_LENGTH=16384 ollama serve`.
- **Linux service**: run `sudo systemctl edit ollama.service`, add the two lines
  `[Service]` and `Environment="OLLAMA_CONTEXT_LENGTH=16384"`, then run
  `sudo systemctl daemon-reload` and `sudo systemctl restart ollama`.
- **macOS app**: run `launchctl setenv OLLAMA_CONTEXT_LENGTH 16384`, then quit and
  reopen Ollama.
- **Windows**: add a user environment variable `OLLAMA_CONTEXT_LENGTH` with the value
  `16384`, then quit Ollama from the taskbar and start it again.

After the first request, `ollama ps` shows the loaded model's context in its
`CONTEXT` column. In `cache/llm/calls.jsonl`, an `input_tokens` value well below what
the request should take, such as 2,050, means a request was cut; delete the cache
folder before running again, because the cut replies were saved.

## 4. Run a pilot

Install the package with the model SDK from the repository root
(`pip install -e ".[dev,llm]"`, or `".[dev,mem0]"` for the two Mem0 systems). Then select
the local server and the model:

```bash
TRACEMEM_PROVIDER=local TRACEMEM_RESOLVER_MODEL=qwen3.5:4b \
  tracemem run --system tracemem-controlled --split dev --condition gold_candidates
```

In Windows PowerShell, set the variables first:

```powershell
$env:TRACEMEM_PROVIDER = "local"
$env:TRACEMEM_RESOLVER_MODEL = "qwen3.5:4b"
tracemem run --system tracemem-controlled --split dev --condition gold_candidates
```

`tracemem run` reads every scenario under `<root>/<split>`. To run a single pilot,
copy it into a folder of its own; `runs/` is kept out of git:

```bash
mkdir -p runs/pilot-01-only/dev
cp benchmark/scenarios/dev/pilot-01-suggestion-after-decision.yaml runs/pilot-01-only/dev/
TRACEMEM_PROVIDER=local TRACEMEM_RESOLVER_MODEL=qwen3.5:4b \
  tracemem run --system tracemem-controlled --root runs/pilot-01-only --condition gold_candidates
```

A small local model is slower than an API. If requests time out, raise
`TRACEMEM_RESOLVER_TIMEOUT_SECONDS` (at most 300); if replies are cut off, raise
`TRACEMEM_RESOLVER_MAX_COMPLETION_TOKENS`. Thinking is off, so the model answers
directly; `TRACEMEM_LOCAL_THINKING=on` allows it, and then needs a larger token limit.
For a server at another address, set `TRACEMEM_LOCAL_BASE_URL`; Ollama needs no key,
but `TRACEMEM_LOCAL_API_KEY` is sent if a server asks for one.

`TRACEMEM_PROVIDER` applies to the controlled comparison systems. The
`pipeline-resolver-dev` diagnostic still uses the built-in OpenAI client.

## Repeated runs are free

Every complete reply is saved under `cache/llm/` (`TRACEMEM_CACHE_DIR`). The cache key
covers the provider settings, the model settings and the full request, but not the
timeout or the number of attempts. Running the same system on the same scenarios with
the same settings again therefore makes no model calls, costs nothing and gives the
same answers. Errors, refusals and cut-off replies are not saved; they are asked again
next time. A request repeated within one scenario, such as a retry that resends the
same feedback, is also sent to the model again and saved separately, so a retry never
receives the reply it is retrying, and a rerun replays both in order.

A saved reply reports zero tokens, so usage totals count only the calls that reached
the provider. All systems share the cache folder: a system that repeats a request
another system or an earlier run already made also reports zero tokens for it.
`usage.json` shows each scenario's cache hits under `model_cache`. To compare token
usage between systems, run each with `TRACEMEM_CACHE=off` or its own fresh
`TRACEMEM_CACHE_DIR`.

To ask everything again, set `TRACEMEM_CACHE=off` or use a fresh cache folder. Every
completed call, saved or not, is appended to `cache/llm/calls.jsonl` with its model,
tokens, cost and whether it came from the cache. The cache folder is in `.gitignore`;
never commit it.

Embeddings for similarity retrieval always come from the local server
(`TRACEMEM_LOCAL_BASE_URL`, model `TRACEMEM_EMBED_MODEL`), whichever provider answers,
and are saved under `cache/emb/`, keyed by model and text, so each text is embedded
once. `TRACEMEM_CACHE` does not apply to them, and they are not counted in usage.

## Paid runs: Haiku through OpenRouter

The Haiku runs use OpenRouter with a capped budget. Put the key in your private
`.env` in the folder you run from, the repository root (`OPENROUTER_API_KEY=...`,
never committed), or in the process environment, and run:

```bash
TRACEMEM_PROVIDER=openrouter TRACEMEM_RESOLVER_MODEL=anthropic/claude-haiku-5.5 \
  tracemem run --system tracemem-controlled --split dev --condition gold_candidates
```

Requests are routed only to OpenRouter endpoints that support every parameter sent,
so structured output is never silently dropped. Before each paid call the client adds
up every cost in the cost log; once the total reaches `TRACEMEM_BUDGET_USD` (US$12 by
default), the run stops with a "spending cap" error instead of calling the model.
Each cost is OpenRouter's own figure for the call, or else the price table in
`src/tracemem/model_client.py`. A call to a model in neither is logged as `unpriced`
at zero and does not count towards the cap; this includes the default `openai`
provider. Local calls are never capped.

The log covers one machine and one cache folder, so each teammate's spending is
counted separately, and a fresh cache folder starts again from zero. Agree on who
runs paid commands, and with which budget, before starting them.

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `TRACEMEM_PROVIDER` | `openai` | `openai` (built-in client, `OPENAI_API_KEY`), `openrouter` or `local` |
| `OPENROUTER_API_KEY` | none | Read from the environment, else from `.env` |
| `TRACEMEM_LOCAL_BASE_URL` | `http://127.0.0.1:11434/v1` | The local server's OpenAI-compatible address |
| `TRACEMEM_LOCAL_THINKING` | `off` | `on` lets the local model think before answering |
| `TRACEMEM_CACHE` | `on` | `off` neither reads nor saves replies; calls are still logged and capped |
| `TRACEMEM_CACHE_DIR` | `cache/llm` | Saved replies and the cost log `calls.jsonl` |
| `TRACEMEM_BUDGET_USD` | `12` | Spending cap over the whole cost log; counts only priced calls, so not the default `openai` provider |
| `TRACEMEM_EMBED_MODEL` | `nomic-embed-text` | Embedding model on the local server, for similarity retrieval |

The model itself and its request limits are the existing `TRACEMEM_RESOLVER_*`
settings in [`.env.example`](../.env.example).
