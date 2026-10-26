# pilot-01 on Claude Haiku: every system's memory, model inputs and replies

This folder shows, for the A7 run on Claude Haiku 5.5, what each of the five systems held in memory after each meeting of pilot-01, the exact text each system sent to the model, and the model's replies. It was made for task E2 ("Demo: pilot-01 step by step, showing what each system answers after each meeting"). The same material from the local model (Qwen 3.5 4B, task A5) is in [`../../dev-a5/pilot-01-r1/`](../../dev-a5/pilot-01-r1/README.md).

## The settings of these runs

The runs used the 13 development scenarios, one run per system, the correct-memories condition (`--condition gold_candidates`), and a reply limit of 1,024 tokens. Each system showed the answering model the 4 memories closest to each question (`TRACEMEM_CONTEXT_TOP_K=4`, decision 0011, question 4). The answer prompt is the one from before the A7 changes of 26 to 27 Oct; its hash begins `b6571cd57e4e`. The deck's final runs will use the prompt after A7, so a few answers here may change after the freeze. TraceMem's resolver prompt does not change in A7.

The A5 runs in the Qwen folder used different settings: no limit of 4 memories (every memory fitted in the 12,000-byte budget) and the model's default temperature. For a comparison where only the model differs, use the chart one folder up, which compares Haiku with the A7 run of the local model at the same settings.

## How these files were made, and why they are exact

The runs saved their answers and logs, but not the memory after each meeting or the exact text sent to the model. Those were rebuilt on 27 Oct by replaying pilot-01 with the code the runs used (commit `dd0cee7`) and the model replies that the runs saved. Each saved reply is stored under the SHA-256 hash of the exact request that produced it, and the replay never called the model. Before writing any file, the build checked every system's replayed answers (status, value and citations) and every TraceMem operation against the runs' own logs, and all of them were equal.

Two requests had no saved reply. Both belong to TraceMem's answer to `model.sentiment@S3-previous` ("Which model, if any, did we use for the sentiment classifier before the current one?"). Haiku's reply ran into the 1,024-token limit twice, and the model client does not save a reply that was cut off, so its text is unknown. The replay fed back an empty cut-off reply in its place, which reproduces the run's logged result: "Answer generation failed after bounded attempts". Those two attempts are marked with a `note` in `answerer-inputs.jsonl`. The A7 changes raise the limit to 2,048 tokens.

The two Mem0 runs were rerun on 26 Oct after a fix: Haiku wraps its JSON replies to Mem0 in a Markdown code block, and the connection between our code and the Mem0 library rejected such replies until commit `2bdd44c`. The Mem0 library itself accepts them. Their `manifest.json` names commit `0b74647` or `d26cd50`, because the manifest records the commit at the moment the run ends; both runs loaded the code of `dd0cee7`, and their recorded answer-prompt hash, `b6571cd57e4e`, confirms it.

## What each system answered

Each cell is the system's answer and how the scorer classed it. `none` means the system said nothing is settled.

