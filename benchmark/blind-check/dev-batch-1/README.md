# Blind-check printouts for dev-01 to dev-08

This folder holds the printouts used to blind-check the eight development scenarios dev-01 to dev-08 in [`benchmark/scenarios/dev/`](../../scenarios/dev/). Each printout is what `tracemem blind` prints for one scenario: the meetings and the questions, without the script, the title or the category. Two teammates each received four printouts and the guide. Each teammate answered every question from the dialogue alone and did not label the act of each turn, because the guide asked for answers only.

- [`GUIDE.md`](GUIDE.md) is the guide that both teammates received; the two copies were identical, so this folder keeps one.
- [`B/`](B/) holds the four printouts that member B answered.
- [`C/`](C/) holds the four printouts that member C answered.

| Printout | Scenario title (from the scenario file, not shown to the reviewer) | Answered by |
|---|---|---|
| `B/dev-01.md` | Demand model with a suggestion nobody adopts | member B |
| `C/dev-02.md` | A disputed backbone for the leaf classifier | member C |
| `B/dev-03.md` | Two learning rates in one recommender | member B |
| `C/dev-04.md` | Card-fraud model with recollections and side reports | member C |
| `B/dev-05.md` | Cleaning and tagging bird-call clips | member B |
| `C/dev-06.md` | Lecture captions changed with explicit replacements | member C |
| `B/dev-07.md` | Readmission choices changed without naming the old ones | member B |
| `C/dev-08.md` | Topic model adopted two meetings after it was suggested | member C |

The printouts differ from the plain `tracemem blind` output in two small ways. Every turn line ends in two spaces, so that each turn shows on its own line when the Markdown is rendered. The heading above the questions says `none` instead of 'nothing settled', to match the guide. The meetings and the questions are otherwise the same as in the scenario files.

The two teammates' answers were compared with the answers that `tracemem replay` computes from each scenario's script, and 110 of the 117 answers agreed. Each scenario file records this check in its `review` field, as `status: blind_checked` with the reviewer's role.
