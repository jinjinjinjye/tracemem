# deck-b07 ("Two school fair deadlines must stay separate"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (6 records)

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1
S1-T2 Noah: deadline.craft_booth = 6 November [active] | sources=S1-T2
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S1-T4 Mira: fee.craft_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.food_booth = SGD 20 [active] | sources=S1-T5,S1-T4
S1-T5 Noah: fee.craft_booth = SGD 20 [active] | sources=S1-T5,S1-T4
```

Shown for "What is the craft-booth form deadline?" (`deadline.craft_booth@S1`, a question about now):

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1
S1-T2 Noah: deadline.craft_booth = 6 November [active] | sources=S1-T2
S1-T4 Mira: fee.craft_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.craft_booth = SGD 20 [active] | sources=S1-T5,S1-T4
```

Shown for "What is the food-booth form deadline?" (`deadline.food_booth@S1`, a question about now):

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1
S1-T2 Noah: deadline.craft_booth = 6 November [active] | sources=S1-T2
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.food_booth = SGD 20 [active] | sources=S1-T5,S1-T4
```

Shown for "What is the fee per session for the craft booth?" (`fee.craft_booth@S1`, a question about now):

```text
S1-T2 Noah: deadline.craft_booth = 6 November [active] | sources=S1-T2
S1-T4 Mira: fee.craft_booth = SGD 20 [superseded] | sources=S1-T4
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.craft_booth = SGD 20 [active] | sources=S1-T5,S1-T4
```

Shown for "What is the fee per session for the food booth?" (`fee.food_booth@S1`, a question about now):

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.craft_booth = SGD 20 [active] | sources=S1-T5,S1-T4
S1-T5 Noah: fee.food_booth = SGD 20 [active] | sources=S1-T5,S1-T4
```

## After meeting 2 (S2): the whole memory (7 records)

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1,S2-T3
S1-T2 Noah: deadline.craft_booth = 6 November [superseded] | sources=S1-T2
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S1-T4 Mira: fee.craft_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.food_booth = SGD 20 [active] | sources=S1-T5,S1-T4
S1-T5 Noah: fee.craft_booth = SGD 20 [active] | sources=S1-T5,S1-T4
S2-T1 Noah: deadline.craft_booth = 9 November [active] | sources=S2-T1
```

Shown for "What is the craft-booth form deadline?" (`deadline.craft_booth@S2`, a question about now):

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1,S2-T3
S1-T2 Noah: deadline.craft_booth = 6 November [superseded] | sources=S1-T2
S1-T4 Mira: fee.craft_booth = SGD 20 [superseded] | sources=S1-T4
S2-T1 Noah: deadline.craft_booth = 9 November [active] | sources=S2-T1
```

Shown for "What is the food-booth form deadline?" (`deadline.food_booth@S2`, a question about now):

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1,S2-T3
S1-T2 Noah: deadline.craft_booth = 6 November [superseded] | sources=S1-T2
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S2-T1 Noah: deadline.craft_booth = 9 November [active] | sources=S2-T1
```

Shown for "What is the fee per session for the craft booth?" (`fee.craft_booth@S2`, a question about now):

```text
S1-T2 Noah: deadline.craft_booth = 6 November [superseded] | sources=S1-T2
S1-T4 Mira: fee.craft_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.craft_booth = SGD 20 [active] | sources=S1-T5,S1-T4
S2-T1 Noah: deadline.craft_booth = 9 November [active] | sources=S2-T1
```

Shown for "What is the fee per session for the food booth?" (`fee.food_booth@S2`, a question about now):

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1,S2-T3
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.craft_booth = SGD 20 [active] | sources=S1-T5,S1-T4
S1-T5 Noah: fee.food_booth = SGD 20 [active] | sources=S1-T5,S1-T4
```

## After meeting 3 (S3): the whole memory (8 records)

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1,S2-T3
S1-T2 Noah: deadline.craft_booth = 6 November [superseded] | sources=S1-T2
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S1-T4 Mira: fee.craft_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.food_booth = SGD 20 [superseded] | sources=S1-T5,S1-T4
S1-T5 Noah: fee.craft_booth = SGD 20 [active] | sources=S1-T5,S1-T4
S2-T1 Noah: deadline.craft_booth = 9 November [active] | sources=S2-T1
S3-T4 Mira: fee.food_booth = SGD 30 [active] | sources=S3-T4
```

Shown for "What is the craft-booth form deadline?" (`deadline.craft_booth@S3`, a question about now):

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1,S2-T3
S1-T2 Noah: deadline.craft_booth = 6 November [superseded] | sources=S1-T2
S1-T4 Mira: fee.craft_booth = SGD 20 [superseded] | sources=S1-T4
S2-T1 Noah: deadline.craft_booth = 9 November [active] | sources=S2-T1
```

Shown for "Which craft-booth form deadline, if any, did we have before the current one?" (`deadline.craft_booth@S3-previous`, a question about the past):

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1,S2-T3
S1-T2 Noah: deadline.craft_booth = 6 November [superseded] | sources=S1-T2
S1-T4 Mira: fee.craft_booth = SGD 20 [superseded] | sources=S1-T4
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.craft_booth = SGD 20 [active] | sources=S1-T5,S1-T4
S1-T5 Noah: fee.food_booth = SGD 20 [superseded] | sources=S1-T5,S1-T4
S2-T1 Noah: deadline.craft_booth = 9 November [active] | sources=S2-T1
S3-T4 Mira: fee.food_booth = SGD 30 [active] | sources=S3-T4
```

Shown for "What is the food-booth form deadline?" (`deadline.food_booth@S3`, a question about now):

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1,S2-T3
S1-T2 Noah: deadline.craft_booth = 6 November [superseded] | sources=S1-T2
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S2-T1 Noah: deadline.craft_booth = 9 November [active] | sources=S2-T1
```

Shown for "What is the fee per session for the craft booth?" (`fee.craft_booth@S3`, a question about now):

```text
S1-T2 Noah: deadline.craft_booth = 6 November [superseded] | sources=S1-T2
S1-T4 Mira: fee.craft_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.craft_booth = SGD 20 [active] | sources=S1-T5,S1-T4
S2-T1 Noah: deadline.craft_booth = 9 November [active] | sources=S2-T1
```

Shown for "What is the fee per session for the food booth?" (`fee.food_booth@S3`, a question about now):

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1,S2-T3
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.food_booth = SGD 20 [superseded] | sources=S1-T5,S1-T4
S3-T4 Mira: fee.food_booth = SGD 30 [active] | sources=S3-T4
```

Shown for "Which food-booth fee, if any, did we charge before the current one?" (`fee.food_booth@S3-previous`, a question about the past):

```text
S1-T1 Mira: deadline.food_booth = 4 November [active] | sources=S1-T1,S2-T3
S1-T2 Noah: deadline.craft_booth = 6 November [superseded] | sources=S1-T2
S1-T4 Mira: fee.craft_booth = SGD 20 [superseded] | sources=S1-T4
S1-T4 Mira: fee.food_booth = SGD 20 [superseded] | sources=S1-T4
S1-T5 Noah: fee.craft_booth = SGD 20 [active] | sources=S1-T5,S1-T4
S1-T5 Noah: fee.food_booth = SGD 20 [superseded] | sources=S1-T5,S1-T4
S2-T1 Noah: deadline.craft_booth = 9 November [active] | sources=S2-T1
S3-T4 Mira: fee.food_booth = SGD 30 [active] | sources=S3-T4
```
