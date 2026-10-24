# When checkpoint questions are asked

This page shows, for every scenario, which questions the harness asks and after which meeting. The rules are in [`docs/benchmark.md`](../../docs/benchmark.md) §6; this page applies them to each file. It lists questions, not their answers: the correct answers come only from `tracemem replay` (`AGENTS.md`, hard rule 4).

**Last updated: 2026-10-24.** Covers the five development scenarios in `dev/` (pilot-01 to pilot-05); no test scenarios yet.

**Is a table stale?** Each scenario's section gives a fingerprint: the first 12 characters of the file's SHA-256 when this page was last updated. If `sha256sum benchmark/scenarios/dev/<file>` starts with different characters, the scenario has changed since, and its table may be wrong.

**Keeping it current.** Update this page in the same pull request that adds or changes a scenario, and change the date and the fingerprint. `tracemem replay <file>` prints every question; an automatic question's id is `<item>@<session>`, so `model.ner@S2` is the `model.ner` question asked after meeting 2.

## How to read the tables

- **Item:** the thing being decided or tracked, as it is keyed under `items:`.
- **Asked as:** the item's `ask:` text, which becomes the automatic "what holds now?" question.
- **First event:** the first line that does something to the item other than mention it. The automatic question starts at the end of that meeting.
- **Asked after:** every meeting at whose end the automatic question is asked, from the first event's meeting to the last meeting.
- **Count:** how many automatic questions the item produces.
- **Written by hand:** questions about the past, from the scenario's `questions:` list. Each is asked once.

## Development scenarios

The five pilots are below. Each new development scenario gets its table when it is added to `dev/`.

### pilot-01: Classifier choice with a late suggestion

[`dev/pilot-01-suggestion-after-decision.yaml`](dev/pilot-01-suggestion-after-decision.yaml) · category `suggestion_after_decision` · meetings S1, S2, S3, S4 · fingerprint `975d4b0c1268`

| Item | Asked as (`ask:`) | First event | Asked after | Count |
|---|---|---|---|---|
| `model.sentiment` | Which model are we using for the sentiment classifier? | S1-T1 ("Let's go with BERT for the sentiment classifier. It's the safe choice."): decide BERT | S1, S2, S3, S4 | 4 |
| `metric.primary` | What is our primary evaluation metric? | S1-T2 ("Sounds good. What do we report, plain accuracy?"): suggest accuracy | S1, S2, S3, S4 | 4 |
| `model.ner` | Which model are we using for NER? | S2-T5 ("Separately, for the NER part we'll use a spaCy model."): decide spaCy | S2, S3, S4 | 3 |

Written by hand under `questions:`:

| Id | Kind | Asked after | Question |
|---|---|---|---|
| `model.sentiment@S3-previous` | previous | S3 | Which model, if any, did we use for the sentiment classifier before the current one? |
| `metric.primary@S4-asof-S1` | as_of | S4 (about the end of S1) | What was the state of the primary-metric choice at the end of the first meeting? |

**Total: 11 automatic + 2 by hand = 13 questions.**

### pilot-02: A contested dataset choice

[`dev/pilot-02-unresolved-contradiction.yaml`](dev/pilot-02-unresolved-contradiction.yaml) · category `unresolved_contradiction` · meetings S1, S2, S3, S4 · fingerprint `a6b1556d5ff1`

| Item | Asked as (`ask:`) | First event | Asked after | Count |
|---|---|---|---|---|
| `dataset.train` | Which dataset are we training on? | S1-T1 ("We'll train on the IMDB reviews."): decide IMDB | S1, S2, S3, S4 | 4 |
| `task.label_audit` | What is the status of the label audit? | S1-T3 ("Priya, can you audit 200 labels from the training set?"): task_open | S1, S2, S3, S4 | 4 |

Written by hand under `questions:`:

| Id | Kind | Asked after | Question |
|---|---|---|---|
| `dataset.train@S4-previous` | previous | S4 | Which dataset, if any, did we train on before the current one? |
| `dataset.train@S4-asof-S2` | as_of | S4 (about the end of S2) | What was the state of the dataset choice at the end of the second meeting? |

**Total: 8 automatic + 2 by hand = 10 questions.**

### pilot-03: Two models in one project

[`dev/pilot-03-confusable-items.yaml`](dev/pilot-03-confusable-items.yaml) · category `confusable_items` · meetings S1, S2, S3, S4 · fingerprint `75bee44ac2ca`

