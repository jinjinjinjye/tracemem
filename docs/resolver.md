# Model-backed Resolver

`LLMResolver` in [`resolver.py`](../src/tracemem/resolver.py) implements the existing
`resolve(candidate, related) -> Operation` interface. It uses a model to distinguish
a settled decision, a suggestion, a reaffirmation, a revision and an unresolved
dispute. It never reads benchmark scripts or gold labels, applies operations, or
sets record statuses. `OpLog` remains the authority for storage semantics.

The registered `pipeline-resolver-dev` system runs this resolver with gold extraction,
matching and retrieval, plus the rule answerer. It is marked `uses_gold=True`: a
component diagnostic, not an end-to-end baseline. Pipeline failure logging and
configuration/usage export and operation-level evaluation are implemented. Mem0
integration and the end-to-end comparison belong to subsequent work.
Offline tests verify parsing, validation and state effects; they do not establish
the model's accuracy or an advantage over Mem0.

## Input and output

The extractor supplies a candidate whose first source turn is the current turn and
whose ID is `<item>@<current turn>`. The matcher supplies the current active record,
relevant open proposals and disputes, and useful history. Records from another
project or item are filtered out before the model sees them. Invalid candidate IDs,
duplicate record IDs, multiple active records and records without statuses fail
before any model request.

The model chooses only `op`, `add_as`, `targets`, `source_turn_ids`, `reason` and
`rationale`. All six fields are required, including nullable `add_as` and `reason`;
unknown fields are rejected. Code derives the operation ID, candidate ID, current
turn, item and value from the candidate. The model cannot rewrite these fields.

| Situation | Operation and constraints |
|---|---|
| First confirmed value | `ADD`, `add_as="active"`; no active record may exist. |
| Unconfirmed suggestion | `ADD`, `add_as="proposed"`; targets must be empty. |
| Explicitly reaffirm the active value | `KEEP`, targeting exactly the active record. This settles all open disputes. |
| Confirm a different value | `SUPERSEDE`, targeting the active record; additional targets must be open proposals or contested claims with the new value. |
| Assert a different current value without settling the disagreement | `FLAG`, targeting exactly the active record. |
| Accept a proposal before any active value | `ADD-active`, targeting the adopted proposal. |
| Accept a proposal replacing an active value | `SUPERSEDE`, targeting the active record and adopted proposal. |

For acceptance, the model must cite the confirmation and the original proposal.
The candidate carries only the confirmation in the gold-candidate condition, so
linking the earlier source is the resolver's responsibility. Citations must come
from the candidate or supplied same-item records and must contain every candidate
source. Unknown, duplicate or closed targets are rejected. Targeting a record does
not automatically copy its citations: for example, an ordinary task progress
update can be supported by the current turn alone.

The component checks the operation against the visible state before returning it.
`OpLog.apply()` still checks the full store, including whether cited turns have
actually been observed. These checks complement rather than replace each other.

## Configuration and optional provider

The core package and its offline tests do not require the provider SDK:

```bash
pip install -e ".[dev]"
pytest tests/test_resolver.py tests/test_resolver_client.py tests/test_resolver_pipeline.py tests/test_resolver_run.py
```

For the OpenAI adapter, install `pip install -e ".[dev,llm]"`. Supply these settings
as process environment variables; [`.env.example`](../.env.example) is a template.
The package does not automatically load `.env` files.

| Variable | Default / requirement |
|---|---|
| `TRACEMEM_RESOLVER_MODEL` | Required. Use the team's chosen model supporting Chat Completions and strict JSON-schema output; pin a snapshot for experiments. |
| `OPENAI_API_KEY` | Required only when constructing the OpenAI client. Never part of `ResolverConfig` or `describe()`. |
| `TRACEMEM_RESOLVER_TIMEOUT_SECONDS` | 30; positive, at most 300. Applied to each provider request. |
| `TRACEMEM_RESOLVER_MAX_ATTEMPTS` | 2 total attempts per candidate, including the first; range 1-5. |
| `TRACEMEM_RESOLVER_MAX_COMPLETION_TOKENS` | 1024; range 1-65536. Increase if the selected model needs more output/reasoning tokens. |
| `TRACEMEM_RESOLVER_TEMPERATURE` | Omitted by default. Optional 0-2; set only if supported by the chosen model. |

No model is selected implicitly. `ResolverConfig.from_env()` rejects missing or
invalid settings without echoing environment values. Configuration is immutable.

```python
from tracemem.resolver import LLMResolver

resolver = LLMResolver.from_env()
# Given an extracted candidate, matched records and the existing operation log:
operation = resolver.resolve(candidate, related)
log.apply(operation)
```

Construction does not send a request. `resolve()` does. The adapter targets
`https://api.openai.com/v1` explicitly and uses
[Chat Completions structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat).
Other providers can implement `CompletionClient.complete(config=..., messages=...,
response_format=...) -> ModelReply` and be injected into `LLMResolver(config, client)`.
There is no provider-specific code in the decision validation path.

Once the chosen model and credentials are configured, run the development diagnostic:

```bash
tracemem systems
tracemem run --system pipeline-resolver-dev --split dev --condition gold_candidates
```

