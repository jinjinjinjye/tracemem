---
id: 10
title: Validate visible answer evidence and restore historical state
status: proposed
date: 2026-10-19
decided_by: []
supersedes: []
superseded_by: []
---

# 0010. Validate visible answer evidence and restore historical state

## Context

The development rerun after decision 0009 retained the DistilBERT and macro-F1
adoption relationships, but later DistilBERT and current accuracy answers still
omitted their visible linked origins. A historical training-dataset question was
also answered as settled. The final record marked the old claim declined without
a closure time, so that projection could not establish its earlier contested
state. More prompt instructions alone had not enforced either requirement.

## Decision

- Add conservative evidence checks to the shared answerer after structural
  validation. Infer scope only when the answer value exactly matches a unique
  active record in the supplied context. For current/as-of answers, reject a
  definite answer when the matched item has visible unresolved contested evidence;
  exclude records created after an as-of boundary.
- For a current settled answer, require its creating decision and a visible older
  superseded same-item/same-value origin when the origin's creating turn appears
  in both its own sources and the active record's sources. The active creating turn
  must likewise appear in its sources. These links establish provenance, not proof
  that the earlier record was a proposal. Do not infer roles from a source ID alone,
  an open proposal, hidden edges or omitted records. Compare the numeric positions
  of displayed creating turns, not unrendered timestamps, to establish earlier;
  skip unparseable positions. Clarify in the shared prompt that both roles matter
  at the first current checkpoint after adoption and after later KEEP confirmations.
- Select context once for both rendering and validation. Use only those records;
  keep the common UTF-8 byte budget, renderer, four-field output schema, model
  settings and `max_attempts`. Give bounded feedback and require a complete new
  model reply. Never add citations or compute a replacement answer silently.
  Exhausted attempts return abstain and retain all attempted usage.
- For versioned as-of reads, use the public requested session and the system's own
  observed operation log with the existing `OpLog.upto` method. Project through the
  last observed turn in that exact session before applying the common budget.
  Return empty context for invalid or unobserved versioned boundaries. Do not
  filter by gold item, question ID or expected state. Current and previous reads
  retain their existing memory view.
- Do not replay the current-only store's scoring audit. Keep Mem0's native memory
  and history as evidence, without fabricated TraceMem statuses. All three arms
  share the same validation code and reader settings; native text remains subject
  to model interpretation where explicit-status checks cannot apply.
- Record the answer-validation policy hash, updated reader policy and temporal
  read policy in comparison manifests. Preserve earlier run artifacts and records.
  This repair does not change Resolver logic or its prompt, schemas or public contracts.
  Capture the real dev failures and test correction, exhaustion, time boundaries,
  budget omissions and retained control cases offline before another paid run.

## Consequences

This is a bounded semantic guard, not a general answer verifier. Exact-value
matching can miss paraphrases and deliberately skips duplicate active values.
It does not prove that the model identified the question's item, validate all
native text or previous-value semantics, enforce minimal citations, or recover
content excluded by storage or budget. A superseded origin's former intent is
unknown. Native event names are storage operations, not decision-status labels.

The implementation uses only visible evidence to reject unsupported output and
allows abstention when correction fails. Source feedback contains at most 12 IDs,
each at most 64 characters long. Oversized IDs are omitted whole rather than
shortened into new source IDs. Full validation remains in force, so incomplete
feedback can make recovery harder. Answer costs and abstentions can increase within the same
configured attempt limit. A lower false-certainty rate caused only by abstention
must not be reported as increased answer accuracy.

Historical projection exposes state already retained in TraceMem's operation log;
it does not restore missing history for the ablation or give any arm benchmark
labels. Read-time changes still alter the experimental method. The next real
development comparison must report write and reader results separately, including
answer retries/exhaustion, citation completeness, historical accuracy and costs.
Offline replay proves enforcement and preserved integration, not live compliance.

The shared `answer_prompt_hash` changes; the output schema and Resolver fingerprints
stay fixed. `answer_validation_policy_hash`, `reader` and `temporal_read_policy`
record the new executable behavior. This is an implemented development proposal, not team ratification
or a rewrite of earlier proposed or accepted decisions.