| Item | Asked as (`ask:`) | First event | Asked after | Count |
|---|---|---|---|---|
| `model.sentiment` | Which model are we using for sentiment? | S1-T1 ("For sentiment, DistilBERT is fast enough. Let's use it."): decide DistilBERT | S1, S2, S3, S4 | 4 |
| `model.ner` | Which model are we using to tag product names? | S2-T1 ("For the product-name tagger, we'll fine-tune BERT."): decide BERT | S2, S3, S4 | 3 |

Written by hand under `questions:`:

| Id | Kind | Asked after | Question |
|---|---|---|---|
| `model.ner@S4-previous` | previous | S4 | Which model, if any, did we use for tagging product names before the current one? |

**Total: 7 automatic + 1 by hand = 8 questions.**

### pilot-04: Two tasks with changing progress

[`dev/pilot-04-task-lifecycle.yaml`](dev/pilot-04-task-lifecycle.yaml) · category `task_lifecycle` · meetings S1, S2, S3, S4 · fingerprint `1421aaca463e`

| Item | Asked as (`ask:`) | First event | Asked after | Count |
|---|---|---|---|---|
| `task.baseline_runs` | What is the status of the baseline runs? | S1-T2 ("I'll take the baseline runs: logistic regression and gradient boosting."): task_open | S1, S2, S3, S4 | 4 |
| `task.error_analysis` | What is the status of the error analysis? | S1-T3 ("And I'll do an error analysis on 100 misclassified customers once we have predictions."): task_open | S1, S2, S3, S4 | 4 |
| `compute.gpu` | Where are we running our experiments? | S1-T1 ("Let's run everything on Colab for now."): decide Colab | S1, S2, S3, S4 | 4 |

Written by hand under `questions:`:

| Id | Kind | Asked after | Question |
|---|---|---|---|
| `compute.gpu@S2-previous` | previous | S2 | Which compute setup, if any, did we use for our experiments before the current one? |

**Total: 12 automatic + 1 by hand = 13 questions.**

### pilot-05: Hypotheticals and recollections around a baseline

[`dev/pilot-05-mention-after-decision.yaml`](dev/pilot-05-mention-after-decision.yaml) · category `mention_after_decision` · meetings S1, S2, S3, S4 · fingerprint `b4df4235d432`

| Item | Asked as (`ask:`) | First event | Asked after | Count |
|---|---|---|---|---|
| `model.baseline` | Which baseline classifier are we using? | S1-T1 ("Let's make the baseline logistic regression on TF-IDF features."): decide logistic regression | S1, S2, S3, S4 | 4 |
| `features.text` | What text features does the baseline use? | S1-T1 ("Let's make the baseline logistic regression on TF-IDF features."): decide TF-IDF | S1, S2, S3, S4 | 4 |

Written by hand under `questions:`:

| Id | Kind | Asked after | Question |
|---|---|---|---|
| `model.baseline@S3-previous` | previous | S3 | Which baseline classifier, if any, did we use before the current one? |

**Total: 8 automatic + 1 by hand = 9 questions.**

## Test scenarios

Their tables are added after the freeze, when the test scenarios are converted and committed (see [`test/README.md`](test/README.md)). Until then this section stays empty: listing a test scenario's items or questions would tell the people who tune the systems what the test asks.

## FAQ

### Why are there more questions than items?

Each item's `ask:` question is asked after every meeting, from the meeting of its first event to the last meeting. Pilot-01 has three items and four meetings. `model.sentiment` and `metric.primary` have their first events in meeting 1, so each is asked four times. `model.ner` is first decided in meeting 2, by S2-T5 ("Separately, for the NER part we'll use a spaCy model."), so it is asked three times. That gives 4 + 4 + 3 = 11 automatic questions; with the two written by hand, pilot-01 asks 13.

Repeating a question does not inflate the score. Under episode weighting ([`docs/metrics.md`](../../docs/metrics.md) §6), a run of repeated questions whose correct answer does not change counts once in total. In pilot-04, `compute.gpu@S2`, `@S3` and `@S4` ("Where are we running our experiments?") form one such run.

### Is every meeting a session?

Yes. A session is one meeting, with an id (`S1`, `S2`, …) and a date. A turn is one line, so one speaker can have several turns in a row: in pilot-01, S2-T4 ("Possibly. I'd rather see numbers first.") and S2-T5 ("Separately, for the NER part we'll use a spaCy model.") are both Mei's.

