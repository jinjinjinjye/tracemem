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
linking the earlier source is the resolver's responsibility. For `ADD-active` and
`SUPERSEDE` with at least one selected proposed/contested target, sources must equal
the set union of every candidate source and those targets' `created_turn` values.
Missing origins and extra sources trigger the existing bounded retry, with both
errors reported together. The Resolver does not silently add or trim citations.
The retry retains the original evidence and asks the model to correct the sources
without dropping justified adoption targets. Overlapping origins appear once.

Allowed sources are candidate sources plus the `source_turn_ids` and `created_turn`
of supplied same-project, same-item records. A visible creation turn remains valid
even when it is absent from that record's source list. Unknown, duplicate or closed
targets are rejected. Selected adoption rejects accumulated support, an active
predecessor's old sources and unselected proposal sources unless they also occur
in the candidate's sources or the selected targets' creating turns. All candidate
sources remain mandatory, even old ones: this is a contract for selected adoption,
not an age-based citation filter. Operations without selected adoption retain the
existing allowed-source rule. An ordinary task progress update can be supported
by the current turn alone. Choosing which open
proposals were actually adopted is still a semantic responsibility: omitting an
otherwise optional adoption target can remain structurally legal. This guard does
not force all same-value proposals to be adopted or reconstruct missing matches.

The component checks the operation against the visible state before returning it.
`OpLog.apply()` still checks the full store, including whether cited turns have
actually been observed. These checks complement rather than replace each other.

## Intent before operation selection

The system prompt's `INTENT_GUIDE` first distinguishes the act expressed in the
clause about the candidate's own item/value, then maps it to the visible state.
An extracted value and a structurally legal target choice do not establish intent.
This is a model instruction, not a keyword classifier or a semantic validator.

| Evidence in the candidate's clause | Intended treatment |
|---|---|
| Criticize the current choice, then suggest trying another | `ADD-proposed`; retain the active value without flagging it. A reason for trying something does not establish adoption. |
| Explicitly select, accept or commit to another value | `SUPERSEDE` if a different active value exists; `ADD-active` before any active value. Reaffirmation of the active value uses `KEEP`. |
| Assert a competing recollection of the existing decision | `FLAG` until the disagreement is explicitly resolved. |
| Undertake work, assign concrete work, or report current progress | Treat as a settled task state. Task value `open` means assigned work, not record status `proposed`. |
| Suggest reopening a cancelled task | `ADD-proposed` with value `open`; the cancelled active record remains until actual reopening is confirmed. |

Future execution and waiting for inputs do not make an undertaking tentative.
An affirmative selection or concrete directive can itself establish adoption:
"We will use Y" and "Let's make Y our choice" do not need a second speaker's
agreement, an existing active record or a separate confirmation phrase. "Let's
consider Y" and a choice conditional on approval remain proposals. This distinction
uses the whole candidate-specific clause, including quotation and withdrawal;
neither `will` nor `let's` is an automatic signal to commit a value.
Approval to undertake work is different from execution/access approval for work
already committed: the latter may be a settled `blocked` update. A direct assignment
phrased as a question differs from asking whether the project should include the
work. Negative decisions and explicit cancellations are still current acts.

The guide uses anonymous contrasting examples, including mixed-item turns and
quoted earlier suggestions followed by explicit adoption. It does not hard-code
Flair, other model names or benchmark item IDs. Words such as `maybe`, `will`, `if`
and `should` are not classification rules. Even a same-value tentative suggestion
must not use `KEEP` to silently resolve disputes. An older mistaken proposal does
not make a new asserted task-status update tentative, and a different-value old
proposal must not be targeted just to repair earlier history.

The final `TRANSITION_EVIDENCE_GUIDE` checks both directions: a settled operation
needs a current selection, assignment or status assertion; a proposed operation
needs a clause that leaves adoption open. Absence of a second confirmation is not
enough to downgrade an affirmative selection. For reopening,
spare capacity, a different value, a past open version or the same speaker's earlier
commitment do not authorize a restart after cancellation. Deliberating whether to
restart is a proposal; assigning or reporting a restart is a settled update. An
explicit challenge to whether the cancellation ever happened is a dispute, distinct
from reporting new progress after it. This check is a prompt instruction, not a
runtime semantic rejection rule. The existing bounded retry repeats this distinction.

