# Model-backed Resolver

`LLMResolver` in [`resolver.py`](../src/tracemem/resolver.py) implements the existing
`resolve(candidate, related) -> Operation` interface. It uses a model to distinguish
a settled decision, a suggestion, a reaffirmation, a revision and an unresolved
dispute. It never reads benchmark scripts or gold labels, applies operations, or
sets record statuses. `OpLog` remains the authority for storage semantics.

This component is implemented independently of the runnable systems. The registry
still uses the gold stand-ins. Pipeline failure logging, CLI registration, resolver
metrics, Mem0 integration and the end-to-end comparison belong to subsequent work.
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
pytest tests/test_resolver.py tests/test_resolver_client.py
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
The existing pipeline only catches storage `InvalidOperation`; it does not yet catch
these resolver exceptions. Until pipeline integration lands, callers must handle
them explicitly. The intended later recovery is to record a candidate failure and
leave the stored memory unchanged, with setup errors terminating the run.

`describe()` returns model settings, client class, system-prompt SHA-256 and output
schema SHA-256. `usage()` counts all attempted calls and reported tokens, including
invalid completions and retries, across this resolver instance. Tokens from a failed
request without a provider usage response are unknown, not a complete billing total.
Writing these fields to the run manifest/log is part of pipeline integration.

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
