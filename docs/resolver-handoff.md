# Resolver integration quickstart

The Resolver, pipeline diagnostics, operation metrics and offline regressions are
implemented for review. Team integration and validation of the latest reader fixes
with a real model remain pending. This guide does not imply approval or a merge.

## Run the offline demo and checks

Use Python 3.11 or newer and check out the PR branch in an existing clone. Run the
following from the repository root. Dependency installation downloads packages;
the demo and tests use scripted replies and need no API credentials.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,mem0]"
.\.venv\Scripts\python.exe scripts/resolver_offline_demo.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m tracemem.cli validate benchmark/scenarios/dev
.\.venv\Scripts\python.exe scripts/check_decisions.py
.\.venv\Scripts\python.exe scripts/check_public.py
```

macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,mem0]'
.venv/bin/python scripts/resolver_offline_demo.py
.venv/bin/python -m pytest
.venv/bin/python -m tracemem.cli validate benchmark/scenarios/dev
.venv/bin/python scripts/check_decisions.py
.venv/bin/python scripts/check_public.py
```

The Mem0 extra installs the pinned native SDK so its offline tests run too. A core
installation with `.[dev]` can run the demo, but skips tests needing that SDK.
The demo's final check is:

```text
PASS: all integration assertions passed; 4 scripted calls, 0 network calls.
```

The sequence is BERT decision, DistilBERT suggestion, formal adoption, later
confirmation, then a historical snapshot. It uses the real Resolver validation and
`OpLog` with explicit mock model replies: a suggestion leaves BERT current; adoption
closes both BERT and the accepted proposal; confirmation adds evidence without a
new version; the historical snapshot still shows BERT before adoption. This checks
wiring and storage semantics, not live-model accuracy or generated answers.

## Connect the component

The boundary remains `Candidate` plus related `Record` objects in, `Operation` out:

```python
resolver = LLMResolver(config, client)
operation = resolver.resolve(candidate, related_records)
log.apply(operation)
```

The caller observes source turns in the store before applying an operation. The
Resolver does not extract candidates, retrieve records, mutate storage or answer
the user's question. The matcher must retain relevant proposals and their sources
so adoption targets can be selected. Keep the existing shared contracts intact.

Read [the Resolver guide](resolver.md) for `CompletionClient.complete(...) ->
ModelReply`, input rules and retries; [interfaces](interfaces.md) for component
types; and [operation metrics](metrics.md#9-resolver-operation-metrics-and-error-analysis)
for write evaluation. The pipeline records applied, rejected, generation-failed
and aborted writes. Exhausted generation skips a write rather than inventing an
operation; configuration and fatal provider errors abort. Count these failures in
evaluation alongside successful writes.

## Choose the model adapter explicitly

`LLMResolver.from_env()`, and so `pipeline-resolver-dev`, use
`OpenAICompletionClient`, whose endpoint is fixed to `https://api.openai.com/v1`.
Changing a base-URL environment variable does not redirect it. The package does
not load `.env` automatically, except for `OPENROUTER_API_KEY` (below);
`.env.example` documents the configuration names.

The default comparison factory takes its client from `model_client.from_env()`:
`TRACEMEM_PROVIDER` selects the same OpenAI client, OpenRouter or a local Ollama
server, and every arm gets the same reply cache and spending cap
([local model guide](local-model.md)). Another backend needs its own
`CompletionClient` adapter and a compatibility check for structured responses, usage,
timeouts and error handling. Inject the same adapter/configuration into every comparison arm.
The private runner used for earlier OpenRouter experiments is not included here.
Agree on the exact provider, model/version, request limits and budget before
running paid commands in [the comparison guide](memory-comparison.md).

## Review scope and remaining work

The included comparison is the earlier three-system setup: `tracemem-controlled`,
`tracemem-no-versions` and native `mem0-classic` 1.0.11 with history. It uses the same
gold candidates and model settings with a shared answerer. It is a component
experiment, not the newer five-system plan or an end-to-end product evaluation.
Alignment with that plan remains a team decision. `pipeline-resolver-dev` is a
separate diagnostic using gold stand-ins.

Before integration, agree on the receiving branch, integration owner and reviewer;
check a real extractor candidate and matcher result against the public types;
confirm that the receiving store preserves adoption links, evidence and history;
and assign ownership of the shared model adapter and experiment runner. Review
the changes on the PR branch rather than replacing a teammate's whole checkout.

The latest provenance and historical-state reader fixes have offline regression
coverage but still need a real-model development rerun. Earlier live results do
not validate these later changes. Report Resolver writes and reader answers
separately, including retries, exhausted/skipped writes, abstentions and citation
completeness. Offline success does not establish general superiority over Mem0.
Keep development tuning separate from sealed test scenarios. Proposed method
changes and their limits are recorded in [the decision index](decisions/README.md).
