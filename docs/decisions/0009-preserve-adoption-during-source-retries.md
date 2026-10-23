---
id: 9
title: Preserve adoption during source retries and prioritise unresolved disputes
status: proposed
date: 2026-10-19
decided_by: []
supersedes: []
superseded_by: []
---

# 0009. Preserve adoption during source retries and prioritise unresolved disputes

## Context

The development rerun after decision 0008 rejected extra old sources on DistilBERT
and macro-F1 acceptance in both Resolver arms. Each retry dropped the adopted
proposal target, bypassing the selected-adoption source check. The resulting active
value had incomplete provenance and left its proposal open. The shared reader also
selected IMDB as certain despite visible unresolved competing SST-2 evidence.

## Decision

- After a structurally legal selected adoption fails source validation, preserve
  its operation, add_as and full target set for this candidate's remaining retries.
  Allow target reordering, but reject target loss, additions, substitution and
  operation changes. Correct only sources under the existing exact-source rule.
- Check all operation/target legality before creating the constraint. Cover every
  source-validation failure on legal adoption; do not lock initial illegal targets
  or non-adoption decisions. Keep the original constraint through malformed,
  refused, transient and target-changing replies. Reset it on the next candidate.
- Bound displayed constraint lists, preserving full internal validation. Retain
  the existing retry limit, usage accounting and failure path; exhaustion writes
  nothing and logs generation_failed. Do not silently fix or apply a rejected reply.
- In the shared reader, decide relevant state at the requested time before choosing
  a settled answer or pruning citations. An unresolved contested claim requires
  conflict, even with an active record. A proposal, closed claim or different-item
  dispute does not. Apply the same principle to native memory's retained text.
- Keep model settings, public contracts, schemas, renderer, context budget,
  semantic validation and intent policy v4 unchanged. Preserve formal decisions,
  SVM replacement/history, macro-F1 suggestions and reopening distinctions.
- Capture the four real source-error/target-loss sequences and both reader errors
  as offline fixtures. Test exhausted and corrected retries through both stores,
  with history where available, and preserve semantically wrong but structurally
  valid reader replies as explicit controls.

## Consequences

The retry guard is executable but only protects an adoption already selected in a
structurally legal reply. It cannot prove intent, infer initially omitted targets,
or repair candidate sources. A mistaken first adoption can exhaust the retry budget
instead of changing intent during source repair. Report skipped writes alongside
correctness in the next experiment, not just fewer wrong applied operations.
Truncated feedback can make recovery of a large selected set difficult; validation
still checks the complete set and rejects an incomplete repair.

The reader repair remains a shared prompt change, not runtime semantic validation.
Scripted replies prove request assembly, enforcement and state effects; they do
not prove live compliance. The existing development runs remain unchanged.

Resolver prompt/policy and shared answer-prompt fingerprints change. Both Resolver
arms receive the write guard; all three arms receive the reader prompt. Report
write and read effects separately under the same model/candidate configuration.
This is an implemented development proposal, not team ratification or replacement
of an accepted decision record.
