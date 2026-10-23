---
id: 5
title: Distinguish reopening proposals from settled task transitions
status: proposed
date: 2026-10-19
decided_by: []
supersedes: []
superseded_by: []
---

# 0005. Distinguish reopening proposals from settled task transitions

## Context

Development logs contain two separate semantic failures. A Resolver treats a
question about reopening as an adopted replacement of cancellation. A shared
answerer treats a settled cancellation and a proposed reopening as a conflict.
Both replies satisfy their structural contracts, so storage and schema validation
cannot establish whether their interpretation is correct.

## Decision

- Ask the Resolver to identify the current clause that actually adopts or reports
  a transition. A changed value, available capacity or an old open version does not
  authorize reopening. An explicit challenge to the recorded cancellation is a
  dispute; reporting that work has restarted after cancellation is a new update.
- Give all three comparison arms the same read policy: for current questions,
  proposed values do not override or dispute an active value; relevant contested
  evidence does. Task value and record status remain distinct. Historical questions
  use retained evidence at the requested time. Missing context is not reconstructed.
- Interpret native Mem0 text and events without inventing TraceMem status labels.
  Keep the reader, byte budget, model configuration and public contracts unchanged.
  Preserve one normal model call and the existing private output schemas.
- Record both changed prompt fingerprints and increment the Resolver intent-policy
  version. Keep the original failures as offline fixtures and explicitly separate
  scripted state/answer checks from evidence of live model improvement.

## Consequences

This clarifies how the existing operations and statuses should be interpreted. It
adds neither keyword classification nor automatic semantic validation, and a legal
but wrong model reply can still pass. Real development reruns are needed to measure
improvement and regressions. Changing both write and read prompts also means a
future before/after score cannot isolate the Resolver's causal contribution alone.

This is an implemented development policy proposed for Resolver and answerer-owner
review. It does not claim team ratification or change the four public contract files.
