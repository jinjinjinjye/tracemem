# The five systems on the local model and on Claude Haiku

![The same five systems on the local model and on Haiku](local-vs-haiku.png)

The chart compares two runs of the five systems on the 13 development scenarios. Only the model differs between the two runs: the local model is Qwen 3.5 4B (run at temperature 0), and the other model is Claude Haiku 5.5. Both runs used one run per system, the correct-memories condition, 4 memories shown per question, a reply limit of 1,024 tokens, and the answer prompt from before the A7 changes (hash `b6571cd57e4e`). The local run is `runs/a7/base/` and the Haiku run is `runs/a7/haiku/` on A's machine; both are single runs, so differences of a few questions are within the variation between repeated runs.

| System | Present, local | Present, Haiku | Past, local | Past, Haiku | Suggestion given as current, local | Suggestion given as current, Haiku |
|---|---|---|---|---|---|---|
| Similarity | 0.79 | 0.84 | 0.30 | 0.67 | 0.11 | 0.00 |
| Similarity + recency | 0.78 | 0.83 | 0.37 | 0.20 | 0.16 | 0.00 |
| Mem0 | 0.50 | 0.72 | 0.30 | 0.50 | 0.26 | 0.32 |
| Mem0 + instructions | 0.48 | 0.66 | 0.27 | 0.53 | 0.05 | 0.37 |
| TraceMem | 0.54 | 0.99 | 0.27 | 0.80 | 0.42 | 0.00 |

"Present" is the share of the 140 questions about the present answered correctly. "Past" is the share of the 30 questions about earlier states answered correctly. "Suggestion given as current" is the share of the 19 suggestion-trap questions where the system gave a suggestion that nobody adopted as the current value; lower is better.

**Most of TraceMem's failures on the local model came from the model, not from TraceMem's design.** TraceMem's resolver, which decides what each new statement does to memory, chose the expected operation for 55 of 121 statements on the local model and for 117 of 121 on Haiku. TraceMem's share of correct answers about the present went from 0.54 on the local model to 0.99 on Haiku.

The folder [`pilot-01/`](pilot-01/README.md) holds every system's memory, model inputs and replies for pilot-01 on Haiku.