The questions are asked at the end of a session, after its last turn. In pilot-04, meeting 1 ends after S1-T3 ("And I'll do an error analysis on 100 misclassified customers once we have predictions."). All three of its items have had an event by then, so all three questions are asked after S1.

Turns carry no clock time of their own. The harness gives each one a made-up time on its session's date: session n starts at 10:00 plus (n − 1) hours, and each turn adds a minute ([`docs/benchmark.md`](../../docs/benchmark.md) §2).

### Does the model build up context from being asked the same question so often?

No. Each question is a separate call to the model. The call contains that question and whatever the system's memory retrieves for it: records, and the turns they came from. Nothing carries over from one call to the next.

Answering also cannot change what a system remembers. [`src/tracemem/systems/base.py`](../../src/tracemem/systems/base.py) requires that "`answer` must not change what the system remembers", and the harness checks it. A system learns only from the turns it observes.

So whether an answer is right depends only on the system's memory, which is exactly what the experiment compares: every system gets the same model, the same answer prompt and the same questions.

### When does a question go in an item's `ask:`, and when under `questions:`?

| You want to ask | Write it | It is asked |
|---|---|---|
| What holds now for an item ("Which model are we using?") | once, as the item's `ask:` under `items:` | automatically, after every meeting from the item's first event |
| What the item was before its current value | under `questions:`, with `kind: previous` | once, after the meeting named in `after` |
| What state the item was in at the end of an earlier meeting | under `questions:`, with `kind: as_of` and `session` | once, after the meeting named in `after` |
| One automatic question, worded differently | under `questions:`, with `kind: current` and that question's id, `<item>@<session>` | instead of that one automatic question |

Pilot-01 shows the first two rows:

```yaml
items:
  - key: model.sentiment
    kind: decision
    ask: Which model are we using for the sentiment classifier?   # asked after S1, S2, S3 and S4
    # ...values...

questions:
  - {id: model.sentiment@S3-previous, after: S3, kind: previous, item: model.sentiment,
     text: "Which model, if any, did we use for the sentiment classifier before the current one?"}   # asked once, after S3
```

The `ask:` line produces `model.sentiment@S1` to `model.sentiment@S4`. The hand-written question is asked once, after S3, where S3-T2 ("Then we switch the sentiment classifier to DistilBERT, since BERT misses the latency limit.") has just replaced the earlier choice.

Every question names an item. To ask about something new, add it as an item first. An item without an `ask:` line gets no automatic questions.

### How is a test scenario written in plain English turned into this format?

Test authors write their scenarios in plain English: meetings with dates, one line per turn, and their questions, each with its answer and the reason. Nobody who tunes a system reads them before the freeze that covers them ([`docs/benchmark.md`](../../docs/benchmark.md) §10). After that freeze, the person who runs the experiment converts each one:

1. List the items being decided, with their values and spellings. Each "what holds now?" question becomes an item's `ask:`.
2. Copy each meeting as a session with its date, and each line as a turn.
3. Label in `script:` what each line does: decide, suggest, accept, revise, mention and the rest ([`docs/benchmark.md`](../../docs/benchmark.md) §4). A line that changes nothing gets no label.
4. Put the questions about the past under `questions:`.
5. Run `tracemem validate` and `tracemem replay`, then compare the replay's answers with the author's. A difference means either the conversion or the author's answer is wrong; settle it with the author before any system runs.

The author's answers are not copied into the file, because the replay computes every correct answer (`AGENTS.md`, hard rule 4). They serve only as the check in step 5.

For example, this plain-English meeting:

```text
Meeting 2, Thu 8 Oct
Arun: Maybe we could try DistilBERT? It might be faster.
Mei: Possibly. I'd rather see numbers first.
```

becomes:

```yaml
sessions:
  - id: S2
    date: 2026-10-08
    turns:
      - {id: S2-T1, speaker: Arun, text: "Maybe we could try DistilBERT? It might be faster."}
      - {id: S2-T2, speaker: Mei, text: "Possibly. I'd rather see numbers first."}

script:
  - {turn: S2-T1, act: suggest, item: model.sentiment, value: DistilBERT}
```

S2-T2 ("Possibly. I'd rather see numbers first.") changes nothing, so it has no script entry.
