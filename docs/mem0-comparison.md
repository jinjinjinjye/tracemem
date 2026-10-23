# Mem0 comparison (open-source baseline)

The `mem0` system is an **actual Mem0 OSS 2.2.1 adapter**, not an imitation of Mem0 or a gold-label probe. It runs inside TraceMem's existing scenario harness and scorer. It is registered with `uses_gold=False`.

## Run

From the repository root, with Python >= 3.11:

```bash
pip install -e '.[dev,mem0]'
export OPENAI_API_KEY='your-key'  # keep keys out of the repository
tracemem systems
tracemem validate benchmark/scenarios/dev
tracemem run --system mem0 --split dev --condition end_to_end
```

The adapter instantiates `mem0.Memory.from_config` once per scenario, with an isolated on-disk Qdrant vector store and SQLite history database in a temporary directory. A unique `user_id` further isolates each scenario and run. Every observed turn is passed to `memory.add` with `infer=True`, in the exact order supplied by the harness, using the original speaker and text. Mem0 performs its normal extraction and memory management; the adapter does **not** classify decisions or apply TraceMem's ADD/KEEP/SUPERSEDE/FLAG rules.

For each checkpoint question, the adapter calls `memory.search` with a `user_id` filter and `top_k=10`. Retrieved memories are passed to a separate answer-model call, which emits TraceMem's `Answer` (`answer`, `none`, `conflict`, `abstain`). Citations are accepted only when Mem0 returned a source-turn ID that the system actually observed. A historical `as_of` question excludes memories attributed to turns after the requested session, and un-attributed memories; Mem0 may nonetheless have overwritten the older value, so historical-answer performance is a substantive baseline limitation.

`gold_candidates` is **not supported** by this adapter. Mem0's native extraction and update behavior is part of the baseline; passing TraceMem's candidate or operation labels would change the system being evaluated. Compare `mem0` to a real, non-gold TraceMem pipeline in the `end_to_end` condition. The existing `pipeline-gold` and probe systems see gold labels and **must not** be reported as competitors or experimental results.

## Configuration

| Environment variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | required | Mem0 extraction/embeddings and answer model |
| `MEM0_MEMORY_MODEL` | `gpt-5-mini` | Mem0's model for extraction and memory management |
| `MEM0_EMBEDDING_MODEL` | `text-embedding-3-small` | Mem0's embedding model |
| `MEM0_ANSWER_MODEL` | `gpt-4.1-mini` | Model used to answer benchmark questions from Mem0 results |
| `MEM0_TOP_K` | `10` | Number of Mem0 search results |

The installed `mem0ai` version, model IDs, context count, and answer prompt hash are included in the benchmark's `manifest.json` through `describe()`. Do not change settings when moving from development to test data. Align the answer model, answer instructions and retrieval budget across Mem0 and a production TraceMem system before making strong causal claims; the present adapter provides the first runnable end-to-end Mem0 comparison, not a completed parity study.

## Known limitations and interpretation

- **Mem0 algorithm**: Mem0's SDK may create, update or remove semantic memories when `infer=True`. Those are its own memory operations, *not* the TraceMem operation labels. We therefore compare downstream answers and error rates, not Mem0's internal actions against the TraceMem action macro-F1 metric.
- **Provenance**: `source_turn_id` is attached to each input turn as metadata. Mem0 may merge/update memories and not preserve the source metadata for all supporting turns. Missing citations are counted as missing; the adapter never fabricates them. Source-turn metadata alone is not a guarantee that a transformed memory has fully supported provenance.
- **Historical answers**: Mem0's search is over its current semantic memories. The adapter does not retrofit TraceMem-style version history into the baseline. A previous or `as_of` answer may be unavailable, even when the original dialogue contained it.
- **Different compute budgets**: The adapter uses Mem0's configured memory model and a separate answer model. Current `Answer.usage` only records the *answer* completion, not Mem0's memory extraction, embeddings, or retrieval calls. Do not interpret it as the full Mem0 run cost.
- **Model parity**: TraceMem's real model-based components are still planned. Until they exist, no apples-to-apples Mem0-vs-TraceMem accuracy score can be produced. The five pilot scenarios are development examples, not a held-out evaluation.
- **Real services**: Running the adapter needs credentials and makes external model calls. Unit tests inject fakes to exercise the integration contract, but do not establish that a particular remote model or Mem0 release behaves correctly on the pilot benchmark.

## Comparison table after both real systems exist

```bash
tracemem run --system mem0 --split dev --condition end_to_end
tracemem run --system tracemem --split dev --condition end_to_end  # only after it is registered
tracemem report runs/<mem0-run> runs/<tracemem-run>
```

Measure current-state accuracy, stale-answer rate, false certainty, historical-answer accuracy, citation support, and non-answer rate together. A system can look safe merely by refusing to answer. Only conduct held-out test evaluation after the team freezes settings and seals the test split.

**References:** [Mem0 OSS Python quickstart](https://docs.mem0.ai/open-source/python-quickstart), [Mem0 memory operations](https://docs.mem0.ai/core-concepts/memory-operations/add), [Mem0 configuration](https://docs.mem0.ai/open-source/configuration), [Mem0 2.2.1 release](https://pypi.org/project/mem0ai/2.2.1/).
