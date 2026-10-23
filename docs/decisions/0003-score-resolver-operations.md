---
id: 3
title: Score resolver operations against all gold candidates
status: proposed
date: 2026-10-18
decided_by: []
supersedes: []
superseded_by: []
---

# 0003. Score resolver operations against all gold candidates

## Context

The pipeline records applied operations, storage rejections and generation failures.
Answer accuracy alone cannot explain whether a Resolver confuses proposals with
decisions, targets the wrong record, or loses required source links. Operation
metrics were planned in the metrics guide; their denominators need to remain stable
when generation fails. This record proposes the implemented scoring conventions.
Team ratification is pending.

## Decision

- Score completed gold-candidate runs only, after each scenario finishes. Match by
  scenario and candidate ID; missing predictions retain their gold denominator,
  and extra predictions cannot improve recall.
- Split ADD into active and proposed labels. Report per-label precision/recall/F1,
  micro F1, macro F1 over defined labels, and confusion by operation and script act.
- Count rejected emitted labels for classification, but require applied operations
  for exact-operation credit. Report rejection and generation-failure rates separately.
- Compare cumulative predicted and gold item states after every candidate. Do not
  restore correct memory before a prediction; upstream errors remain visible.
- Compare targets and source IDs as sets while flagging duplicates. Exact operation
  checks ignore free-text explanations and operation IDs. Exact source equality is
  a strict diagnostic, not a judgment that every additional citation is unsupported.
- Save all scorer rows, an error-only subset and a versioned summary with explicit
  denominators. Report null for undefined rates. A report can be rebuilt without
  rereading scenarios or making model calls.
- Failed runs keep partial execution diagnostics but do not receive complete resolver
  evaluation artifacts. Existing question-level scoring and end-to-end artifacts stay compatible.

## Consequences

Classification, execution validity and cumulative state correctness are separately
visible. A resolver cannot improve recall by duplicating an operation or hide missing
outputs by omitting them from an operation file. Error flags can overlap, and a
correct local operation may inherit an earlier state error.

The four shared contract files stay unchanged. Resolver and evaluation owners should
review these conventions before ratification. Extraction metrics, teacher-forced
evaluation, operation-level confidence intervals and Mem0 comparison remain separate work.
Definitions and commands are in [the metrics guide](../metrics.md#9-resolver-operation-metrics-and-error-analysis).
