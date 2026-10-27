# similarity-recency: memory after each meeting (pilot-05, Haiku, freeze-deck settings, k = 4)

For each meeting: the whole memory after it, then, for each question about the present asked after it, the 4 lines the answering model was shown (k = 4: the 4 records closest to the question). A question about an earlier meeting or about history has its exact input in answerer-inputs.jsonl.

## After S1: the whole memory (3 records)

```text
S1-T1 Kai: model.baseline = logistic regression "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T1 Kai: features.text = TF-IDF "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
```

Shown for `features.text@S1`:

```text
S1-T1 Kai: features.text = TF-IDF "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T1 Kai: model.baseline = logistic regression "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
```

Shown for `model.baseline@S1`:

```text
S1-T1 Kai: features.text = TF-IDF "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T1 Kai: model.baseline = logistic regression "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
```

## After S2: the whole memory (3 records)

```text
S1-T1 Kai: model.baseline = logistic regression "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T1 Kai: features.text = TF-IDF "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
```

Shown for `features.text@S2`:

```text
S1-T1 Kai: features.text = TF-IDF "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T1 Kai: model.baseline = logistic regression "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
```

Shown for `model.baseline@S2`:

```text
S1-T1 Kai: features.text = TF-IDF "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T1 Kai: model.baseline = logistic regression "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
```

## After S3: the whole memory (5 records)

```text
S1-T1 Kai: model.baseline = logistic regression "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T1 Kai: features.text = TF-IDF "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
S3-T1 Kai: model.baseline = linear SVM "I ran it: the linear SVM beats logistic regression by two points. Let's make the SVM our baseline." | sources=S3-T1
S3-T2 Rosa: model.baseline = linear SVM "OK, SVM it is." | sources=S3-T2
```

Shown for `features.text@S3`:

```text
S1-T1 Kai: features.text = TF-IDF "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
S3-T1 Kai: model.baseline = linear SVM "I ran it: the linear SVM beats logistic regression by two points. Let's make the SVM our baseline." | sources=S3-T1
S3-T2 Rosa: model.baseline = linear SVM "OK, SVM it is." | sources=S3-T2
```

Shown for `model.baseline@S3`:

```text
S1-T1 Kai: model.baseline = logistic regression "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
S3-T1 Kai: model.baseline = linear SVM "I ran it: the linear SVM beats logistic regression by two points. Let's make the SVM our baseline." | sources=S3-T1
S3-T2 Rosa: model.baseline = linear SVM "OK, SVM it is." | sources=S3-T2
```

Shown for `model.baseline@S3-previous`:

```text
S1-T1 Kai: model.baseline = logistic regression "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
S3-T1 Kai: model.baseline = linear SVM "I ran it: the linear SVM beats logistic regression by two points. Let's make the SVM our baseline." | sources=S3-T1
S3-T2 Rosa: model.baseline = linear SVM "OK, SVM it is." | sources=S3-T2
```

## After S4: the whole memory (5 records)

```text
S1-T1 Kai: model.baseline = logistic regression "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T1 Kai: features.text = TF-IDF "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
S3-T1 Kai: model.baseline = linear SVM "I ran it: the linear SVM beats logistic regression by two points. Let's make the SVM our baseline." | sources=S3-T1
S3-T2 Rosa: model.baseline = linear SVM "OK, SVM it is." | sources=S3-T2
```

Shown for `features.text@S4`:

```text
S1-T1 Kai: features.text = TF-IDF "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
S3-T1 Kai: model.baseline = linear SVM "I ran it: the linear SVM beats logistic regression by two points. Let's make the SVM our baseline." | sources=S3-T1
S3-T2 Rosa: model.baseline = linear SVM "OK, SVM it is." | sources=S3-T2
```

Shown for `model.baseline@S4`:

```text
S1-T1 Kai: model.baseline = logistic regression "Let's make the baseline logistic regression on TF-IDF features." | sources=S1-T1
S1-T2 Rosa: model.baseline = naive Bayes "What if we used naive Bayes instead? It's the classic for spam." | sources=S1-T2
S3-T1 Kai: model.baseline = linear SVM "I ran it: the linear SVM beats logistic regression by two points. Let's make the SVM our baseline." | sources=S3-T1
S3-T2 Rosa: model.baseline = linear SVM "OK, SVM it is." | sources=S3-T2
```
