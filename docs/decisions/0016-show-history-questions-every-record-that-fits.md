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
- **When every record fits, similarity and similarity + recency show the same context for a question about the past.** The two systems store the same records and differ only in how they rank them. When all of those records fit the 12,000-byte budget, each system shows all of them in time order, so the ranking chooses nothing: the two requests are identical, and the recency term has no effect on those questions. On the 13 development scenarios this holds for every question about the past, because the budget never left a record out of any of them (see "The budget can still cut the earlier record" above); rebuilt without model calls, the requests of the two systems are identical for all 30 of them. The gap between the two systems on questions about the past in the check on Haiku below (1.000 for similarity, 0.933 for similarity + recency) therefore comes from the replies to identical requests, not from ranking. Questions about now still separate the two systems, because each keeps the 4 records its own ranking puts first. For a question about the past, the recency term matters again only when the budget cuts records, as it may in a longer scenario. A later review of pull request #6 raised this limit.
- **Showing every stored record does not prove that nothing was lost when memories were written.** When a question's context ends without the line "k of N records shown", the answering model saw every record the system could have shown for that question. A wrong none on such a question therefore did not come from records cut when answering. It can still come from writing: a value the system never stored, or stored and later overwrote, is not among those records, and this change does not alter how any system writes. Mem0 is the clear case (see "Mem0 is expected to gain little" below). TraceMem without versions is another: it keeps no replaced records, so its earlier record was missing on 20 of 22 questions in the check on Haiku. A later review of pull request #6 raised this limit.
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

The check ran on 27 Oct 2026 from 17:43:58 to 17:53:36 SGT. All six systems answered the 13 development scenarios on Claude Haiku 5.5 at the `freeze-deck` settings, with the code of commit `bcb34a4`. A copy of the A7 run's saved replies was reused, so unchanged requests were not paid for again; the check cost US$0.23. The comparison is the A7 run of 27 Oct, 00:01 to 00:17 SGT (code `d26cd50`), one run each.

| System | Questions about now (140), A7 / check | Questions about the past (30), A7 / check | Earlier record left out (22), A7 / check |
|---|---|---|---|
| similarity | 0.957 / 0.964 | 0.867 / 1.000 | 0 / 0 |
| similarity-recency | 0.936 / 0.936 | 0.500 / 0.933 | 13 / 0 |
| tracemem-controlled | 0.986 / 0.986 | 1.000 / 1.000 | 0 / 0 |
| mem0-classic | 0.814 / 0.814 | 0.733 / 0.733 | 0 / 0 |
| mem0-instructions | 0.750 / 0.750 | 0.600 / 0.767 | 1 / 0 |
| tracemem-no-versions | not run in A7 / 0.993 | not run in A7 / 0.233 | not run in A7 / 20 |

- Similarity + recency gains the most. Its earlier record is no longer left out (13 of 22 questions before, none now), and its score on questions about the past rises from 0.500 to 0.933. On two questions whose answer is an open dispute (dev-02 `model.backbone` as of S3, pilot-02 `dataset.train` as of S2), it now names one side instead of answering none or abstaining.
- Similarity rises from 0.867 to 1.000 on questions about the past: four "as of" questions that it had answered with none or an abstention are now right.
- Mem0 + instructions rises from 0.600 to 0.767. Mem0 stays at 0.733: two answers improve, and two get worse (an answer with extra words, "fine-tuned BERT", and the value of a similar item, "LDA" for a metric).
- TraceMem stays at 1.000.
- TraceMem without versions keeps no replaced records, so its earlier record is missing by design (20 of 22), not because of the budget.
- Answers about now are unchanged for every system except one: similarity's answer to dev-01 `task.weather_join` after S1 went from none to the right "open". Its request was identical to A7's. The saved reply it received had been written by similarity + recency, which sent the same request at the same time in the A7 run, so this change comes from the reply cache, not from this record. It also shows that Haiku can answer an identical request in two ways.
- The line "k of N records shown" never appeared: no history question in the development scenarios had a record cut by the budget. The rule to abstain instead of answering none is therefore tested only by the unit tests.
- One run on 13 scenarios gives no interval. These numbers show that the change works as intended on the development scenarios, not how large its effect will be on unseen scenarios.

## Consequences

- On these scenarios, the limit of 4 records no longer hides an earlier decision from a question about the past.
- Requests for questions about the past are longer, so each such question costs a little more.
- The deck's results remain those of `freeze-deck`. Runs made before this change cannot be reported beside runs made after it.
- The team should revisit this record if the line appears often on the report's scenarios, or if the systems abstain much more often on questions about the past whose answer is none.
