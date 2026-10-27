# pilot-01, A5 repeat 1: every system's memory, model inputs and replies

This folder shows, for the A5 development run (repeat 1, local Qwen 3.5 4B, correct-memories condition), what each of the five systems held in memory after each meeting of pilot-01, the exact text each one sent to the model, and the model's replies. It was made for task E2 ("Demo: pilot-01 step by step, showing what each system answers after each meeting") and is useful for explaining failures.

## How these files were made, and why they are exact

The A5 run saved its answers and logs, but not the memory after each meeting or the exact text sent to the model. Those were rebuilt on 26 Oct by replaying pilot-01 with A5's own code (commit `f298722`) and the model replies that A5 saved. Each saved reply is stored under the SHA-256 hash of the exact request that produced it, and the replay was set to stop on any request without a saved reply instead of calling the model. All 108 requests of the five systems found their saved replies, so every request in this folder is byte-for-byte the one A5 sent, and every reply is the one the model gave. As a cross-check, the replayed answers and TraceMem's operations equal A5's saved logs exactly. The only differences are Mem0's internal memory ids (`id`, `history_id`), which Mem0 draws at random on every run, and token counts, which a saved reply reports as zero.

## What each system answered

Each cell is the system's answer and how the scorer classed it. `none` means the system said nothing is settled.

| Question | Expected | similarity | similarity-recency | mem0-classic | mem0-instructions | tracemem-controlled |
|---|---|---|---|---|---|---|
| `metric.primary@S1` | accuracy | accuracy (correct) | accuracy (correct) | accuracy (correct) | accuracy (correct) | accuracy (correct) |
| `model.sentiment@S1` | BERT | BERT (correct) | BERT (correct) | BERT (correct) | accuracy (wrong_other) | conflict (false_conflict) |
| `metric.primary@S2` | accuracy | accuracy (correct) | accuracy (correct) | accuracy (correct) | accuracy (correct) | accuracy (correct) |
| `model.ner@S2` | spaCy | spaCy (correct) | spaCy (correct) | spaCy (correct) | spaCy (correct) | spaCy (correct) |
| `model.sentiment@S2` | BERT | BERT (correct) | BERT (correct) | BERT (correct) | DistilBERT (unconfirmed_as_current) | none (missed) |
| `metric.primary@S3` | macro-F1 | none (missed) | none (missed) | macro-F1 (correct) | macro-F1 (correct) | macro-F1 (correct) |
| `model.ner@S3` | spaCy | spaCy (correct) | spaCy (correct) | spaCy (correct) | spaCy (correct) | spaCy (correct) |
| `model.sentiment@S3` | DistilBERT | none (missed) | none (missed) | DistilBERT (correct) | none (missed) | DistilBERT (correct) |
| `model.sentiment@S3-previous` | BERT | DistilBERT (current_as_historical) | DistilBERT (current_as_historical) | BERT (correct) | DistilBERT (current_as_historical) | DistilBERT (current_as_historical) |
| `metric.primary@S4` | macro-F1 | macro-F1 (correct) | macro-F1 (correct) | macro-F1 (correct) | none (missed) | macro-F1 (correct) |
| `metric.primary@S4-asof-S1` | accuracy | accuracy (correct) | accuracy (correct) | abstain (abstained) | accuracy (correct) | accuracy (correct) |
| `model.ner@S4` | spaCy | spaCy (correct) | spaCy (correct) | spaCy (correct) | spaCy (correct) | spaCy (correct) |
| `model.sentiment@S4` | DistilBERT | DistilBERT (correct) | DistilBERT (correct) | DistilBERT (correct) | DistilBERT (correct) | DistilBERT (correct) |

The scoring classes are explained in `docs/metrics.md`, section 3.

## Files in each system's folder

| File | What it holds |
|---|---|
| `memory-after-each-meeting.md` | The memory the answering model saw after each meeting, as sent. Start here for the demo. |
| `memory-after-each-meeting.json` | The same memory as records (item, value, status, source turns). |
| `answerer-inputs.jsonl` | One line per question: the question, the expected answer, the outcome, and every attempt sent to the answering model (the messages and the reply). An answer is retried when the call fails or times out, or when the reply is incomplete, inconsistent, or cites a turn it was not shown; each retry is a further attempt. |
| `memory-write-calls.jsonl` | Mem0 and TraceMem only: every model call made while storing a statement (TraceMem's resolver; Mem0's own update step), with the meeting it belongs to, the messages and the reply. |
| `a5-*.jsonl` | A5's own logs for pilot-01, unchanged: `a5-answers.jsonl`, `a5-candidates.jsonl` (the statements given to the system), and for TraceMem `a5-ops.jsonl` (each operation with the model's rationale), `a5-resolver_events.jsonl` (`attempts` above 1 means the call was retried), `a5-resolver_errors.jsonl` (empty: no call failed), `a5-resolver_scores.jsonl` and `a5-resolver_analysis.jsonl` (each operation against the expected one); for Mem0, `a5-memory_events.jsonl` (each change Mem0 made). |

The two long fixed prompts are stored once in `prompts/`: `answer-prompt-….txt` (the answer prompt every system uses) and `tracemem-resolver-prompt-….txt` (TraceMem's resolver prompt). A message stored there appears in the JSON files as `{"role": …, "content_file": …, "sha256": …}`; the file's SHA-256 equals the given hash.

## Reading a memory line

`S1-T1 Mei: model.sentiment = BERT [proposed] | sources=S1-T1` means: the record comes from meeting 1, line 1, spoken by Mei; it says the sentiment model is BERT; TraceMem filed it as a proposal, not a decision; and it rests on turn S1-T1. The similarity systems show the quoted turn instead of a status; the Mem0 systems show Mem0's own wording of the memory.

For example, TraceMem's memory after S1 holds S1-T1 ("Let's go with BERT for the sentiment classifier. It's the safe choice.") as `[proposed]`, and after S2 it holds DistilBERT, which was only suggested in S2-T3, also as `[proposed]`. Its answers to `model.sentiment@S1` and `model.sentiment@S2` follow from that memory; the resolver's reasoning for each operation is in `a5-ops.jsonl` and `memory-write-calls.jsonl`.
