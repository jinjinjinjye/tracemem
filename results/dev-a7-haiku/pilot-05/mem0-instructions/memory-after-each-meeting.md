# mem0-instructions: memory after each meeting (pilot-05, Haiku, freeze-deck settings, k = 4)

For each meeting: the whole memory after it, then, for each question about the present asked after it, the 4 lines the answering model was shown (k = 4: the 4 records closest to the question). A question about an earlier meeting or about history has its exact input in answerer-inputs.jsonl.

## After S1: the whole memory (6 records)

```text
S1-T1 Kai: features.text = Current Mem0 memory: spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active) | sources=S1-T1
S1-T1 Kai: model.baseline = Current Mem0 memory: Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai) | sources=S1-T1
S1-T1 Kai: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)"} | sources=S1-T1
S1-T1 Kai: features.text = {"mem0_history": "ADD", "before": null, "after": "spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S1-T2 Rosa: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2)"} | sources=S1-T2
```

Shown for `features.text@S1`:

```text
S1-T1 Kai: features.text = Current Mem0 memory: spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active) | sources=S1-T1
S1-T1 Kai: features.text = {"mem0_history": "ADD", "before": null, "after": "spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S1-T2 Rosa: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2)"} | sources=S1-T2
```

Shown for `model.baseline@S1`:

```text
S1-T1 Kai: model.baseline = Current Mem0 memory: Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai) | sources=S1-T1
S1-T1 Kai: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S1-T2 Rosa: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2)"} | sources=S1-T2
```

## After S2: the whole memory (6 records)

```text
S1-T1 Kai: features.text = Current Mem0 memory: spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active) | sources=S1-T1
S1-T1 Kai: model.baseline = Current Mem0 memory: Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai) | sources=S1-T1
S1-T1 Kai: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)"} | sources=S1-T1
S1-T1 Kai: features.text = {"mem0_history": "ADD", "before": null, "after": "spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S1-T2 Rosa: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2)"} | sources=S1-T2
```

Shown for `features.text@S2`:

```text
S1-T1 Kai: features.text = Current Mem0 memory: spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active) | sources=S1-T1
S1-T1 Kai: features.text = {"mem0_history": "ADD", "before": null, "after": "spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S1-T2 Rosa: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2)"} | sources=S1-T2
```

Shown for `model.baseline@S2`:

```text
S1-T1 Kai: model.baseline = Current Mem0 memory: Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai) | sources=S1-T1
S1-T1 Kai: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S1-T2 Rosa: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2)"} | sources=S1-T2
```

## After S3: the whole memory (7 records)

```text
S1-T1 Kai: features.text = Current Mem0 memory: spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active) | sources=S1-T1
S1-T1 Kai: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)"} | sources=S1-T1
S1-T1 Kai: features.text = {"mem0_history": "ADD", "before": null, "after": "spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S1-T2 Rosa: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2)"} | sources=S1-T2
S3-T1 Kai: model.baseline = Current Mem0 memory: Baseline model (model.baseline) for project spam-filter is linear SVM (decided by Kai); previous active version: logistic regression on TF-IDF features | sources=S3-T1,S1-T1
S3-T1 Kai: model.baseline = {"mem0_history": "UPDATE", "before": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)", "after": "Baseline model (model.baseline) for project spam-filter is linear SVM (decided by Kai); previous active version: logistic regression on TF-IDF features"} | sources=S3-T1,S1-T1
```

Shown for `features.text@S3`:

```text
S1-T1 Kai: features.text = Current Mem0 memory: spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active) | sources=S1-T1
S1-T1 Kai: features.text = {"mem0_history": "ADD", "before": null, "after": "spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S1-T2 Rosa: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2)"} | sources=S1-T2
```

Shown for `model.baseline@S3`:

```text
S1-T1 Kai: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S3-T1 Kai: model.baseline = Current Mem0 memory: Baseline model (model.baseline) for project spam-filter is linear SVM (decided by Kai); previous active version: logistic regression on TF-IDF features | sources=S3-T1,S1-T1
S3-T1 Kai: model.baseline = {"mem0_history": "UPDATE", "before": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)", "after": "Baseline model (model.baseline) for project spam-filter is linear SVM (decided by Kai); previous active version: logistic regression on TF-IDF features"} | sources=S3-T1,S1-T1
```

Shown for `model.baseline@S3-previous`:

```text
S1-T1 Kai: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S1-T2 Rosa: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2)"} | sources=S1-T2
S3-T1 Kai: model.baseline = Current Mem0 memory: Baseline model (model.baseline) for project spam-filter is linear SVM (decided by Kai); previous active version: logistic regression on TF-IDF features | sources=S3-T1,S1-T1
```

## After S4: the whole memory (7 records)

```text
S1-T1 Kai: features.text = Current Mem0 memory: spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active) | sources=S1-T1
S1-T1 Kai: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)"} | sources=S1-T1
S1-T1 Kai: features.text = {"mem0_history": "ADD", "before": null, "after": "spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S1-T2 Rosa: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2)"} | sources=S1-T2
S3-T1 Kai: model.baseline = Current Mem0 memory: Baseline model (model.baseline) for project spam-filter is linear SVM (decided by Kai); previous active version: logistic regression on TF-IDF features | sources=S3-T1,S1-T1
S3-T1 Kai: model.baseline = {"mem0_history": "UPDATE", "before": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)", "after": "Baseline model (model.baseline) for project spam-filter is linear SVM (decided by Kai); previous active version: logistic regression on TF-IDF features"} | sources=S3-T1,S1-T1
```

Shown for `features.text@S4`:

```text
S1-T1 Kai: features.text = Current Mem0 memory: spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active) | sources=S1-T1
S1-T1 Kai: features.text = {"mem0_history": "ADD", "before": null, "after": "spam-filter project: features.text is TF-IDF for the baseline logistic regression (set by Kai, active)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S1-T2 Rosa: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2)"} | sources=S1-T2
```

Shown for `model.baseline@S4`:

```text
S1-T1 Kai: model.baseline = {"mem0_history": "ADD", "before": null, "after": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)"} | sources=S1-T1
S1-T2 Rosa: model.baseline = Current Mem0 memory: Proposed (not adopted): model.baseline for project spam-filter could be naive Bayes instead (suggested by Rosa, source turn S1-T2) | sources=S1-T2
S3-T1 Kai: model.baseline = Current Mem0 memory: Baseline model (model.baseline) for project spam-filter is linear SVM (decided by Kai); previous active version: logistic regression on TF-IDF features | sources=S3-T1,S1-T1
S3-T1 Kai: model.baseline = {"mem0_history": "UPDATE", "before": "Baseline model (model.baseline) for project spam-filter is logistic regression on TF-IDF features (decided by Kai)", "after": "Baseline model (model.baseline) for project spam-filter is linear SVM (decided by Kai); previous active version: logistic regression on TF-IDF features"} | sources=S3-T1,S1-T1
```
