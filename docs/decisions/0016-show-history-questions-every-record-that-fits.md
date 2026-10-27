---
id: 16
title: Show a question about the past every record that fits, and say when records are left out
status: proposed
date: 2026-10-27
decided_by: []
supersedes: []
superseded_by: []
---

# 0016. Show a question about the past every record that fits, and say when records are left out

## Context

Each system shows the answering model the 4 records closest to the question (`TRACEMEM_CONTEXT_TOP_K=4`, [record 0011](0011-compare-five-memory-systems.md), question 4), within a budget of 12,000 bytes. Two kinds of question ask about the past. A `previous` question asks which value the team used before the current one. An `as_of` question asks what was settled at the end of a given meeting. For these questions, the record of the earlier decision can rank fifth or lower, and then the answering model never sees it. Since commit `0b74647`, the answer prompt tells the model to answer none when a question about the past shows no earlier settled value. A record cut off by the limit of 4 therefore turns into a confident wrong none.

A review of pull request #6 raised this problem as its finding 1. We counted it on the A7 run on Claude Haiku: 13 development scenarios, the deck's frozen settings, one run per system. Each system had 22 questions whose answer is an earlier value. Similarity + recency lost the earlier record on 13 of them: it answered none on 7, abstained on 5 and gave a value on 1. Mem0 + instructions lost the earlier record once. Similarity, TraceMem and Mem0 never lost it.

## Decision

The same rule applies to all five systems and to TraceMem without its history. It does not use the item a question is about, because no system is given that item.

1. **A question about the past is not limited to 4 records.** A `previous` or `as_of` question is shown every record that fits the 12,000-byte budget. When they do not all fit, the system keeps the records closest to the question first, by its own ranking; similarity + recency therefore keeps its recency term. The records are shown in time order, as before.
2. **When the budget still leaves records out, the context says so.** The context of such a question then ends with one more line, for example "8 of 11 records shown; 3 left out to fit the context budget." The second number counts every record the system could have shown for that question. The line is not a record: it does not count against the budget, and it cannot be cited.
3. **With that line, the question gets a rule of its own.** The request for that question also carries this rule: "Records were left out of this context, as its last line says, so the settled value this previous/as_of question asks about may exist without being shown. Answer none only when nothing was left out: here, if the context does not show that value, abstain instead of answering none." When nothing was left out, the request carries no rule. The shared answer prompt already lets the model answer none in that case.
4. **A question about the present does not change.** Its request is byte for byte the request the frozen code sent. Its answers and the saved replies of earlier runs therefore stay valid. The line and the rule never enter the shared answer prompt, which every question receives.
5. **Each run records the rule.** Each run's manifest records `history_context_policy` and `history_rule_hash` under `comparison`. A run made before this change has neither key, so `tracemem report` refuses to show it beside a run made after the change.

The way systems write memories does not change: neither TraceMem's resolver nor Mem0's updates. The change is in `SharedAnswerer.answer` in `src/tracemem/systems/comparison.py`. Its tests are in `tests/test_history_context.py`.

## Limits of the change

- **The rule does not know the item.** A system receives a question's text and kind but not its item. The similarity systems also store raw turns without item labels. The rule therefore shows every record that fits the budget, not every record of the item asked about.
- **The budget can still cut the earlier record.** That can happen in a scenario longer than the development scenarios, such as one of the report's 20 test scenarios, which nobody who tunes has seen. Points 2 and 3 exist for that case. On the 13 development scenarios the budget never cut a question about the past: none of the 150 requests of the five systems for such questions carried the line. A check on these scenarios therefore tests point 1 only. Only the unit tests cover points 2 and 3.
- **Mem0 is expected to gain little.** Mem0 never lost the earlier record on the development scenarios, so there was nothing for it to recover. Its questions about the past do now see more records. The reason is that the shared reader receives Mem0's current memories and every event in Mem0's native history, and a question about the past is no longer limited to 4 of them. But showing more records cannot bring back a value that Mem0's own updates did not keep. Mem0 is not treated differently from the other systems.
- **The change mostly concerns a baseline.** The lost records were almost all in similarity + recency. The change is therefore about fairness to the systems TraceMem is compared with, not about TraceMem itself. It changes how the baselines score on questions about the past.
- **The change was made after the deck freeze and judged on development scenarios only.** It came after the tag `freeze-deck`, under [record 0014](0014-freeze-the-deck-and-keep-tuning-for-the-report.md) item 2, which allows prompts and settings to change until `freeze-v1` when only development scenarios judge them. The deck's test results did not drive this change (record 0014 item 4), and this change does not alter them.

## Request check, without model calls

We built every answer request of the five systems on the 13 development scenarios twice: once with the code before the change and once with the code after it. Writes were replayed from the saved replies of the A7 run on Claude Haiku, so both versions answered from the same memories. No model was called.

| System | Questions about the present: request unchanged | Questions about the past: request changed |
|---|---|---|
| Similarity | 140 of 140 | 30 of 30 |
| Similarity + recency | 140 of 140 | 30 of 30 |
| Mem0 | 140 of 140 | 30 of 30 |
| Mem0 + instructions | 140 of 140 | 30 of 30 |
| TraceMem | 140 of 140 | 21 of 30 |

Every request that changed now shows more records. TraceMem's other 9 questions about the past already had 4 records or fewer, so their requests did not change. On average, a changed request grew by about 890 characters for the two similarity systems, about 2,800 for Mem0, about 2,700 for Mem0 + instructions and about 290 for TraceMem.

## Check on Haiku

To follow. All six systems are to be run on the 13 development scenarios with Claude Haiku, reusing the A7 run's saved replies so that only the changed requests are paid for. The results will be added here.

## Consequences

- On these scenarios, the limit of 4 records no longer hides an earlier decision from a question about the past.
- Requests for questions about the past are longer, so each such question costs a little more.
- The deck's results remain those of `freeze-deck`. Runs made before this change cannot be reported beside runs made after it.
- The team should revisit this record if the line appears often on the report's scenarios, or if the systems abstain much more often on questions about the past whose answer is none.