The same final check distinguishes criticizing a choice's suitability from asserting
that a different choice was already settled. Criticism followed by asking whether
to switch remains `ADD-proposed`; the absence of adoption does not itself make it a
dispute. A competing claim about the existing agreement may use `FLAG`, while an
affirmative new choice uses a settled operation. The examples use generic reporting
measures, with no metric-name or scenario-specific classification rules.

The six-field output schema, provider configuration and normal one-call flow are
unchanged. Structural failures still trigger the existing bounded retry; the retry
also asks the model to recheck intent. A structurally legal semantic mistake does
not trigger this retry and is not rewritten by code.

## Configuration and optional provider

The core package and its offline tests do not require the provider SDK:

```bash
pip install -e ".[dev]"
pytest tests/test_resolver.py tests/test_resolver_client.py tests/test_resolver_pipeline.py tests/test_resolver_run.py
```

For the OpenAI adapter, install `pip install -e ".[dev,llm]"`. Supply these settings
as process environment variables; [`.env.example`](../.env.example) is a template.
The package does not automatically load `.env` files. The one exception is
`OPENROUTER_API_KEY`, which the comparison systems' OpenRouter provider reads from
`.env` when it is absent from the environment ([local model guide](local-model.md#paid-runs-haiku-through-openrouter)).

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

Each request includes `target_constraints`, computed only from the candidate and
the validated records for its item/project. It names the active record (or null)
and lists structurally legal operations with required and optional targets:

| Visible state | Legal target choices |
|---|---|
| Any state | `ADD-proposed` with no targets, if the dialogue is an unconfirmed suggestion. |
| No active record | `ADD-active` with no required targets; only same-value open proposals may be adopted as optional targets. An older, different-value proposal is not a current decision. |
| Active value equals candidate | `KEEP` targeting exactly the active record. |
| Active value differs | `SUPERSEDE` must target the active record and may adopt same-value open proposals/claims; `FLAG` must target exactly the active record. |

These choices describe structural legality, not the correct interpretation of the
dialogue. The model still chooses the act and evidence. The resolver does not remove
bad targets, switch operations, or manufacture a successful write. Existing local
validation and the storage contract still reject invalid decisions. Other open
disputes are settled by storage when `KEEP`/`SUPERSEDE` is applied; they are not extra
targets just because they need closing.

After a rejected decision, the next request contains the original evidence plus
one JSON feedback message: the validation error, the same target choices, and the
rejected `op`, `add_as`, `targets` and `source_turn_ids`. Only schema-valid decisions
contribute these fields. Each echoed ID list is limited to 32 entries and each ID
to 256 characters; `rejected_decision_truncated` identifies a shortened echo. This
limit applies to feedback only, not to the operation contract. Arbitrary rationale,
reason, malformed JSON and provider error text are not replayed. Schema failures,
refusals and incomplete responses receive static feedback without a rejected
decision. Feedback replaces the previous feedback rather than accumulating across
attempts, and is reset for each candidate. Transient provider failures resend the
pending request within the same attempt limit.

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

`describe()` returns model settings, client class, system-prompt SHA-256, output
schema SHA-256 and `decision_policy_hash`. The latter fingerprints the target-policy,
source-policy and intent-policy versions, retry instructions, echoed fields and
feedback limits; increment the corresponding version when changing those policies.
The current intent policy is `candidate-speech-act-v4` and the executable adoption
source policy is `selected-adoption-origins-v2`; guide text
is also covered by the system-prompt hash. Controlled comparison manifests
carry it as `resolver_reference_policy_hash` in all three arms, so a run with a
different resolver request policy cannot silently enter the same comparison.
`usage()` counts all attempted calls and reported tokens, including
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
| `usage.json` | Resolver write-path calls and provider-reported tokens, by scenario and in total. Controlled comparison systems also report separate answer-model usage; no token-to-currency conversion is made. |
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

The Resolver also powers `tracemem-controlled` and `tracemem-no-versions`, alongside
the native `mem0-classic` baseline. These gold-candidate-only systems share model
settings and an answerer without gold retrieval. See [the comparison guide](memory-comparison.md)
for the precise ablation, native-history policy, offline tests and reproducible run commands.

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

`tests/fixtures/resolver_failures.json` preserves eight exhausted candidates from
the first real-model development comparison (five TraceMem, three current-only),
including all sixteen rejected attempts and the visible state at each failure.
`tests/test_resolver_regressions.py` checks that feedback identifies each rejection,
that a scripted corrected decision applies through the real operation log, and that
repeating the original bad decisions still fails without mutating memory. The
fixtures are synthetic development data; corrections are test-only replies, not new
benchmark labels or evidence that a live model's failure rate has improved.
`tests/test_resolver_feedback.py` covers target choices, bounded feedback, retries
and policy fingerprints independently of those recorded examples.

`tests/fixtures/resolver_intent_failures.json` preserves nine development examples:
eight semantic mistakes accepted at capture time and one correct dispute control.
They cover Flair suggestions interpreted as replacement/dispute, definite model
and task commitments interpreted as proposals, task assignment/progress, suggested
reopening, and a further tentative-alternative error. The intent regression tests
replay the original replies and scripted corrections through the real operation log,
including the task commitment -> cancellation -> proposed reopening lifecycle.
They check that the guide reaches the model while the original candidate/records
and six-field contract are preserved. The intent-policy tests additionally cover
ambiguous wording boundaries, retry instructions and reproducibility fingerprints.
These tests verify request assembly and state effects, not live-model intent
accuracy. One captured reopening mistake also omitted its adopted proposal's source
and is now rejected by the provenance guard; its original state effects are retained
as a replay control. The other captured semantic errors remain structurally valid;
a development model rerun is required to measure whether the revised prompt reduces them.

Before merging, run `pytest`, `tracemem validate`, `python scripts/check_decisions.py`
and `python scripts/check_public.py`. The four contract files remain unchanged.

`tests/fixtures/task_reopening_failures.json` captures the later development failure
with a correctly recorded cancellation and superseded open history, plus the shared
answerer's false conflict on cancellation with a reopening proposal. The reopening
regression tests replay both structurally valid bad replies and scripted corrections,
including commitment -> cancellation -> proposal -> explicit adoption through both
stores. The policy tests cover real dispute controls, restarted work, historical
questions, unrelated-item disputes, missing context and native Mem0 evidence.
See [decision 0005](decisions/0005-interpret-task-reopening.md) for the shared read/write
policy and its offline-validation limits.

`tests/fixtures/explicit_decision_failures.json` captures development replies that
downgraded the spaCy selection and the initial logistic-regression selection to
proposals, along with the subsequent baseline chain. The explicit-decision
regressions replay both observed and corrected replies. They check the first active
choice, an unaccepted alternative, an actual replacement, reaffirmation, predecessor
links, source preservation and historical snapshots in the versioned store. The
current-only store checks deliberate history omission instead. A proposal-only
bad prior state cannot supply a predecessor: a later `ADD-active` is legal there,
and the Resolver must not fabricate a past decision to force `SUPERSEDE`.

The policy tests add generic affirmative/conditional/withdrawn and mixed-item
contrasts, structurally invalid replacement retry, and reopening contrasts. The
existing reopening and answer-state tests stay enabled. Scripted replies establish
state and request contracts, not live model classification accuracy. Existing saved
wrong states are not repaired in place; a new rollout must replay the write chain.
That affirmative-selection update changed Resolver prompt/policy fingerprints only; the shared answer
prompt, renderer, model configuration and output schemas remain unchanged. See
[decision 0006](decisions/0006-recognize-affirmative-selections.md).

The subsequent provenance repair in
[decision 0007](decisions/0007-preserve-adoption-and-history-evidence.md) changes both
the Resolver and the shared answer prompt. `tests/fixtures/resolver_provenance_failures.json`
preserves six observed acceptance-source omissions across the two Resolver arms,
the macro-F1 suggestion wrongly flagged as a dispute in the current-only arm, and
correct dispute controls. The provenance regressions replay missing-source rejection,
scripted correction and exhaustion without mutation, including a contested target
left by the earlier macro-F1 error. They also replay the corrected proposal followed
by formal acceptance through both stores. Unlike the semantic misclassification,
the captured source omissions now fail executable validation.

`tests/test_resolver_source_policy.py` covers multiple adopted targets, accumulated
support, visible creation metadata, filtered foreign records, bounded diagnostics
and ordinary revisions that do not adopt proposals. Existing affirmative-selection,
SVM replacement/history and reopening tests remain enabled. Historical citation
regressions use the same answer policy across all three arms; see
[the comparison guide](memory-comparison.md). These tests establish validation and
scripted state effects, not improved live classification or citation completeness.

The later precision repair in
[decision 0008](decisions/0008-constrain-adoption-and-answer-evidence.md) rejects extra
sources as well as omissions on selected adoption. The four captured failures in
`tests/fixtures/adoption_source_precision_failures.json` retain the actual requests
and replies for DistilBERT and macro-F1 acceptance in both Resolver arms. The tests
replay rejected overcitation, corrected writes and exhausted retries through the
real stores, preserving predecessor history where available. Generic tests cover
candidate-supplied old support, unselected and accumulated sources, overlapping
origins, combined/bounded diagnostics and unaffected non-adoption operations.
The pipeline regression checks `generation_failed`, unchanged memory and recovery
on a later candidate. Intent policy v4 and its formal-selection, macro-F1 and
reopening distinctions remain unchanged. Reader evidence checks are shared across
all three arms and remain prompt instructions; see the comparison guide.

The source-retry repair in
[decision 0009](decisions/0009-preserve-adoption-during-source-retries.md) retains a
candidate-local snapshot of the first structurally legal adoption rejected for its
sources. Subsequent replies must preserve its `op`, `add_as` and complete target
set; target order may change. This prevents repairing extra citations by silently
dropping the adopted proposal or claim. Source errors include missing candidate or
origin sources, duplicate sources, unavailable sources and extra sources. All
operation and target checks run first, so an initially illegal structure remains
fully correctable. Operations without selected adoption targets are not locked.

`source_repair_constraints` and a source-specific instruction accompany subsequent
feedback, including after a malformed/refused reply or a target-changing reply.
Transient failures retain the pending request. The original constraint persists
until success or exhaustion and never crosses candidates. Feedback previews are
bounded, while validation retains the entire target set. The existing attempt limit
and usage accounting remain unchanged. A truncated preview may not let the model
recover every originally selected target from the initial records; this can exhaust
the budget, but cannot silently relax the full-set check. Exhaustion raises `ResolverError`; the
pipeline logs `generation_failed` without applying either rejected operation.
There is no automatic target restoration or source completion.

`tests/fixtures/adoption_retry_failures.json` captures four actual two-reply sequences
from the subsequent development rerun: DistilBERT and macro-F1 in each Resolver
arm, first overciting and then deleting an adoption target. The regressions reject
both replies without mutation, then exercise a scripted third reply that corrects
sources while retaining adoption. They check proposal closure, exact sources,
version history where retained, and both stores' pipeline failure/success logs.
`tests/test_resolver_source_retry.py` covers generic repair boundaries and lifecycle.

This guard preserves a selected adoption; it does not prove the first decision's
semantic intent, infer a target omitted in the first reply, or repair candidate
sources. A wrongly selected but structurally legal adoption must fail safely if
it cannot be repaired within these constraints. The formal-decision, SVM history,
macro-F1 suggestion and reopening suites remain enabled with unchanged intent
guides. Live improvement and any increase in exhausted writes require a new run.
