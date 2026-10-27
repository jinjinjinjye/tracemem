# tracemem-controlled: memory after each meeting (pilot-01, A5 repeat 1)

Each block is the memory text the answering model saw for the questions about the present asked after that meeting, exactly as sent. The budget held every record, so it is the whole memory. A question about the state at an earlier meeting may see less: its exact input is in answerer-inputs.jsonl.

## After S1 (3 records)

```text
S1-T1 Mei: model.sentiment = BERT [proposed] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [active] | sources=S1-T3,S1-T2
```

## After S2 (5 records)

```text
S1-T1 Mei: model.sentiment = BERT [proposed] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [active] | sources=S1-T3,S1-T2
S2-T3 Arun: model.sentiment = DistilBERT [proposed] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
```

## After S3 (7 records)

```text
S1-T1 Mei: model.sentiment = BERT [proposed] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [superseded] | sources=S1-T3,S1-T2
S2-T3 Arun: model.sentiment = DistilBERT [superseded] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
S3-T2 Mei: model.sentiment = DistilBERT [active] | sources=S3-T2,S2-T3
S3-T3 Arun: metric.primary = macro-F1 [active] | sources=S3-T3,S3-T4
```

## After S4 (8 records)

```text
S1-T1 Mei: model.sentiment = BERT [proposed] | sources=S1-T1
S1-T2 Arun: metric.primary = accuracy [superseded] | sources=S1-T2
S1-T3 Mei: metric.primary = accuracy [superseded] | sources=S1-T3,S1-T2
S2-T3 Arun: model.sentiment = DistilBERT [superseded] | sources=S2-T3
S2-T5 Mei: model.ner = spaCy [active] | sources=S2-T5
S3-T2 Mei: model.sentiment = DistilBERT [active] | sources=S3-T2,S2-T3,S4-T1
S3-T3 Arun: metric.primary = macro-F1 [active] | sources=S3-T3,S3-T4
S4-T1 Mei: metric.primary = macro-F1 [proposed] | sources=S4-T1
```
