---
id: 7
title: Preserve adoption sources and complete historical answer evidence
status: proposed
date: 2026-10-19
decided_by: []
supersedes: []
superseded_by: []
---

# 0007. Preserve adoption sources and complete historical answer evidence

## Context

The development rerun after decision 0006 restored initial selections and the
versioned replacement chain. It still accepted selected proposals without citing
their origins, returned a correct previous value without its replacement evidence,
and in the current-only arm treated a criticism plus a switching question as a
dispute. These are distinct write-provenance, read-citation and intent errors.

## Decision

- Validate adopted-target provenance in the Resolver. `ADD-active`/`SUPERSEDE`
  must cite all candidate sources and the creating turn of each selected proposed
  or contested target. Include visible same-item/project creation metadata in the
  allowed sources. Use bounded rejection feedback and the existing attempt limit;
  never silently complete sources or fabricate a write after exhaustion.
- Preserve ordinary revisions and optional-target semantics. Do not require every
  active predecessor source, accumulated support or unselected proposal. The model
  still determines whether a proposal is adopted.
- Clarify that criticism of suitability plus a question about switching remains
  a proposal. A dispute asserts a competing settled fact; an affirmative new
  selection can establish adoption. Preserve the earlier decision/reopening rules.
- Use one historical citation guide in all three answer arms. Previous answers
  need the earlier settled choice and its replacement evidence; as-of answers use
  evidence by the requested time. Cite only retained context, without reconstructing
  missing history or using a later reaffirmation as replacement evidence. Keep the
  renderer, context budget, schemas, model settings and public contracts unchanged.
- Save development failures and verify rejected/corrected/exhausted source paths,
  suggestion/dispute controls, partial/complete historical answers and the existing
  formal-selection, replacement/history and reopening regressions offline.

## Consequences

Missing sources on selected adoption targets now cause deterministic rejection.
If the model omits an otherwise optional target, interpretation is still needed;
this guard cannot infer every acceptance. Intent and answer-citation completeness
remain model policies, not keyword classifiers or semantic validators. Scripted
offline tests do not establish improved live behavior, and saved runs are not
repaired in place.

Both Resolver prompt/policy and shared answer-prompt fingerprints change. A new
three-arm rerun must report write and read results separately; Mem0 also receives
the shared reader change. Whole-run differences are not a Resolver-only effect.
This implemented development policy remains proposed for component-owner review,
without claiming team ratification or superseding accepted decisions.
