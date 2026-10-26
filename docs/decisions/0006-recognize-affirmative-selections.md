---
id: 6
title: Recognize affirmative selections without extra confirmation
status: proposed
date: 2026-10-19
decided_by: []
supersedes: []
superseded_by: []
---

# 0006. Recognize affirmative selections without extra confirmation

## Context

The development rerun after the reopening repair preserved cancellation when
reopening was only proposed, but also downgraded affirmative initial selections
to proposals. Missing the first active choice propagated into a later replacement:
with only proposals visible, the Resolver could legally add a new active value but
could not record the intended predecessor. Correcting the later operation alone
would invent an active record that had never been created.

## Decision

- Balance the Resolver's final evidence check. An affirmative selection or concrete
  undertaking can itself establish adoption, without another speaker's agreement,
  a special confirmation word or completed execution. Asking whether to adopt,
  considering a choice or conditioning its adoption on approval remains tentative.
- Preserve candidate-specific interpretation, quotation/negation/withdrawal
  boundaries and the reopening distinction from decision 0005. Increment the
  intent-policy version; update the bounded structural-retry instruction too.
- Capture the observed failures and test corrected initial selection, unaccepted
  alternative, replacement and reaffirmation through actual stores. Check sources,
  predecessor links, snapshots and supplied answer context. Preserve a bad-prior-state
  control rather than forcing a fabricated replacement or retrospectively creating
  history. Keep reopening regressions enabled.
- Keep the shared answer policy, model settings, output schemas and public contracts
  unchanged, so the next rollout can examine the write-policy change separately.

## Consequences

This is a prompt-policy correction, not a keyword classifier or semantic validator.
Structurally valid wrong replies can still pass; scripted offline tests establish
request/state contracts and do not prove improved live model interpretation. Saved
incorrect states require a new write rollout, not an in-place repair by this change.
Repeated development evaluation must report new regressions as well as target gains.

This implemented development policy remains proposed for component-owner review;
it does not claim team ratification or supersede an accepted decision.
