# mem0-instructions: memory after each meeting (pilot-01, Haiku, k = 4)

For each meeting: the whole memory after it, then, for each question about the present asked after it, the 4 lines the answering model was shown (k = 4: the 4 records closest to the question). A question about an earlier meeting or about history has its exact input in answerer-inputs.jsonl.

## After S1: the whole memory (6 records)

```text
S1-T1 Mei: model.sentiment = Current Mem0 memory: model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1) | sources=S1-T1
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1)"} | sources=S1-T1
S1-T2 Arun: metric.primary = Current Mem0 memory: Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2. | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2."} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 ("Yes, accuracy as the main metric for now."). | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 (\"Yes, accuracy as the main metric for now.\")."} | sources=S1-T3
```

Shown for `metric.primary@S1`:

```text
S1-T2 Arun: metric.primary = Current Mem0 memory: Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2. | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2."} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 ("Yes, accuracy as the main metric for now."). | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 (\"Yes, accuracy as the main metric for now.\")."} | sources=S1-T3
```

Shown for `model.sentiment@S1`:

```text
S1-T1 Mei: model.sentiment = Current Mem0 memory: model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1) | sources=S1-T1
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1)"} | sources=S1-T1
S1-T2 Arun: metric.primary = Current Mem0 memory: Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2. | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2."} | sources=S1-T2
```

## After S2: the whole memory (10 records)

```text
S1-T1 Mei: model.sentiment = Current Mem0 memory: model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1) | sources=S1-T1
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1)"} | sources=S1-T1
S1-T2 Arun: metric.primary = Current Mem0 memory: Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2. | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2."} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 ("Yes, accuracy as the main metric for now."). | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 (\"Yes, accuracy as the main metric for now.\")."} | sources=S1-T3
S2-T3 Arun: model.sentiment = Current Mem0 memory: model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT) | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT)"} | sources=S2-T3
S2-T5 Mei: model.ner = Current Mem0 memory: model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5) | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5)"} | sources=S2-T5
```

Shown for `metric.primary@S2`:

```text
S1-T2 Arun: metric.primary = Current Mem0 memory: Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2. | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2."} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 ("Yes, accuracy as the main metric for now."). | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 (\"Yes, accuracy as the main metric for now.\")."} | sources=S1-T3
```

Shown for `model.ner@S2`:

```text
S2-T3 Arun: model.sentiment = Current Mem0 memory: model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT) | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT)"} | sources=S2-T3
S2-T5 Mei: model.ner = Current Mem0 memory: model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5) | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5)"} | sources=S2-T5
```

Shown for `model.sentiment@S2`:

```text
S1-T1 Mei: model.sentiment = Current Mem0 memory: model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1) | sources=S1-T1
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1)"} | sources=S1-T1
S2-T3 Arun: model.sentiment = Current Mem0 memory: model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT) | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT)"} | sources=S2-T3
```

## After S3: the whole memory (15 records)

```text
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1)"} | sources=S1-T1
S1-T2 Arun: metric.primary = Current Mem0 memory: Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2. | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2."} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 ("Yes, accuracy as the main metric for now."). | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 (\"Yes, accuracy as the main metric for now.\")."} | sources=S1-T3
S2-T3 Arun: model.sentiment = Current Mem0 memory: model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT) | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT)"} | sources=S2-T3
S2-T5 Mei: model.ner = Current Mem0 memory: model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5) | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5)"} | sources=S2-T5
S3-T2 Mei: model.sentiment = Current Mem0 memory: model.sentiment = DistilBERT (committed by Mei for the sentiment classifier, project sentiment-project, source S3-T2; previous active version BERT, committed by Mei, source S1-T1) | sources=S3-T2,S1-T1
S3-T2 Mei: model.sentiment = {"mem0_history": "UPDATE", "before": "model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1)", "after": "model.sentiment = DistilBERT (committed by Mei for the sentiment classifier, project sentiment-project, source S3-T2; previous active version BERT, committed by Mei, source S1-T1)"} | sources=S3-T2,S1-T1
S3-T3 Arun: metric.primary = Current Mem0 memory: Proposed value for metric.primary (project sentiment-project): macro-F1. Not confirmed; suggested by Arun in S3-T3 ("Should we use macro-F1?"). | sources=S3-T3
S3-T3 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Proposed value for metric.primary (project sentiment-project): macro-F1. Not confirmed; suggested by Arun in S3-T3 (\"Should we use macro-F1?\")."} | sources=S3-T3
S3-T4 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): macro-F1. Committed by Mei in S3-T4 ("Agreed, macro-F1 is the primary metric from now on."). Supersedes previous active value accuracy (S1-T3). | sources=S3-T4
S3-T4 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Active value for metric.primary (project sentiment-project): macro-F1. Committed by Mei in S3-T4 (\"Agreed, macro-F1 is the primary metric from now on.\"). Supersedes previous active value accuracy (S1-T3)."} | sources=S3-T4
```

Shown for `metric.primary@S3`:

```text
S1-T2 Arun: metric.primary = Current Mem0 memory: Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2. | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 ("Yes, accuracy as the main metric for now."). | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 (\"Yes, accuracy as the main metric for now.\")."} | sources=S1-T3
S3-T4 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): macro-F1. Committed by Mei in S3-T4 ("Agreed, macro-F1 is the primary metric from now on."). Supersedes previous active value accuracy (S1-T3). | sources=S3-T4
```

