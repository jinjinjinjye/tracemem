---
id: 14
title: Freeze the deck as freeze-deck and keep tuning on development scenarios until freeze-v1
status: proposed
date: 2026-10-25
decided_by: []
supersedes: []
superseded_by: []
---

# 0014. Freeze the deck as freeze-deck and keep tuning on development scenarios until freeze-v1

## Context

The team plan has two freezes. The deck's prompts are frozen on Mon 26 Oct, and its 20 test scenarios are then opened, converted and run for the presentation on Thu 29 Oct. Work then continues until the final freeze, `freeze-v1`, on Wed 4 Nov, which precedes the report's own 20 test scenarios. Four written rules do not allow that sequence:

- `tracemem run --split test` refuses to run unless a tag matching `freeze-*` is reachable from the commit (`src/tracemem/cli.py`), so a tag named `deck-freeze` would not unlock the deck's test run.
- `AGENTS.md` hard rule 2 forbids changing prompts or settings after a `freeze-*` tag without a decision record that says so, and the [working agreement](../working-agreement.md) adds that such a change invalidates earlier test results.
- [`docs/benchmark.md`](../benchmark.md) section 10 says that people who tune any compared system never open or review a test scenario, yet the person who tunes is the one who opens and converts the deck's 20.
- `AGENTS.md` hard rule 1 forbids an AI assistant to open, read, summarise or tune on test scenarios, which rules out help with the conversion.

## Decision

**The deck freeze is the tag `freeze-deck`, and tuning may continue on development scenarios after it, up to `freeze-v1`, on the conditions below.** This record is the record that `AGENTS.md` hard rule 2 asks for, and it covers that window only.

1. **Tag.** The team tags the commit that produces the deck's results `freeze-deck`, before anyone who tunes opens a deck test scenario.
2. **Tuning after the tag.** Between `freeze-deck` and `freeze-v1`, prompts and settings may change, and only development scenarios may be used to judge the changes. After `freeze-v1` nothing changes without a new record.
3. **The deck's results.** They are the results of the `freeze-deck` commit, are reported for the deck only, and are never combined with results from later commits.
4. **The deck's test scenarios are spent once opened.** They are never used to tune, never counted in the report's test results, and may appear in the report only as the deck's earlier, separately labelled result.
5. **The report's test scenarios.** Nobody who tunes opens them before `freeze-v1`, as section 10 requires.
6. **Converting a test set.** After the matching freeze tag, and only then, the person who tunes may convert that set from plain English to the scenario format, with an AI assistant's help if the person instructs it; this is an exception to `AGENTS.md` hard rule 1 for conversion only. Each converted file must pass `tracemem validate`, and its `tracemem replay` answers must match the author's own answers; any difference is settled with the author before the run. Conversion changes no prompt or setting.

## Consequences

The deck's test run can go ahead on Tue 27 Oct, and the work of the following week can still improve the systems. The cost is that the deck and the report rest on different prompt versions, so their numbers must be presented separately, and that the deck's 20 test scenarios cannot strengthen the report's test set. One follow-up applies once the team accepts this record: `AGENTS.md` hard rules 1 and 2 should point to it. The team page's task for the deck freeze already names the tag `freeze-deck`. Revisit this record if a deck test scenario must be reused, or if the report needs more than its own 20 test scenarios.
