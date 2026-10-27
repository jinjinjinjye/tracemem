# Development run A5: every answer, with the gold answer and the automatic score

**These are development results, not the experiment's findings.** They come from the five pilot scenarios, which the team reads and tunes on, and from a small local model; the reported results come from test scenarios after the freeze ([`docs/benchmark.md`](../../docs/benchmark.md) section 10). This folder holds every answer from the first run (task A5), so that teammates can audit answers and tell model errors from scoring errors.

## What was run

All five systems ran on the 5 example scenarios that came with the starter code (pilot-01 to pilot-05), three times each (`repeat` r1, r2 and r3, each started from an empty reply cache). The model was Qwen 3.5 4B, run locally. Each system received the correct memories directly (the correct-memories condition, `gold_candidates`). All runs used the code at commit `f298722` on the branch `overnight/build-on-pr4`.

That gives 795 rows: 5 systems × 3 repeats × 53 questions (46 about the present, 7 about the past). Similarity + recency sent exactly the same requests as similarity in every run, so its rows repeat similarity's.

## Files

- `a5-answers.csv`: one row per answer. List fields are joined with "; ".
- `a5-answers.json`: the same rows, with lists kept as lists.
- `table.md`: the summary table, the mean over the three repeats with the lowest and highest.
- `run-records/r1` to `run-records/r3`: each run's `manifest.json` (exact settings, code commit, scenario fingerprints) and `metrics.json` (every rate the scorer computes). The full run folders are not committed: `runs/` is ignored, as the [working agreement](../../docs/working-agreement.md) section 4 sets out, and these two files are the record a reader needs.

## Columns

| Column | Meaning |
|---|---|
| `repeat`, `run_id`, `system`, `model`, `condition`, `commit` | which run produced the answer |
| `scenario_id`, `category` | which scenario, and the pattern it is built around |
| `question_id`, `kind`, `asked_after`, `about_session` | the question's id; whether it asks about now (`current`), the previous value (`previous`) or the state at an earlier meeting (`as_of`); the meeting after which it is asked; and, for `as_of`, the meeting it asks about |
| `item`, `question_text` | what is asked about, and the question the system received |
| `gold_status`, `gold_value` | the correct answer: `answer` with a value, `none` (nothing settled), or `conflict` (the team disagrees) |
| `gold_accepted_spellings` | spellings that count as correct |
| `gold_replaced_values`, `gold_unconfirmed_values`, `gold_other_item_values` | values that would be wrong in a specific way: replaced, only suggested or disputed, or belonging to a similar item |
| `gold_required_support` | the turns a fully supported answer should cite |
| `trap_newer_record`, `trap_newer_mention`, `trap_similar_item` | whether the question is one of the three kinds of trap question |
| `answer_status`, `answer_value`, `answer_cited_turns`, `answer_text` | what the system answered, the turns it cited, and its explanation |
| `automatic_score` | the scorer's verdict: one of ten classes, defined in section 3, "Outcome classes", of [`docs/metrics.md`](../../docs/metrics.md) |

## Where the gold answers come from

Nobody wrote them by hand: `tracemem replay` computes them from each scenario's script. The scenario files are in the team repository under `benchmark/scenarios/dev/` (`pilot-01-…yaml` to `pilot-05-…yaml`); each turn's id, such as S2-T3, is meeting 2, line 3.

## Telling model errors from scoring errors

- **A model error:** `answer_status` and `answer_value` are wrong when read against the scenario. Check the answer against the dialogue, not only against `gold_value`.
- **A scoring error:** the answer is right, but `automatic_score` is not `correct`. Common causes: a correct spelling missing from `gold_accepted_spellings`, or a value the scorer put in the wrong class.
- **A gold error:** the dialogue supports a different answer from `gold_value`. That points to the scenario's script, not to the scorer, and is worth reporting too.
