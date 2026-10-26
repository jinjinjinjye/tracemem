---
id: 4
title: Compare controlled TraceMem, current-only memory and classic Mem0
status: proposed
date: 2026-10-18
decided_by: []
supersedes: []
superseded_by: []
---

# 0004. Compare controlled TraceMem, current-only memory and classic Mem0

## Context

Proposal feedback asks what TraceMem adds to Mem0's existing memory updates.
Answer-only comparison against a homegrown imitation, a different model or an
adapter that suppresses native history would not answer that question. Mem0 2.x
also changed the classic update algorithm, so the evaluated version must be named.
This record proposes an implemented development protocol; team ratification is pending.

## Decision

- Register three gold-candidate-only systems with the same candidate input, model
  configuration, all-same-item matching rule, bounded reader and answer prompt.
  Factories receive no gold timeline or question-item labels.
- Use `LLMResolver` with `OpLog` for TraceMem. Its ablation uses the same resolver
  and current-state semantics but discards closed versions and supersession links.
  Audits never become read or matching context.
- Pin Mem0 OSS 1.0.11 and call its native update/storage/history methods. Replace
  extraction with candidate identity, matching with the controlled item filter,
  and provider transport with the shared client. Include native history in reads.
  Document every adaptation and do not label this as latest Mem0 or end-to-end.
- Hash candidates and shared settings in the manifest. Refuse incompatible
  controlled reports even when the ordinary mixed-run override is requested.
- Use question-level metrics across all arms. Keep TraceMem operation metrics for
  the two TraceMem arms, and retain Mem0 native events without forcing its action
  space into TraceMem's labels. Record write and answer usage, including retries.
- Keep each scenario isolated, disable SDK telemetry, validate native batches and
  roll back partial writes. Exercise actual pinned SDK behavior with offline model
  replies, then evaluate real model semantics separately on development scenarios.

## Consequences

The comparison isolates retained memory and decision semantics after extraction.
It does not measure production retrieval, extraction, hosting latency or Mem0 2.x.
The current-only ablation removes version access while retaining proposal/conflict
handling; it cannot be described as removing the resolver or all provenance.
Native Mem0 history remains a capable reference for historical questions.

The optional SDK pin and internal dependency injection require maintenance when
upgrading. CI installs the extra and runs real SDK tests without provider access.
The four shared contract files remain unchanged. Resolver, evaluation and retrieval
owners should review this protocol before ratification. Commands and full
limitations are in [the comparison guide](../memory-comparison.md).
