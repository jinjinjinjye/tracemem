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
`CONTEXT` column. The local client checks it for you: after every reply it reads the
model's context from the server's `/api/ps` and stops the run, saving nothing, unless
it equals `TRACEMEM_LOCAL_CONTEXT_TOKENS` (16,384 by default). It also stops the run
when the server reports reading fewer tokens than one for every six bytes of the
request, which means the request was cut even at that context; requests take about
four bytes a token. The server must therefore be Ollama. If your computer cannot hold
a 16,384-token context, start the server with a smaller one and set
`TRACEMEM_LOCAL_CONTEXT_TOKENS` to the same number: a request too long for it then
stops the run instead of being answered in part.

The context is part of the recorded model settings, so `tracemem report` refuses to
compare runs made with different contexts, and a reply saved under one context is
never replayed under another. Runs and saved replies made before this check existed
do not record a context: they cannot be reported beside newer runs, and a newer run
asks the model again.

A tag such as `qwen3.5:4b` does not fix the weights: pulling it again can bring new
weights or a new template under the same name. Before a run, the local client
therefore reads the model's digest from the server's `/api/tags` and records it with
the other model settings. A model pulled again gets a new digest, so its replies are
never mixed with replies saved from the old weights, and `tracemem report` refuses
to compare runs made on different weights, including two teammates' runs. If the
model is not installed, the run stops before it starts and names the `ollama pull`
command to run. Runs and saved replies made before the digest was recorded cannot be
reported beside newer runs either, and a newer run asks the model again.

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
`TRACEMEM_RESOLVER_MAX_COMPLETION_TOKENS`. A timeout is retried within
`TRACEMEM_RESOLVER_MAX_ATTEMPTS`, but a server that refuses or drops the connection
is down, so the run stops with an error and is saved as failed; otherwise every
remaining question would be scored as a failed answer. Start the server again and
rerun: the saved replies make the repeated part free. Thinking is off, so the model answers
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
completed call, saved or not, is appended to the cost log, `cache/costs.jsonl`
(`TRACEMEM_COST_LOG`), with its model, tokens, cost and whether it came from the
cache. The cost log is not inside the cache folder, so every cache folder adds to the
same log. The `cache/` folder is in `.gitignore`; never commit it.

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
so structured output is never silently dropped. Before each paid call the client
reads the cost log again and adds up every cost in it; once the total reaches
`TRACEMEM_BUDGET_USD` (US$12 by default), the run stops with a "spending cap" error
instead of calling the model. Each cost is OpenRouter's own figure for the call, or
else the price table (`PRICES_PER_MILLION` in `src/tracemem/model_client.py`). So
that no call escapes the cap when OpenRouter omits its figure, the openrouter
provider accepts only a `TRACEMEM_RESOLVER_MODEL` in that table, and refuses any other
before the run starts; to use another model, add its prices to the table first. A
call through the default `openai` provider is logged as `unpriced` at zero and does
not count towards the cap. Local calls are never capped. A call is logged before its
reply is saved, so a reply that cannot be saved, for example on a full disk, is still
counted.

The cost log, `cache/costs.jsonl` unless `TRACEMEM_COST_LOG` names another file, does
not depend on the cache folder. A fresh cache folder therefore keeps the spending
already logged, and runs going on at the same time on one machine share one cap,
because each reads the log again before every paid call. A relative path is read from
the folder you run in, so run paid commands from the repository root. The log covers
one machine, so each teammate's spending is counted separately. Agree on who runs
paid commands, and with which budget, before starting them.

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `TRACEMEM_PROVIDER` | `openai` | `openai` (built-in client, `OPENAI_API_KEY`), `openrouter` or `local` |
| `OPENROUTER_API_KEY` | none | Read from the environment, else from `.env` |
| `TRACEMEM_LOCAL_BASE_URL` | `http://127.0.0.1:11434/v1` | The local server's OpenAI-compatible address |
| `TRACEMEM_LOCAL_API_KEY` | `local` | Sent to the local server; Ollama ignores it, so set it only for a server that checks one |
| `TRACEMEM_LOCAL_THINKING` | `off` | `on` lets the local model think before answering |
| `TRACEMEM_LOCAL_CONTEXT_TOKENS` | `16384` | The context the local server must give the model (`OLLAMA_CONTEXT_LENGTH`); checked after every reply |
| `TRACEMEM_CACHE` | `on` | `off` neither reads nor saves replies; calls are still logged and capped |
| `TRACEMEM_CACHE_DIR` | `cache/llm` | Saved replies |
| `TRACEMEM_COST_LOG` | `cache/costs.jsonl` | The cost log: every completed call with its cost, whatever the cache folder |
| `TRACEMEM_BUDGET_USD` | `12` | Spending cap over the whole cost log; counts only priced calls, so not the default `openai` provider |
| `TRACEMEM_EMBED_MODEL` | `nomic-embed-text` | Embedding model on the local server, for similarity retrieval |

The model itself and its request limits are the existing `TRACEMEM_RESOLVER_*`
settings in [`.env.example`](../.env.example).
