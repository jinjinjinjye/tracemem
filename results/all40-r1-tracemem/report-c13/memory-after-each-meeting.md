# report-c13 ("Two Herbs on the Balcony"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (2 records)

```text
S1-T1 Elena: pot.basil = terracotta pot [active] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [active] | sources=S1-T3,S1-T4
```

Shown for "Which pot is assigned to the basil?" (`pot.basil@S1`, a question about now):

```text
S1-T1 Elena: pot.basil = terracotta pot [active] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [active] | sources=S1-T3,S1-T4
```

Shown for "Which pot is assigned to the mint?" (`pot.mint@S1`, a question about now):

```text
S1-T1 Elena: pot.basil = terracotta pot [active] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [active] | sources=S1-T3,S1-T4
```

## After meeting 2 (S2): the whole memory (2 records)

```text
S1-T1 Elena: pot.basil = terracotta pot [active] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [active] | sources=S1-T3,S1-T4
```

Shown for "Which pot is assigned to the basil?" (`pot.basil@S2`, a question about now):

```text
S1-T1 Elena: pot.basil = terracotta pot [active] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [active] | sources=S1-T3,S1-T4
```

Shown for "Which pot is assigned to the mint?" (`pot.mint@S2`, a question about now):

```text
S1-T1 Elena: pot.basil = terracotta pot [active] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [active] | sources=S1-T3,S1-T4
```

## After meeting 3 (S3): the whole memory (3 records)

```text
S1-T1 Elena: pot.basil = terracotta pot [active] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [superseded] | sources=S1-T3,S1-T4
S3-T2 Yuki: pot.mint = white pot [active] | sources=S3-T2,S3-T4
```

Shown for "Which pot is assigned to the basil?" (`pot.basil@S3`, a question about now):

```text
S1-T1 Elena: pot.basil = terracotta pot [active] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [superseded] | sources=S1-T3,S1-T4
S3-T2 Yuki: pot.mint = white pot [active] | sources=S3-T2,S3-T4
```

Shown for "Which pot is assigned to the mint?" (`pot.mint@S3`, a question about now):

```text
S1-T1 Elena: pot.basil = terracotta pot [active] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [superseded] | sources=S1-T3,S1-T4
S3-T2 Yuki: pot.mint = white pot [active] | sources=S3-T2,S3-T4
```

## After meeting 4 (S4): the whole memory (5 records)

```text
S1-T1 Elena: pot.basil = terracotta pot [superseded] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [superseded] | sources=S1-T3,S1-T4
S3-T2 Yuki: pot.mint = white pot [active] | sources=S3-T2,S3-T4
S4-T2 Marcus: pot.basil = cobalt-blue pot [superseded] | sources=S4-T2
S4-T3 Yuki: pot.basil = cobalt-blue pot [active] | sources=S4-T3,S4-T2,S4-T4
```

Shown for "Which pot is assigned to the basil?" (`pot.basil@S4`, a question about now):

```text
S1-T1 Elena: pot.basil = terracotta pot [superseded] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [superseded] | sources=S1-T3,S1-T4
S4-T2 Marcus: pot.basil = cobalt-blue pot [superseded] | sources=S4-T2
S4-T3 Yuki: pot.basil = cobalt-blue pot [active] | sources=S4-T3,S4-T2,S4-T4
```

Shown for "Which pot is assigned to the mint?" (`pot.mint@S4`, a question about now):

```text
S1-T1 Elena: pot.basil = terracotta pot [superseded] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [superseded] | sources=S1-T3,S1-T4
S3-T2 Yuki: pot.mint = white pot [active] | sources=S3-T2,S3-T4
S4-T2 Marcus: pot.basil = cobalt-blue pot [superseded] | sources=S4-T2
```

## After meeting 5 (S5): the whole memory (6 records)

```text
S1-T1 Elena: pot.basil = terracotta pot [superseded] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [superseded] | sources=S1-T3,S1-T4
S3-T2 Yuki: pot.mint = white pot [active] | sources=S3-T2,S3-T4
S4-T2 Marcus: pot.basil = cobalt-blue pot [superseded] | sources=S4-T2
S4-T3 Yuki: pot.basil = cobalt-blue pot [active] | sources=S4-T3,S4-T2,S4-T4,S5-T3,S5-T4
S5-T1 Yuki: pot.mint = white pot [proposed] | sources=S5-T1
```

Shown for "Which pot is assigned to the basil?" (`pot.basil@S5`, a question about now):

```text
S1-T1 Elena: pot.basil = terracotta pot [superseded] | sources=S1-T1,S1-T4
S4-T2 Marcus: pot.basil = cobalt-blue pot [superseded] | sources=S4-T2
S4-T3 Yuki: pot.basil = cobalt-blue pot [active] | sources=S4-T3,S4-T2,S4-T4,S5-T3,S5-T4
S5-T1 Yuki: pot.mint = white pot [proposed] | sources=S5-T1
```

Shown for "Which pot, if any, did we use for the basil before the current one?" (`pot.basil@S5-previous`, a question about the past):

```text
S1-T1 Elena: pot.basil = terracotta pot [superseded] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [superseded] | sources=S1-T3,S1-T4
S3-T2 Yuki: pot.mint = white pot [active] | sources=S3-T2,S3-T4
S4-T2 Marcus: pot.basil = cobalt-blue pot [superseded] | sources=S4-T2
S4-T3 Yuki: pot.basil = cobalt-blue pot [active] | sources=S4-T3,S4-T2,S4-T4,S5-T3,S5-T4
S5-T1 Yuki: pot.mint = white pot [proposed] | sources=S5-T1
```

Shown for "Which pot is assigned to the mint?" (`pot.mint@S5`, a question about now):

```text
S1-T3 Yuki: pot.mint = green pot [superseded] | sources=S1-T3,S1-T4
S3-T2 Yuki: pot.mint = white pot [active] | sources=S3-T2,S3-T4
S4-T2 Marcus: pot.basil = cobalt-blue pot [superseded] | sources=S4-T2
S5-T1 Yuki: pot.mint = white pot [proposed] | sources=S5-T1
```

Shown for "Which pot, if any, did we use for the mint before the current one?" (`pot.mint@S5-previous`, a question about the past):

```text
S1-T1 Elena: pot.basil = terracotta pot [superseded] | sources=S1-T1,S1-T4
S1-T3 Yuki: pot.mint = green pot [superseded] | sources=S1-T3,S1-T4
S3-T2 Yuki: pot.mint = white pot [active] | sources=S3-T2,S3-T4
S4-T2 Marcus: pot.basil = cobalt-blue pot [superseded] | sources=S4-T2
S4-T3 Yuki: pot.basil = cobalt-blue pot [active] | sources=S4-T3,S4-T2,S4-T4,S5-T3,S5-T4
S5-T1 Yuki: pot.mint = white pot [proposed] | sources=S5-T1
```