| Question | Expected | similarity | similarity-recency | mem0-classic | mem0-instructions | tracemem-controlled |
|---|---|---|---|---|---|---|
| `metric.primary@S1` | accuracy | accuracy (correct) | accuracy (correct) | none (missed) | accuracy (correct) | accuracy (correct) |
| `model.sentiment@S1` | BERT | BERT (correct) | BERT (correct) | BERT (correct) | BERT (correct) | BERT (correct) |
| `metric.primary@S2` | accuracy | accuracy (correct) | accuracy (correct) | accuracy (correct) | accuracy (correct) | accuracy (correct) |
| `model.ner@S2` | spaCy | spaCy (correct) | spaCy (correct) | spaCy (correct) | none (missed) | spaCy (correct) |
| `model.sentiment@S2` | BERT | BERT (correct) | BERT (correct) | BERT (correct) | BERT (correct) | BERT (correct) |
| `metric.primary@S3` | macro-F1 | macro-F1 (correct) | macro-F1 (correct) | macro-F1 (correct) | macro-F1 (correct) | macro-F1 (correct) |
| `model.ner@S3` | spaCy | spaCy (correct) | spaCy (correct) | spaCy (correct) | spaCy (correct) | spaCy (correct) |
| `model.sentiment@S3` | DistilBERT | DistilBERT (correct) | DistilBERT (correct) | DistilBERT (correct) | DistilBERT (correct) | DistilBERT (correct) |
| `model.sentiment@S3-previous` | BERT | BERT (correct) | BERT (correct) | BERT (correct) | BERT (correct) | abstain (abstained) |
| `metric.primary@S4` | macro-F1 | macro-F1 (correct) | macro-F1 (correct) | macro-F1 (correct) | macro-F1 (correct) | macro-F1 (correct) |
| `metric.primary@S4-asof-S1` | accuracy | accuracy (correct) | abstain (abstained) | none (missed) | accuracy (correct) | accuracy (correct) |
| `model.ner@S4` | spaCy | spaCy (correct) | spaCy (correct) | spaCy (correct) | spaCy (correct) | spaCy (correct) |
| `model.sentiment@S4` | DistilBERT | DistilBERT (correct) | DistilBERT (correct) | DistilBERT (correct) | DistilBERT (correct) | DistilBERT (correct) |

Correct answers out of 13, at the same settings: similarity 13 on Haiku and 13 on the local model; similarity + recency 12 and 12; Mem0 11 and 11; Mem0 + instructions 12 and 12; TraceMem 12 and 10.

**pilot-01 hardly separates the systems on Haiku.** Of the 13 development scenarios, pilot-01 shows the smallest spread between the best and the worst system on Haiku (2 answers). The systems differ most on pilot-05 (TraceMem 9 of 9, similarity 3 of 9) and dev-06 (TraceMem 14 of 14, Mem0 + instructions 3 of 14). The scoring classes are explained in `docs/metrics.md`, section 3.

## Files in each system's folder

| File | What it holds |
|---|---|
| `memory-after-each-meeting.md` | For each meeting, the whole memory after it, and for each question about the present the 4 lines the answering model was shown. Start here for the demo. |
| `memory-after-each-meeting.json` | The same memory as records (item, value, status, source turns), with the lines shown for each question. |
| `answerer-inputs.jsonl` | One line per question: the question, the expected answer, the outcome, the whole memory, the lines shown, and every attempt sent to the answering model (the messages and the reply). An answer is retried when the call fails, or when the reply is incomplete, inconsistent, or cites a turn the model was not shown. |
| `memory-write-calls.jsonl` | Mem0 and TraceMem only: every model call made while storing a statement (TraceMem's resolver; Mem0's own update step), with the meeting it belongs to, the messages and the reply. |
| `run-*.jsonl` | The run's own logs for pilot-01, unchanged: `run-answers.jsonl`, `run-candidates.jsonl` (the statements given to the system), and for TraceMem `run-ops.jsonl` (each operation with the model's reason), `run-resolver_events.jsonl` (`attempts` above 1 means the call was retried), `run-resolver_errors.jsonl` (empty: no call failed) and `run-resolver_scores.jsonl` (each operation against the expected one); for Mem0, `run-memory_events.jsonl` (each change Mem0 made). |

The two long fixed prompts are stored once in `prompts/`: `answer-prompt-….txt` (the answer prompt every system uses) and `tracemem-resolver-prompt-….txt` (TraceMem's resolver prompt). A message stored there appears in the JSON files as `{"role": …, "content_file": …, "sha256": …}`; the file's SHA-256 equals the given hash.

## Reading a memory line

`S1-T1 Mei: model.sentiment = BERT [active] | sources=S1-T1` means: the record comes from meeting 1, line 1, spoken by Mei; it says that the sentiment model is BERT; TraceMem stored it as the current decision; and it rests on turn S1-T1. The similarity systems show the quoted turn instead of a status. The Mem0 systems show Mem0's own wording of the memory and its history of changes.
