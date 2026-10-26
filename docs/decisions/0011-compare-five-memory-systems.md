---
id: 11
title: Compare five memory systems through one retriever and one answer prompt
status: proposed
date: 2026-10-25
decided_by: []
supersedes: []
superseded_by: []
---

# 0011. Compare five memory systems through one retriever and one answer prompt

## Context

[Decision 0004](0004-compare-controlled-memory.md) (the controlled comparison of
TraceMem, its current-only ablation and classic Mem0) compares three
gold-candidate systems. RQ1 ("Does TraceMem give fewer outdated answers and fewer
wrong replacements than a memory that retrieves by similarity, with and without a
preference for recent statements?") needs two baselines without a write path, and
[the metrics guide](../metrics.md#5-the-metrics) reads one RQ1 comparison against
each. A third new system gives Mem0 TraceMem's rules in its update prompt, so that
what the rules contribute can be told apart from what TraceMem's operation log
contributes. The repository now registers these three systems, and every compared
system selects its context through one retriever, `SharedRetriever` in
[`retrieval.py`](../../src/tracemem/retrieval.py). This record proposes that
protocol: it builds on decision 0004, changes only which of its systems are
compared, and keeps the answer validation and historical reads of
[decision 0010](0010-validate-reader-evidence-and-historical-state.md).

## Decision

Five systems are compared on gold candidates: `similarity` and
`similarity-recency` over every candidate as a record without a status,
`mem0-classic` and `mem0-instructions` over native Mem0 memories, and
`tracemem-controlled` over its operation log. All five select their context
through one retriever (`alpha=0`, `alpha=0.3` with a 7-day half-life, and
`alpha=1` for the other three) and answer through one shared prompt, client and
validator. Only the similarity systems' lines quote their source turn, and
`mem0-instructions` adds the project rules below after Mem0's default update
prompt. `tracemem-no-versions` leaves the compared set and stays registered as a
diagnostic.

The details follow. All five accept only `--condition gold_candidates`, and none
receives the gold timeline, expected answers or the question-to-item mapping.
Decision 0004 compares `tracemem-no-versions`, its current-only ablation, as one
of its three systems. This record replaces that part of 0004: the ablation runs
under the same shared settings, but as a diagnostic outside the five reported
systems (open question 6). Decision 0004's record is left as it is.

| System | Write path | Store | Retriever |
|---|---|---|---|
| `similarity` | none | every observed candidate as one record without a status (`ops.flat_records`) | similarity to the question (`alpha=0`) |
| `similarity-recency` | none | the same | similarity and recency (`alpha=0.3`, `half_life_days=7`) |
| `mem0-classic` | the native `mem0ai` 1.0.11 update engine with its own update prompt | current native memories and every native history event | newest first (`alpha=1`) |
| `mem0-instructions` | the same engine, with the project rules below after the SDK's default update prompt | the same | newest first (`alpha=1`) |
| `tracemem-controlled` | `LLMResolver` and `OpLog` | current and closed records with statuses, sources and supersession links | newest first (`alpha=1`) |

- **One retriever.** Each record scores `(1 - alpha) * cosine(question, line) +
  alpha * 0.5 ** (age_days / half_life_days)`, where the line is the record's
  context line and the age runs from its `created_at` to the latest observed turn.
  Records are taken in descending score, newest first among equal scores, while
  they fit the shared byte budget (`TRACEMEM_CONTEXT_BUDGET_BYTES`, default 12,000
  UTF-8 bytes). A line that does not fit is skipped whole, and the selection is
  shown in time order. At `alpha=1` no embedding is computed, and the selection
  equals that of the comparison's earlier newest-first reader
  (`_selected_context` in [`comparison.py`](../../src/tracemem/systems/comparison.py)),
  ties included: newest first by creation time, creating turn, item, value and
  record id. The similarity + recency weight and half-life are provisional and may
  be tuned on development scenarios only. The embedding model is the subject of
  [decision 0013](0013-embed-with-nomic-embed-text.md).
- **A fixed number of records per answer (question 4 below, settled 26 Oct).**
  With `TRACEMEM_CONTEXT_TOP_K=k`, every system shows the answering model at most
  `k` records: the `k` best-scoring that fit the byte budget, still shown in time
  order. `similarity`, both Mem0 systems and TraceMem then rank by similarity alone
  (`alpha=0`); `similarity-recency` keeps its recency weight, its one difference.
  Every system records `k` as `context_top_k` in its comparison settings, so runs
  with different `k` cannot be reported together. Unset, every system selects as
  above, and Mem0 and TraceMem keep the newest-first selection. `k` is fixed by a
  rule that reads no system's answers: the smallest `k` that puts every turn a
  question's correct answer rests on (its required support) on the page for at
  least 90% of the development questions, measured on the similarity store
  ranked by closeness ([`scripts/choose_top_k.py`](../../scripts/choose_top_k.py)).
  On the 13 development scenarios of 26 Oct it gives `k = 4` (157 of 165
  questions covered; `k = 3` covers 147). It is recomputed whenever the
  development scenarios change before the freeze, and frozen with the prompts.
- **Quoted source turns for the similarity systems only.** Their store is the
  candidate text itself, so each of their lines adds the quoted text of the
  record's first source turn, as `render_records` writes it when given the turns.
  Without the quote, a line with no status cannot tell a suggestion from a
  decision. For pilot-01 S2-T3 ("Maybe we could try DistilBERT?"), the line without
  and with the quote is:

  ```text
  S2-T3 Arun: model.sentiment = DistilBERT | sources=S2-T3
  S2-T3 Arun: model.sentiment = DistilBERT "Maybe we could try DistilBERT? It might be faster." | sources=S2-T3
  ```

  The Mem0 and TraceMem systems keep their earlier lines, with no dialogue, so
  that discarded versions cannot come back through turn text. The quote is part of
  the text that is embedded and of the bytes that are budgeted.
- **Mem0 with project instructions.** `mem0-instructions` uses the update prompt
  of `mem0-classic`, the installed SDK's own default, followed by a blank line and
  `PROJECT_RULES` from [`mem0_baseline.py`](../../src/tracemem/systems/mem0_baseline.py),
  exactly:

  ```text
  Project rules. They were written for a memory whose operations are ADD-proposed, ADD-active, FLAG, KEEP and SUPERSEDE; apply their intent using ADD, UPDATE, DELETE and NONE.
  1. Locate the clause about THIS candidate's item and value. Decide whether the speaker
     commits to it, merely proposes it, or challenges what is already settled. Do not
     transfer a commitment about another item/value to this candidate. Candidate.value
     is an extracted value, not proof that anyone accepted it.
  2. A suggestion asks for consideration, a trial or approval without adopting the
     candidate value. Use ADD-proposed, even if it criticizes the current choice or
     gives a strong reason for an alternative. A performance complaint is not itself
     a disagreement about which value is currently settled. Neither FLAG nor SUPERSEDE
     is justified by a tentative alternative alone.
  4. A dispute asserts a competing claim about the existing decision without resolving
     it. For a different candidate value and an active record use FLAG. A recollection
     that the team had agreed otherwise is not a new decision to switch. Explicit
     resolution in favour of the active value is KEEP; adoption of a different value
     is SUPERSEDE. Before any active value, a settled commitment uses ADD-active.
  - Active X, proposed Z: 'Let's make Y our choice from now on.' -> SUPERSEDE Y,
    targeting X; retain X as the previous active version, and do not adopt proposed Z.
  - 'We chose X for classification. Maybe Y for tagging?' -> the Y/tagging candidate
    is a proposal; the X/classification decision does not confirm it.
  ```

  The first line is added so that the rules can be applied with Mem0's operations.
  Every other line is copied verbatim from `INTENT_GUIDE` in
  [`resolver.py`](../../src/tracemem/resolver.py): item 1, the first four sentences
  of item 2, item 4 and two of the guide's contrast examples. They carry four
  rules: a suggestion is not a decision (items 1 and 2); a dispute stays open
  (item 4); a statement about another item never replaces this one (item 1's "Do
  not transfer…" and the tagging example); a replaced decision is kept (the
  example that retains X as the previous active version). No code enforces them. The
  update model alone applies them, and the adapter validates and applies its
  actions exactly as for `mem0-classic`.
- **One answer prompt, client and validator.** Every system answers through
  `SharedAnswerer` with the same `ANSWER_PROMPT`, output schema, model settings,
  answer validation, retry limit and byte budget, and with one model client per
  scenario from `make_client()` ([decision 0012](0012-cache-and-cap-model-calls.md)).
  A system with a write path uses the same client and settings for its write calls.
  The prompt adds one paragraph (`ANSWER_CONVENTIONS`) for the conventions of
  [benchmark section 5](../benchmark.md#5-labelling-conventions-for-hard-cases)
  that decide answers, in the parts it did not already state: a turn that puts a
  value forward is a suggestion, and one that only names a value is a mention; a
  dispute stays open until someone states a value as final or the other side
  agrees; on a decision, a turn that adopts the value of an earlier open
  suggestion accepts it, even when it gives reasons of its own, and the
  suggestion's turn is part of the evidence; a task's progress changes when
  someone announces the change. Since 26 Oct (task A7) the prompt also says that
  a question about the previous value is answered *none* when the evidence shows
  no earlier settled value, rather than abstaining. With both, `answer_prompt_hash`
  begins `01b75f6fb20f`.
- **Manifests.** Each run records its retriever settings, whether its lines quote
  source turns and, for the Mem0 systems, the hashes of the update prompt and of
  the rules; `instructions_hash` begins `33757c0e88e5` for these rules and is
  `null` for `mem0-classic`.
  [The comparison guide](../memory-comparison.md#shared-retriever-and-answer-conventions)
  lists the fields. `tracemem report` refuses to compare runs whose shared
  settings differ.

## Consequences

The five systems now differ only in the write path, the store, the retriever's
two settings and the quote; the model, client, answer prompt, validator and byte
budget are shared. The similarity systems make no write calls, so they report
zero write usage and have no operations to score. Mem0's native actions stay in
`memory_events.jsonl`, as in decision 0004. A change to the retriever settings,
the quote or the rules changes requests, so the affected systems must be rerun; a
change to the answer prompt means rerunning all of them.

Four limits applied when this record was proposed; the first and the last are now resolved:

- On every development scenario in the repository, the default budget holds all
  of a similarity system's records: the largest store, pilot-01's, takes 1,153
  bytes. The retriever then drops nothing, and because the selection is shown in
  time order, its ranking has no effect. `similarity` and `similarity-recency`
  select the same records and send identical requests, so on these scenarios they
  are one system, and RQ1's comparisons against the two baselines are comparisons
  against the same system. The weight and half-life matter only once a store is
  larger than the budget. Resolved by question 4: with `TRACEMEM_CONTEXT_TOP_K=4`
  each system shows the four records closest to the question, so the two
  similarity systems differ.
- The similarity systems read the speaker's own words; the other three read stored
  values and statuses, or Mem0's memory text, which may or may not keep the quote.
  A difference between them may therefore come from the quote rather than from the
  memory design.
- The rules leave out the last four sentences of `INTENT_GUIDE` item 2, and items
  3 and 5, so `mem0-instructions` is not given TraceMem's definition of a decision
  (item 3).
- Resolved on 26 Oct (task A7), when the paragraph gained the rule. Until then,
  the conventions paragraph left out benchmark section 5's rule that, on a
  decision, a turn adopting the value of an open suggestion accepts it, even when
  it gives reasons of its own, and that only an acceptance cites the suggestion's
  turn as evidence. The similarity systems cannot get that link from their
  records. In pilot-01, `model.sentiment@S3` ("Which model are we using for the
  sentiment classifier?", after session 3) needs both S2-T3 ("Maybe we could try
  DistilBERT?") and S3-T2 ("Then we switch the sentiment classifier to DistilBERT,
  since BERT misses the latency limit.") as support, but the record for S3-T2
  has only its own turn as source; TraceMem's records can carry the earlier turn
  as a source. Adding the rule changes `answer_prompt_hash` and means rerunning
  all five systems.

This record does not cover the planned Timeline and full-history systems or the
end-to-end version of any system, listed in
[the interfaces guide](../interfaces.md#comparison-systems-planned), nor
production extraction or Mem0 2.x. Its set of systems also differs from the list
the [README](../../README.md#how-this-differs-from-the-proposal-pending-team-ratification)
gives as pending team ratification. This record adds the two Mem0 systems, and it
has no TraceMem without supersession, the README's ablation, whose resolver may
only add records; the registered ablation, `tracemem-no-versions`, keeps
supersession and discards closed versions. Commands and details are in
[the comparison guide](../memory-comparison.md). The retrieval, resolver and
evaluation owners should review this record before ratification.

Open questions for the team. The systems run on the choices above until the team
decides:

1. **Which Mem0.** `mem0-classic` is the native `mem0ai` 1.0.11 SDK behind
   decision 0004's adapter, not a re-implementation of the Mem0 paper's algorithm
   in this repository, which the team's plan had assumed. A later run with Mem0's
   own extraction could build on the same adapter.
2. **Whether systems receive the item keys.** Runs use the CLI's default,
   `--vocabulary keys`, a choice the
   [working agreement](../working-agreement.md#1-decisions-live-in-decision-records)
   leaves to the team. Under `gold_candidates` none of the five systems reads that
   list: the item keys reach them through the candidates and appear in every
   context line. The choice matters for runs with a real extractor.
3. **Who sees quoted turns.** The options are quotes for the similarity systems
   only, as now, for every system, or for none.
   [The interfaces guide](../interfaces.md#systems-without-a-resolver) describes
   every record-based line as quoting its creating turn, while decision 0004's
   systems leave the quote out.
4. **How retrieval should matter.** The options are: every system retrieves a
   fixed number of the records closest to the question (by similarity for all,
   with recency added for `similarity-recency`), tuned on development scenarios; a
   smaller byte budget for every system; or one similarity system fewer in the
   reported comparison. The team's plan describes all five systems as reading the
   records closest to the question, while the Mem0 and TraceMem systems here read
   newest first. The choice should come before any tuning; until then the weight
   0.3 and the 7-day half-life stay provisional.
   **Settled on 26 Oct by member A, for the team to accept: the first option**,
   with `k` chosen by the 90% rule (see "A fixed number of records per answer"
   above). The reason: at the default budget both similarity systems send
   identical requests on every development scenario, while a smaller budget
   with newest-first selection decides which systems look good (in a one-run
   diagnostic at 600 bytes, both Mem0 systems lost about a quarter of their
   current accuracy and TraceMem gained). With every system taking the records
   closest to the question, no system is cut by a different rule.
5. **The rules' text.** Whether to keep the added first line and this choice of
   passages, to copy item 2 whole, or to add items 3 and 5. Any change alters
   `instructions_hash` and the answers of `mem0-instructions`.
6. **Which systems are reported.** The options are this record's five, with
   `tracemem-no-versions` as a diagnostic outside them; the same five and that
   ablation, as decision 0004 compares it; or the README's list, which has no Mem0
   system and adds Timeline, full history and TraceMem without supersession. The
   README and [the interfaces guide](../interfaces.md#comparison-systems-planned)
   should then list the set the team chooses.
   **Settled on 26 Oct by member A, for the team to accept: the first option**,
   this record's five, with `tracemem-no-versions` as a diagnostic outside them.
   The reason: the five answer the project's question, whether a memory that
   tracks each decision's status beats memories that find similar statements or
   let a model add, update and delete facts. The ablation answers a different
   question, which part of TraceMem matters, and only the history questions can
   separate it from TraceMem, so it is reported beside the five. The README and
   the interfaces guide now list this set;
   [the comparison guide](../memory-comparison.md#questions-about-the-systems)
   explains it in plain words.
