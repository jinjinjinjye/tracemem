# tracemem-controlled: memory after each meeting (pilot-01, Haiku, freeze-deck settings, k = 4)

For each meeting: the whole memory after it, then, for each question about the present asked after it, the 4 lines the answering model was shown (k = 4: the 4 records closest to the question). A question about an earlier meeting or about history has its exact input in answerer-inputs.jsonl.

## After S1: the whole memory (3 records)

```text
S1-T1 Mei: model.sentiment = BERT [active] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [active] | sources=S1-T3,S1-T2
```

Shown for `metric.primary@S1`:

```text
S1-T1 Mei: model.sentiment = BERT [active] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [active] | sources=S1-T3,S1-T2
```

Shown for `model.sentiment@S1`:

```text
S1-T1 Mei: model.sentiment = BERT [active] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [active] | sources=S1-T3,S1-T2
```

## After S2: the whole memory (5 records)

```text
S1-T1 Mei: model.sentiment = BERT [active] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [active] | sources=S1-T3,S1-T2
S2-T3 Arun: model.sentiment = DistilBERT [proposed] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
```

Shown for `metric.primary@S2`:

```text
S1-T1 Mei: model.sentiment = BERT [active] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [active] | sources=S1-T3,S1-T2
S2-T3 Arun: model.sentiment = DistilBERT [proposed] | sources=S2-T3
```

Shown for `model.ner@S2`:

```text
S1-T1 Mei: model.sentiment = BERT [active] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S2-T3 Arun: model.sentiment = DistilBERT [proposed] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
```

Shown for `model.sentiment@S2`:

```text
S1-T1 Mei: model.sentiment = BERT [active] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S2-T3 Arun: model.sentiment = DistilBERT [proposed] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
```

## After S3: the whole memory (8 records)

```text
S1-T1 Mei: model.sentiment = BERT [superseded] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [superseded] | sources=S1-T3,S1-T2
S2-T3 Arun: model.sentiment = DistilBERT [superseded] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
S3-T2 Mei: model.sentiment = DistilBERT [active] | sources=S3-T2,S2-T3
S3-T3 Arun: metric.primary = macro-F1 [superseded] | sources=S3-T3
S3-T4 Mei: metric.primary = macro-F1 [active] | sources=S3-T4,S3-T3
```

Shown for `metric.primary@S3`:

```text
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [superseded] | sources=S1-T3,S1-T2
S3-T3 Arun: metric.primary = macro-F1 [superseded] | sources=S3-T3
S3-T4 Mei: metric.primary = macro-F1 [active] | sources=S3-T4,S3-T3
```

Shown for `model.ner@S3`:

```text
S1-T1 Mei: model.sentiment = BERT [superseded] | sources=S1-T1
S2-T3 Arun: model.sentiment = DistilBERT [superseded] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
S3-T2 Mei: model.sentiment = DistilBERT [active] | sources=S3-T2,S2-T3
```

Shown for `model.sentiment@S3`:

```text
S1-T1 Mei: model.sentiment = BERT [superseded] | sources=S1-T1
S2-T3 Arun: model.sentiment = DistilBERT [superseded] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
S3-T2 Mei: model.sentiment = DistilBERT [active] | sources=S3-T2,S2-T3
```

Shown for `model.sentiment@S3-previous`:

```text
S1-T1 Mei: model.sentiment = BERT [superseded] | sources=S1-T1
S2-T3 Arun: model.sentiment = DistilBERT [superseded] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
S3-T2 Mei: model.sentiment = DistilBERT [active] | sources=S3-T2,S2-T3
```

## After S4: the whole memory (8 records)

```text
S1-T1 Mei: model.sentiment = BERT [superseded] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [superseded] | sources=S1-T3,S1-T2
S2-T3 Arun: model.sentiment = DistilBERT [superseded] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
S3-T2 Mei: model.sentiment = DistilBERT [active] | sources=S3-T2,S2-T3,S4-T1
S3-T3 Arun: metric.primary = macro-F1 [superseded] | sources=S3-T3
S3-T4 Mei: metric.primary = macro-F1 [active] | sources=S3-T4,S3-T3,S4-T1
```

Shown for `metric.primary@S4`:

```text
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [superseded] | sources=S1-T3,S1-T2
S3-T3 Arun: metric.primary = macro-F1 [superseded] | sources=S3-T3
S3-T4 Mei: metric.primary = macro-F1 [active] | sources=S3-T4,S3-T3,S4-T1
```

Shown for `model.ner@S4`:

```text
S1-T1 Mei: model.sentiment = BERT [superseded] | sources=S1-T1
S2-T3 Arun: model.sentiment = DistilBERT [superseded] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
S3-T2 Mei: model.sentiment = DistilBERT [active] | sources=S3-T2,S2-T3,S4-T1
```

Shown for `model.sentiment@S4`:

```text
S1-T1 Mei: model.sentiment = BERT [superseded] | sources=S1-T1
S2-T3 Arun: model.sentiment = DistilBERT [superseded] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
S3-T2 Mei: model.sentiment = DistilBERT [active] | sources=S3-T2,S2-T3,S4-T1
```
