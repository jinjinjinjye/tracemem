---
id: 2
title: Record resolver failures and usage without changing memory
status: proposed
date: 2026-10-18
decided_by: []
supersedes: []
superseded_by: []
---

# 0002. Record resolver failures and usage without changing memory

## Context

The model-backed Resolver can fail before producing an Operation. The existing
storage rejection path covers only operations that were produced but violate
OpLog rules. Integration needs to preserve this distinction, retain model usage
including retries, and prevent failed evaluations from being presented as complete.
This record proposes the conventions implemented by the Resolver integration;
team ratification is still pending.

## Decision

- Exhausted model attempts raise ResolverError. The pipeline records a generation
  failure, performs no memory write, and proceeds to the next candidate. It never
  substitutes KEEP or an invented proposal. Incoming turns remain observed.
- Input-contract, configuration and fatal provider errors abort the run. The CLI
  saves partial diagnostics marked failed and returns a nonzero exit code. Reports
  refuse failed runs. Aborted test-split attempts remain in the test-run audit log,
  with failed status and null accuracy. Unexpected programming errors are not silently recovered.
- Candidate events distinguish applied, storage-rejected, generation-failed and
  aborted outcomes. Existing applied/rejected operation artifacts retain their format.
- Optional pipeline hooks supply event snapshots and resolver-only usage totals.
  The harness stores per-candidate deltas, final scenario totals and a run sum.
  Calls include retries; tokens count only usage returned by the provider. Missing
  instrumentation is unknown, not a fabricated zero or a billing estimate.
- Resolver configuration and prompt/schema hashes are recorded in the manifest.
  Provider credentials and raw provider error bodies are not logged.
- The registered pipeline-resolver-dev system creates a fresh real Resolver per
  scenario, with gold extraction/matching/retrieval and the rule answerer. It remains
  uses_gold=True and must be labelled a component diagnostic, not a baseline.

## Consequences

Failures cannot silently disappear from evaluation denominators or change a
disputed decision into a confirmed one. A failed run retains useful diagnostics
without qualifying for comparison. Downstream resolver metrics must count failed
candidates explicitly and separate generation failure from storage rejection.

The four shared contract files and the operation meanings remain unchanged.
The optional event hooks and failure-artifact conventions require review by the
pipeline and evaluation owners. See [the resolver guide](../resolver.md) for fields
and commands. Full resolver scoring, caching, Mem0 and end-to-end experiments are
separate work.