Listing systems never constructs a client. Running this system constructs a fresh
resolver for every scenario and makes model calls. The gold timeline is used only
by the stand-ins; `LLMResolver` sees the candidate and matched records. The default
`end_to_end` condition also uses `GoldExtractor` in this diagnostic, so it remains
a gold-assisted mock in either condition. Use the real extractor/matcher/retriever
before making end-to-end claims.

## Failures and reproducibility

- `ResolverInputError`: malformed input or inconsistent matched state; no request is made.
- `ResolverConfigError`: missing SDK, credentials or invalid configuration; fix setup.
- `FatalModelError`: provider authentication, permissions or other non-transient request
  errors; propagated immediately. No raw provider error body is exposed.
- `ResolverError`: all attempts failed due to timeout, connection/transient HTTP
  failure, malformed output, refusal, truncation or an illegal decision. It carries
  `candidate_id`, `attempts` and a validation detail. No operation is fabricated.

The adapter disables SDK automatic retries, so `max_attempts` bounds the actual
requests for a candidate. Transient status codes are 408, 409, 429 and server errors.
Retries also cover invalid model decisions and include validation feedback when
available. Programming errors are not caught as model failures.

`KEEP` is a real confirmation that resolves disputes. It is never an error fallback.
The pipeline catches `ResolverError`, records a `generation_failed` event, skips the
write and continues with the next candidate. Incoming turns and candidates are still
recorded; existing memory records and operations are unchanged. Storage rejections
remain `InvalidOperation` events and are kept separately in `rejected_ops.jsonl`.

Input, configuration and fatal provider errors stop the run. A failure during
resolution produces an `aborted` event; a failure during factory construction has
no candidate event. The harness preserves completed questions, applied/rejected
operations, candidate events and reported usage in `RunAborted.result`. The CLI
saves these diagnostics with `manifest.status="failed"`, prints a clear error and
returns exit code 2. Failed runs cannot be loaded by `tracemem report`, even with
`--allow-mixed`. Earlier manifests without a status retain their completed meaning.
Aborted test-split attempts still append to `results/test-runs.jsonl`, with failed
status, configuration and failure details; their accuracy is null.
Unexpected programming errors still propagate normally; this is not a catch-all
recovery or resume mechanism.

`describe()` returns model settings, client class, system-prompt SHA-256 and output
schema SHA-256. `usage()` counts all attempted calls and reported tokens, including
invalid completions and retries, across this resolver instance. Tokens from a failed
request without a provider usage response are unknown, not a complete billing total.
The pipeline exposes this configuration under `system_config.resolver_config` in
the manifest. It measures usage deltas around each candidate, so retry calls are
counted once, then the harness sums final scenario totals without summing cumulative
snapshots repeatedly.

| Artifact | Contents |
|---|---|
| `manifest.json` | Model/settings, prompt/schema hashes, `status` and optional failure type/message/scenario. |
| `resolver_events.jsonl` | One row per processed candidate: scenario, turn, candidate, item, status, operation ID, attempts, usage and optional error type/detail. |
| `resolver_errors.jsonl` | Generation failures and aborts from those events; not storage rejections. An instrumented successful run has an empty error file. |
| `usage.json` | Resolver write-path calls and provider-reported tokens, by scenario and in total. It does not include answer-model usage or convert tokens into currency. |
| `ops.jsonl`, `rejected_ops.jsonl`, `candidates.jsonl` | Existing operation/candidate artifacts, preserving their earlier formats. |

Event statuses are `applied`, `rejected`, `generation_failed` and `aborted`. Missing
usage instrumentation is represented as null in an event, never invented zero
counts; the usage file is emitted only when the system reports usage. Successful
legacy gold runs retain their earlier artifact set. Logs contain validated operation
data and sanitized exception details, not raw provider error bodies or credentials.
The CLI also prints resolver outcome counts for completed instrumented runs, so a
run with many skipped candidates is visible even though it completed normally.

The proposed cross-component conventions are recorded in
[decision 0002](decisions/0002-record-resolver-failures.md).

## Operation evaluation

Completed `gold_candidates` runs now add `resolver_metrics.json`,
`resolver_scores.jsonl` and `resolver_analysis.jsonl`. Use
`tracemem resolver-report runs/<saved-run-folder>` to inspect five-label F1,
act/operation confusion, cumulative state accuracy, target/source errors and failures.
Missing candidates remain in denominators; rejected operations keep their emitted
label but cannot earn applied exact-operation credit. The complete definitions and
offline check command are in [the metrics guide](metrics.md#9-resolver-operation-metrics-and-error-analysis).
The scorer uses gold after a scenario completes and never feeds it back into the resolver.

## Boundaries to keep visible in experiments

- There is no `NOOP` or abstention operation in the existing contract. Extraction
  should filter passing mentions. The resolver cannot make an unsupported statement
  harmless by returning `KEEP`; a new skip policy would need explicit design work.
- `Record` does not include historical raw dialogue, and `Candidate` does not include
  item-kind or speaker-authority metadata. The prompt uses only the supplied evidence.
- The resolver cannot distinguish a truly empty item from a matcher that missed its
  active record. Matcher recall and current-record coverage must be checked at integration.
- Offline scripted replies test the implementation, not the model's interpretation.
  Semantic quality must be measured separately on development scenarios, then on the
  sealed test split after settings are frozen.

Before merging, run `pytest`, `tracemem validate`, `python scripts/check_decisions.py`
and `python scripts/check_public.py`. The four contract files remain unchanged.
