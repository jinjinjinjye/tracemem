---
id: 1
title: Adopt the working agreement
status: proposed
date: 2026-09-26
decided_by: []
supersedes: []
superseded_by: []
---

# 0001. Adopt the working agreement

## Context

The project runs for about seven weeks with five or six people building separate components against a shared benchmark, in a public repository. Its own subject is records that go stale without anyone noticing, and a team produces the same failure in its coordination: a changed schema, a benchmark scenario edited after tuning, a decision that stays in a chat thread.

## Decision

The team adopts [`docs/working-agreement.md`](../working-agreement.md) as proposed, or with the edits recorded in this pull request. From acceptance on, decisions that affect more than one person are written as records in this folder.

## Consequences

Cross-component changes take one extra step: a pull request with the affected owners' approval. In return, every current decision can be found in one place with its history, and the benchmark's test split stays trustworthy. The team revisits the agreement at the week-4 check-in.
