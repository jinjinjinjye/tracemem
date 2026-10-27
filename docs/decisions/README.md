# Decision records

A decision that affects more than one person lives here as a numbered file, `NNNN-short-slug.md`. The rules are in the [working agreement, section 1](../working-agreement.md#1-decisions-live-in-decision-records); this page is the how-to.

## Writing a record

1. Copy [`0000-template.md`](0000-template.md) to the next free number, for example `0007-store-an-operation-log.md`.
2. Fill in the front matter and the three sections. Keep the decision itself to a few sentences a teammate can act on.
3. Open a pull request with the record at `status: proposed`.
4. When the people listed in the working agreement for that kind of decision approve the pull request, set `status: accepted`, fill in `decided_by`, and merge.

## Replacing a record

Never rewrite the substance of an accepted record. In one pull request:

1. Write the new record with the old id in `supersedes`, and set it to `accepted` once approved.
2. In the old record, set `status: superseded` and add the new id to `superseded_by`.

`python scripts/check_decisions.py` runs in CI and fails when a link goes only one way, when a superseded record has no successor, or when an accepted record does not name who decided it.

## Index

| Id | Title | Status |
|---|---|---|
| 0001 | [Adopt the working agreement](0001-adopt-the-working-agreement.md) | proposed |
| 0002 | [Record resolver failures](0002-record-resolver-failures.md) | proposed |
| 0003 | [Score resolver operations against all gold candidates](0003-score-resolver-operations.md) | proposed |
| 0004 | [Compare controlled TraceMem, current-only memory and classic Mem0](0004-compare-controlled-memory.md) | proposed |
| 0005 | [Distinguish reopening proposals from settled task transitions](0005-interpret-task-reopening.md) | proposed |
| 0006 | [Recognize affirmative selections without extra confirmation](0006-recognize-affirmative-selections.md) | proposed |
| 0007 | [Preserve adoption sources and complete historical answer evidence](0007-preserve-adoption-and-history-evidence.md) | proposed |
| 0008 | [Constrain adoption sources and check answer evidence roles](0008-constrain-adoption-and-answer-evidence.md) | proposed |
| 0009 | [Preserve adoption during source retries and prioritise unresolved disputes](0009-preserve-adoption-during-source-retries.md) | proposed |
| 0010 | [Validate visible answer evidence and restore historical state](0010-validate-reader-evidence-and-historical-state.md) | proposed |
| 0011 | [Compare five memory systems through one retriever and one answer prompt](0011-compare-five-memory-systems.md) | proposed |
| 0012 | [Call local and paid models through one client with a reply cache and a spending cap](0012-cache-and-cap-model-calls.md) | proposed |
| 0013 | [Embed records with nomic-embed-text on the local model server](0013-embed-with-nomic-embed-text.md) | proposed |
| 0014 | [Freeze the deck as freeze-deck and keep tuning on development scenarios until freeze-v1](0014-freeze-the-deck-and-keep-tuning-for-the-report.md) | proposed |
| 0015 | [Report a second score that accepts extra words around the value, beside the strict score](0015-report-a-second-score-for-extra-words.md) | proposed |
| 0016 | [Show a question about the past every record that fits, and say when records are left out](0016-show-history-questions-every-record-that-fits.md) | proposed |
