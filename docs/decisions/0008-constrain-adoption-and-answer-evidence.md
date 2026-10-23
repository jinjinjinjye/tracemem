---
id: 8
title: Constrain adoption sources and check answer evidence roles
status: proposed
date: 2026-10-19
decided_by: []
supersedes: []
superseded_by: []
---

# 0008. Constrain adoption sources and check answer evidence roles

## Context

The development rerun after decision 0007 included the missing proposal origins,
but both Resolver arms also copied old predecessor sources into two acceptances.
The shared reader still omitted replacement evidence for an LR-to-SVM historical
answer and the adopted origin for a DistilBERT current answer, even though the
necessary records were visible. Correct values do not establish complete citations.

## Decision

- For `ADD-active`/`SUPERSEDE` selecting proposed or contested targets, require
  sources to equal candidate sources union selected targets' creating turns.
  Reject missing and extra sources with bounded feedback and the existing retry
  limit. Preserve all candidate sources, even old ones. Do not silently trim,
  append, drop targets or fabricate operations after exhaustion.
- Leave operations without selected adoption under their existing source rules.
  Preserve intent policy v4, including affirmative decisions, criticism followed
  by a switching question, and cancellation followed by a reopening proposal.
- Give all three answer arms the same final evidence-role check. PREVIOUS cites
  both the earlier choice and formal replacement; CURRENT cites the decision
  and a visibly linked origin when retained. Mentioning an ID only in prose is
  insufficient. Exclude sources by their relevance to the question/status,
  preserving both sides where a predecessor or conflict requires them.
- Keep schemas, renderer, budget, model configuration and public contracts fixed.
  Do not infer original status from a closed record, restore missing history from
  source IDs, or access raw dialogue, hidden edges or gold during answering.
- Save the observed development failures and test rejection, correction, retry
  exhaustion and pipeline recovery offline. Retain the earlier formal-decision,
  SVM history, macro-F1 suggestion and reopening regression suites.

## Consequences

Extra-source rejection is executable only when adoption targets are selected.
Determining whether a proposal was adopted remains a model responsibility; an
omitted optional target can remain structurally legal. Candidate-source quality
is assumed, not independently inferred by this guard.

Reader completeness remains a prompt policy under the existing four-field
answer contract and flat, budget-limited context. Offline scripted replies test
request assembly and state effects, not live semantic improvement. Previous runs
are preserved unchanged.

Resolver prompt/policy and shared answer-prompt fingerprints change. Both Resolver
arms receive the write repair, and all three arms receive the reader repair.
Future real-model results must separate write and read effects; whole-run changes
cannot be attributed only to version management or Resolver. This implemented
development proposal does not claim team ratification or supersede an accepted
decision.
