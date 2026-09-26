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
