# pilot-05 on Claude Haiku at the deck's frozen settings: every system's memory, model inputs and replies

This folder shows, for the A7 run on Claude Haiku 5.5 at the settings frozen as `freeze-deck`, what each of the five systems held in memory after each meeting of pilot-05, the exact text each system sent to the model, and the model's replies. It was made for task E2 ("Demo: pilot-01 step by step, showing what each system answers after each meeting").

pilot-05 is a mention-after-decision scenario. Similarity, similarity + recency and TraceMem answer all 9 questions correctly. Each Mem0 system has 3 answers scored wrong, and all 3 give the right model with extra words: "logistic regression on TF-IDF features" where the expected value is "logistic regression". The scorer counts such an answer as a different value. Whether it should is an open question for the team; read these 3 as a scoring issue, not a memory error.

## The settings of these runs

The runs are the A7 run of 27 Oct, 00:01 to 00:17: the 13 development scenarios, one run per system, the correct-memories condition (`--condition gold_candidates`), a reply limit of 2,048 tokens, and the answer prompt after the A7 changes (its hash begins `67e86c7f78db`). Each system showed the answering model the 4 memories closest to each question (`TRACEMEM_CONTEXT_TOP_K=4`). These are the settings of the tag `freeze-deck`, so the deck's test runs use the same prompts and settings.

## How these files were made, and why they are exact

The run saved its answers and logs, but not the memory after each meeting or the exact text sent to the model. Those were rebuilt on 27 Oct by replaying pilot-05 with the run's code and the model replies that the run saved. Each saved reply is stored under the SHA-256 hash of the exact request that produced it, the replay never called the model, and every request found its saved reply. Before writing any file, the build checked every system's replayed answers (status, value and citations) and every TraceMem operation against the run's own logs, and all of them were equal. The runs' `manifest.json` files name commit `6db9267`, because a manifest records the commit at the moment the run ends; that commit only added files under `results/`, and its code is the same as `d26cd50`, the commit the run started from.

## What each system answered

Each cell is the system's answer and how the scorer classed it. `none` means the system said nothing is settled. The scoring classes are explained in `docs/metrics.md`, section 3.

| Question | Expected | similarity | similarity-recency | mem0-classic | mem0-instructions | tracemem-controlled |
|---|---|---|---|---|---|---|
| `features.text@S1` | TF-IDF | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) |
| `model.baseline@S1` | logistic regression | logistic regression (correct) | logistic regression (correct) | logistic regression on TF-IDF features (wrong_other) | logistic regression on TF-IDF features (wrong_other) | logistic regression (correct) |
| `features.text@S2` | TF-IDF | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) |
| `model.baseline@S2` | logistic regression | logistic regression (correct) | logistic regression (correct) | logistic regression on TF-IDF features (wrong_other) | logistic regression on TF-IDF features (wrong_other) | logistic regression (correct) |
| `features.text@S3` | TF-IDF | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) |
| `model.baseline@S3` | linear SVM | linear SVM (correct) | linear SVM (correct) | linear SVM (correct) | linear SVM (correct) | linear SVM (correct) |
| `model.baseline@S3-previous` | logistic regression | logistic regression (correct) | logistic regression (correct) | logistic regression on TF-IDF features (wrong_other) | logistic regression on TF-IDF features (wrong_other) | logistic regression (correct) |
| `features.text@S4` | TF-IDF | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) | TF-IDF (correct) |
| `model.baseline@S4` | linear SVM | linear SVM (correct) | linear SVM (correct) | linear SVM (correct) | linear SVM (correct) | linear SVM (correct) |

Correct answers out of 9: similarity 9, similarity-recency 9, mem0-classic 6, mem0-instructions 6, tracemem-controlled 9.

## Files in each system's folder

| File | What it holds |
|---|---|
| `memory-after-each-meeting.md` | For each meeting, the whole memory after it, and for each question about the present the 4 lines the answering model was shown. Start here for the demo. |
| `memory-after-each-meeting.json` | The same memory as records (item, value, status, source turns), with the lines shown for each question. |
| `answerer-inputs.jsonl` | One line per question: the question, the expected answer, the outcome, the whole memory, the lines shown, and every attempt sent to the answering model (the messages and the reply). An answer is retried when the call fails, or when the reply is incomplete, inconsistent, or cites a turn the model was not shown. |
| `memory-write-calls.jsonl` | Mem0 and TraceMem only: every model call made while storing a statement (TraceMem's resolver; Mem0's own update step), with the meeting it belongs to, the messages and the reply. |
| `run-*.jsonl` | The run's own logs for pilot-05, unchanged: `run-answers.jsonl`, `run-candidates.jsonl` (the statements given to the system), and for TraceMem `run-ops.jsonl` (each operation with the model's reason), `run-resolver_events.jsonl` (`attempts` above 1 means the call was retried), `run-resolver_errors.jsonl` (empty: no call failed) and `run-resolver_scores.jsonl` (each operation against the expected one); for Mem0, `run-memory_events.jsonl` (each change Mem0 made). |

The two long fixed prompts are stored once in `prompts/`: `answer-prompt-….txt` (the answer prompt every system uses) and `tracemem-resolver-prompt-….txt` (TraceMem's resolver prompt). A message stored there appears in the JSON files as `{"role": …, "content_file": …, "sha256": …}`; the file's SHA-256 equals the given hash.

## Reading a memory line

`S1-T1 Mei: model.sentiment = BERT [active] | sources=S1-T1` (from pilot-01) means: the record comes from meeting 1, line 1, spoken by Mei; it says that the sentiment model is BERT; TraceMem stored it as the current decision; and it rests on turn S1-T1. The similarity systems show the quoted turn instead of a status. The Mem0 systems show Mem0's own wording of the memory and its history of changes.
