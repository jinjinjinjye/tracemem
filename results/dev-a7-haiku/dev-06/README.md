# dev-06 on Claude Haiku at the deck's frozen settings: every system's memory, model inputs and replies

This folder shows, for the A7 run on Claude Haiku 5.5 at the settings frozen as `freeze-deck`, what each of the five systems held in memory after each meeting of dev-06, the exact text each system sent to the model, and the model's replies. It was made for task E2 ("Demo: pilot-01 step by step, showing what each system answers after each meeting").

dev-06 is an explicit-revision scenario: the team switches its speech-to-text model from wav2vec 2.0 to Whisper small, its audio splitting from fixed 30-second chunks to voice activity detection, and its caption format from SRT to WebVTT. TraceMem answers all 14 questions correctly. Mem0 + instructions answers 4: after each switch it keeps giving the old value (wav2vec 2.0, fixed 30-second chunks), and it answers *none* to several questions about the past. Similarity answers 12; once it gives wav2vec 2.0 after the switch. Of the 13 development scenarios, dev-06 shows the largest spread between systems on these settings.

## The settings of these runs

The runs are the A7 run of 27 Oct, 00:01 to 00:17: the 13 development scenarios, one run per system, the correct-memories condition (`--condition gold_candidates`), a reply limit of 2,048 tokens, and the answer prompt after the A7 changes (its hash begins `67e86c7f78db`). Each system showed the answering model the 4 memories closest to each question (`TRACEMEM_CONTEXT_TOP_K=4`). These are the settings of the tag `freeze-deck`, so the deck's test runs use the same prompts and settings.

## How these files were made, and why they are exact

The run saved its answers and logs, but not the memory after each meeting or the exact text sent to the model. Those were rebuilt on 27 Oct by replaying dev-06 with the run's code and the model replies that the run saved. Each saved reply is stored under the SHA-256 hash of the exact request that produced it, the replay never called the model, and every request found its saved reply. Before writing any file, the build checked every system's replayed answers (status, value and citations) and every TraceMem operation against the run's own logs, and all of them were equal. The runs' `manifest.json` files name commit `6db9267`, because a manifest records the commit at the moment the run ends; that commit only added files under `results/`, and its code is the same as `d26cd50`, the commit the run started from.

## What each system answered

Each cell is the system's answer and how the scorer classed it. `none` means the system said nothing is settled. The scoring classes are explained in `docs/metrics.md`, section 3.

| Question | Expected | similarity | similarity-recency | mem0-classic | mem0-instructions | tracemem-controlled |
|---|---|---|---|---|---|---|
| `audio.segmentation@S1` | fixed 30-second chunks | fixed 30-second chunks (correct) | fixed 30-second chunks (correct) | fixed 30-second chunks (correct) | fixed 30-second chunks (correct) | fixed 30-second chunks (correct) |
| `model.asr@S1` | wav2vec 2.0 | wav2vec 2.0 (correct) | wav2vec 2.0 (correct) | wav2vec 2.0 (correct) | wav2vec 2.0 (correct) | wav2vec 2.0 (correct) |
| `audio.segmentation@S2` | fixed 30-second chunks | fixed 30-second chunks (correct) | fixed 30-second chunks (correct) | fixed 30-second chunks (correct) | fixed 30-second chunks (correct) | fixed 30-second chunks (correct) |
| `model.asr@S2` | Whisper small | Whisper small (correct) | Whisper small (correct) | Whisper small (correct) | wav2vec 2.0 (stale) | Whisper small (correct) |
| `output.format@S2` | SRT | SRT (correct) | SRT (correct) | SRT (correct) | none (missed) | SRT (correct) |
| `audio.segmentation@S3` | voice activity detection | voice activity detection (correct) | fixed 30-second chunks (stale) | split on voice activity detection so cuts land in pauses (wrong_other) | fixed 30-second chunks (stale) | voice activity detection (correct) |
| `model.asr@S3` | Whisper small | wav2vec 2.0 (stale) | Whisper small (correct) | Whisper small (correct) | wav2vec 2.0 (stale) | Whisper small (correct) |
| `model.asr@S3-previous` | wav2vec 2.0 | wav2vec 2.0 (correct) | abstain (abstained) | wav2vec 2.0 (correct) | none (missed) | wav2vec 2.0 (correct) |
| `output.format@S3` | SRT | SRT (correct) | SRT (correct) | SRT (correct) | none (missed) | SRT (correct) |
| `audio.segmentation@S4` | voice activity detection | voice activity detection (correct) | voice activity detection (correct) | voice activity detection (correct) | fixed 30-second chunks (stale) | voice activity detection (correct) |
| `audio.segmentation@S4-previous` | fixed 30-second chunks | fixed 30-second chunks (correct) | fixed 30-second chunks (correct) | fixed 30-second chunks (correct) | none (missed) | fixed 30-second chunks (correct) |
| `model.asr@S4` | Whisper small | Whisper small (correct) | Whisper small (correct) | Whisper small (correct) | wav2vec 2.0 (stale) | Whisper small (correct) |
| `output.format@S4` | WebVTT | WebVTT (correct) | WebVTT (correct) | WebVTT (correct) | WebVTT (correct) | WebVTT (correct) |
| `output.format@S4-asof-S2` | SRT | none (missed) | abstain (abstained) | SRT (correct) | none (missed) | SRT (correct) |

Correct answers out of 14: similarity 12, similarity-recency 11, mem0-classic 13, mem0-instructions 4, tracemem-controlled 14.

## Files in each system's folder

| File | What it holds |
|---|---|
| `memory-after-each-meeting.md` | For each meeting, the whole memory after it, and for each question about the present the 4 lines the answering model was shown. Start here for the demo. |
| `memory-after-each-meeting.json` | The same memory as records (item, value, status, source turns), with the lines shown for each question. |
| `answerer-inputs.jsonl` | One line per question: the question, the expected answer, the outcome, the whole memory, the lines shown, and every attempt sent to the answering model (the messages and the reply). An answer is retried when the call fails, or when the reply is incomplete, inconsistent, or cites a turn the model was not shown. |
| `memory-write-calls.jsonl` | Mem0 and TraceMem only: every model call made while storing a statement (TraceMem's resolver; Mem0's own update step), with the meeting it belongs to, the messages and the reply. |
| `run-*.jsonl` | The run's own logs for dev-06, unchanged: `run-answers.jsonl`, `run-candidates.jsonl` (the statements given to the system), and for TraceMem `run-ops.jsonl` (each operation with the model's reason), `run-resolver_events.jsonl` (`attempts` above 1 means the call was retried), `run-resolver_errors.jsonl` (empty: no call failed) and `run-resolver_scores.jsonl` (each operation against the expected one); for Mem0, `run-memory_events.jsonl` (each change Mem0 made). |

The two long fixed prompts are stored once in `prompts/`: `answer-prompt-….txt` (the answer prompt every system uses) and `tracemem-resolver-prompt-….txt` (TraceMem's resolver prompt). A message stored there appears in the JSON files as `{"role": …, "content_file": …, "sha256": …}`; the file's SHA-256 equals the given hash.

## Reading a memory line

`S1-T1 Mei: model.sentiment = BERT [active] | sources=S1-T1` (from pilot-01) means: the record comes from meeting 1, line 1, spoken by Mei; it says that the sentiment model is BERT; TraceMem stored it as the current decision; and it rests on turn S1-T1. The similarity systems show the quoted turn instead of a status. The Mem0 systems show Mem0's own wording of the memory and its history of changes.
