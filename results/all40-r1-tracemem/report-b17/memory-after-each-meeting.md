# report-b17 ("The model might be recognising the hospital"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (3 records)

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1
S1-T3 Researcher: data.split = by patient [active] | sources=S1-T3
S1-T5 Researcher: metric.lead = AUROC [active] | sources=S1-T5
```

Shown for "How are we splitting the X-ray images into training, validation and test sets?" (`data.split@S1`, a question about now):

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1
S1-T3 Researcher: data.split = by patient [active] | sources=S1-T3
S1-T5 Researcher: metric.lead = AUROC [active] | sources=S1-T5
```

Shown for "Which metric leads the results table?" (`metric.lead@S1`, a question about now):

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1
S1-T3 Researcher: data.split = by patient [active] | sources=S1-T3
S1-T5 Researcher: metric.lead = AUROC [active] | sources=S1-T5
```

Shown for "Which model architecture are we using for the X-ray classifier?" (`model.architecture@S1`, a question about now):

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1
S1-T3 Researcher: data.split = by patient [active] | sources=S1-T3
S1-T5 Researcher: metric.lead = AUROC [active] | sources=S1-T5
```

## After meeting 2 (S2): the whole memory (6 records)

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1
S1-T3 Researcher: data.split = by patient [superseded] | sources=S1-T3
S1-T5 Researcher: metric.lead = AUROC [active] | sources=S1-T5
S2-T2 Agent: data.split = Hospital C held out for testing [superseded] | sources=S2-T2
S2-T3 Researcher: data.split = Hospital C held out for testing [active] | sources=S2-T3,S2-T2
S2-T4 Agent: model.architecture = vision transformer [proposed] | sources=S2-T4
```

Shown for "How are we splitting the X-ray images into training, validation and test sets?" (`data.split@S2`, a question about now):

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1
S1-T3 Researcher: data.split = by patient [superseded] | sources=S1-T3
S2-T2 Agent: data.split = Hospital C held out for testing [superseded] | sources=S2-T2
S2-T3 Researcher: data.split = Hospital C held out for testing [active] | sources=S2-T3,S2-T2
```

Shown for "Which metric leads the results table?" (`metric.lead@S2`, a question about now):

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1
S1-T3 Researcher: data.split = by patient [superseded] | sources=S1-T3
S1-T5 Researcher: metric.lead = AUROC [active] | sources=S1-T5
S2-T3 Researcher: data.split = Hospital C held out for testing [active] | sources=S2-T3,S2-T2
```

Shown for "Which model architecture are we using for the X-ray classifier?" (`model.architecture@S2`, a question about now):

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1
S1-T5 Researcher: metric.lead = AUROC [active] | sources=S1-T5
S2-T3 Researcher: data.split = Hospital C held out for testing [active] | sources=S2-T3,S2-T2
S2-T4 Agent: model.architecture = vision transformer [proposed] | sources=S2-T4
```

## After meeting 3 (S3): the whole memory (7 records)

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1,S3-T4
S1-T3 Researcher: data.split = by patient [superseded] | sources=S1-T3
S1-T5 Researcher: metric.lead = AUROC [active] | sources=S1-T5
S2-T2 Agent: data.split = Hospital C held out for testing [superseded] | sources=S2-T2
S2-T3 Researcher: data.split = Hospital C held out for testing [active] | sources=S2-T3,S2-T2
S2-T4 Agent: model.architecture = vision transformer [proposed] | sources=S2-T4
S3-T4 Agent: metric.lead = AUROC [proposed] | sources=S3-T4
```

Shown for "How are we splitting the X-ray images into training, validation and test sets?" (`data.split@S3`, a question about now):

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1,S3-T4
S1-T3 Researcher: data.split = by patient [superseded] | sources=S1-T3
S2-T2 Agent: data.split = Hospital C held out for testing [superseded] | sources=S2-T2
S2-T3 Researcher: data.split = Hospital C held out for testing [active] | sources=S2-T3,S2-T2
```

Shown for "Which way of splitting the X-ray images, if any, did we use before the current one?" (`data.split@S3-previous`, a question about the past):

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1,S3-T4
S1-T3 Researcher: data.split = by patient [superseded] | sources=S1-T3
S1-T5 Researcher: metric.lead = AUROC [active] | sources=S1-T5
S2-T2 Agent: data.split = Hospital C held out for testing [superseded] | sources=S2-T2
S2-T3 Researcher: data.split = Hospital C held out for testing [active] | sources=S2-T3,S2-T2
S2-T4 Agent: model.architecture = vision transformer [proposed] | sources=S2-T4
S3-T4 Agent: metric.lead = AUROC [proposed] | sources=S3-T4
```

Shown for "Which metric leads the results table?" (`metric.lead@S3`, a question about now):

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1,S3-T4
S1-T5 Researcher: metric.lead = AUROC [active] | sources=S1-T5
S2-T3 Researcher: data.split = Hospital C held out for testing [active] | sources=S2-T3,S2-T2
S3-T4 Agent: metric.lead = AUROC [proposed] | sources=S3-T4
```

Shown for "Which model architecture are we using for the X-ray classifier?" (`model.architecture@S3`, a question about now):

```text
S1-T1 Researcher: model.architecture = ResNet-18 [active] | sources=S1-T1,S3-T4
S1-T5 Researcher: metric.lead = AUROC [active] | sources=S1-T5
S2-T4 Agent: model.architecture = vision transformer [proposed] | sources=S2-T4
S3-T4 Agent: metric.lead = AUROC [proposed] | sources=S3-T4
```