Shown for `model.ner@S3`:

```text
S2-T3 Arun: model.sentiment = Current Mem0 memory: model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT) | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT)"} | sources=S2-T3
S2-T5 Mei: model.ner = Current Mem0 memory: model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5) | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5)"} | sources=S2-T5
```

Shown for `model.sentiment@S3`:

```text
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1)"} | sources=S1-T1
S2-T3 Arun: model.sentiment = Current Mem0 memory: model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT) | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT)"} | sources=S2-T3
S3-T2 Mei: model.sentiment = Current Mem0 memory: model.sentiment = DistilBERT (committed by Mei for the sentiment classifier, project sentiment-project, source S3-T2; previous active version BERT, committed by Mei, source S1-T1) | sources=S3-T2,S1-T1
```

Shown for `model.sentiment@S3-previous`:

```text
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1)"} | sources=S1-T1
S2-T3 Arun: model.sentiment = Current Mem0 memory: model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT) | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT)"} | sources=S2-T3
S3-T2 Mei: model.sentiment = Current Mem0 memory: model.sentiment = DistilBERT (committed by Mei for the sentiment classifier, project sentiment-project, source S3-T2; previous active version BERT, committed by Mei, source S1-T1) | sources=S3-T2,S1-T1
```

## After S4: the whole memory (15 records)

```text
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1)"} | sources=S1-T1
S1-T2 Arun: metric.primary = Current Mem0 memory: Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2. | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2."} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 ("Yes, accuracy as the main metric for now."). | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 (\"Yes, accuracy as the main metric for now.\")."} | sources=S1-T3
S2-T3 Arun: model.sentiment = Current Mem0 memory: model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT) | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT)"} | sources=S2-T3
S2-T5 Mei: model.ner = Current Mem0 memory: model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5) | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5)"} | sources=S2-T5
S3-T2 Mei: model.sentiment = Current Mem0 memory: model.sentiment = DistilBERT (committed by Mei for the sentiment classifier, project sentiment-project, source S3-T2; previous active version BERT, committed by Mei, source S1-T1) | sources=S3-T2,S1-T1
S3-T2 Mei: model.sentiment = {"mem0_history": "UPDATE", "before": "model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1)", "after": "model.sentiment = DistilBERT (committed by Mei for the sentiment classifier, project sentiment-project, source S3-T2; previous active version BERT, committed by Mei, source S1-T1)"} | sources=S3-T2,S1-T1
S3-T3 Arun: metric.primary = Current Mem0 memory: Proposed value for metric.primary (project sentiment-project): macro-F1. Not confirmed; suggested by Arun in S3-T3 ("Should we use macro-F1?"). | sources=S3-T3
S3-T3 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Proposed value for metric.primary (project sentiment-project): macro-F1. Not confirmed; suggested by Arun in S3-T3 (\"Should we use macro-F1?\")."} | sources=S3-T3
S3-T4 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): macro-F1. Committed by Mei in S3-T4 ("Agreed, macro-F1 is the primary metric from now on."). Supersedes previous active value accuracy (S1-T3). | sources=S3-T4
S3-T4 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Active value for metric.primary (project sentiment-project): macro-F1. Committed by Mei in S3-T4 (\"Agreed, macro-F1 is the primary metric from now on.\"). Supersedes previous active value accuracy (S1-T3)."} | sources=S3-T4
```

Shown for `metric.primary@S4`:

```text
S1-T2 Arun: metric.primary = Current Mem0 memory: Proposed value for metric.primary (project sentiment-project): accuracy. Not confirmed; raised as a question by Arun in S1-T2. | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 ("Yes, accuracy as the main metric for now."). | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "Active value for metric.primary (project sentiment-project): accuracy. Committed by Mei in S1-T3 (\"Yes, accuracy as the main metric for now.\")."} | sources=S1-T3
S3-T4 Mei: metric.primary = Current Mem0 memory: Active value for metric.primary (project sentiment-project): macro-F1. Committed by Mei in S3-T4 ("Agreed, macro-F1 is the primary metric from now on."). Supersedes previous active value accuracy (S1-T3). | sources=S3-T4
```

Shown for `model.ner@S4`:

```text
S2-T3 Arun: model.sentiment = Current Mem0 memory: model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT) | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT)"} | sources=S2-T3
S2-T5 Mei: model.ner = Current Mem0 memory: model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5) | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "model.ner = spaCy (for the NER part, we'll use a spaCy model; speaker: Mei; project: sentiment-project; candidate_id: model.ner@S2-T5)"} | sources=S2-T5
```

Shown for `model.sentiment@S4`:

```text
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment = BERT (committed by Mei for the sentiment classifier, project sentiment-project, source S1-T1)"} | sources=S1-T1
S2-T3 Arun: model.sentiment = Current Mem0 memory: model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT) | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "model.sentiment proposed = DistilBERT (proposed by Arun for project sentiment-project, source S2-T3, not adopted; current settled value remains BERT)"} | sources=S2-T3
S3-T2 Mei: model.sentiment = Current Mem0 memory: model.sentiment = DistilBERT (committed by Mei for the sentiment classifier, project sentiment-project, source S3-T2; previous active version BERT, committed by Mei, source S1-T1) | sources=S3-T2,S1-T1
```
