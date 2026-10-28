# deck-b04 ("A restaurant question is mistaken for a booking change"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer). This scenario has no question about the past.

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (3 records)

```text
S1-T2 Max: dinner.restaurant = Cedar Kitchen [active] | sources=S1-T2
S1-T3 Lina: dinner.time = 7 pm [superseded] | sources=S1-T3
S1-T4 Max: dinner.time = 7 pm [active] | sources=S1-T4,S1-T3
```

Shown for "Which restaurant is selected for the birthday dinner?" (`dinner.restaurant@S1`, a question about now):

```text
S1-T2 Max: dinner.restaurant = Cedar Kitchen [active] | sources=S1-T2
S1-T3 Lina: dinner.time = 7 pm [superseded] | sources=S1-T3
S1-T4 Max: dinner.time = 7 pm [active] | sources=S1-T4,S1-T3
```

Shown for "What time is the birthday dinner?" (`dinner.time@S1`, a question about now):

```text
S1-T2 Max: dinner.restaurant = Cedar Kitchen [active] | sources=S1-T2
S1-T3 Lina: dinner.time = 7 pm [superseded] | sources=S1-T3
S1-T4 Max: dinner.time = 7 pm [active] | sources=S1-T4,S1-T3
```

## After meeting 2 (S2): the whole memory (3 records)

```text
S1-T2 Max: dinner.restaurant = Cedar Kitchen [active] | sources=S1-T2,S2-T4
S1-T3 Lina: dinner.time = 7 pm [superseded] | sources=S1-T3
S1-T4 Max: dinner.time = 7 pm [active] | sources=S1-T4,S1-T3
```

Shown for "Which restaurant is selected for the birthday dinner?" (`dinner.restaurant@S2`, a question about now):

```text
S1-T2 Max: dinner.restaurant = Cedar Kitchen [active] | sources=S1-T2,S2-T4
S1-T3 Lina: dinner.time = 7 pm [superseded] | sources=S1-T3
S1-T4 Max: dinner.time = 7 pm [active] | sources=S1-T4,S1-T3
```

Shown for "What time is the birthday dinner?" (`dinner.time@S2`, a question about now):

```text
S1-T2 Max: dinner.restaurant = Cedar Kitchen [active] | sources=S1-T2,S2-T4
S1-T3 Lina: dinner.time = 7 pm [superseded] | sources=S1-T3
S1-T4 Max: dinner.time = 7 pm [active] | sources=S1-T4,S1-T3
```

## After meeting 3 (S3): the whole memory (3 records)

```text
S1-T2 Max: dinner.restaurant = Cedar Kitchen [active] | sources=S1-T2,S2-T4,S3-T4
S1-T3 Lina: dinner.time = 7 pm [superseded] | sources=S1-T3
S1-T4 Max: dinner.time = 7 pm [active] | sources=S1-T4,S1-T3,S3-T2
```

Shown for "Which restaurant is selected for the birthday dinner?" (`dinner.restaurant@S3`, a question about now):

```text
S1-T2 Max: dinner.restaurant = Cedar Kitchen [active] | sources=S1-T2,S2-T4,S3-T4
S1-T3 Lina: dinner.time = 7 pm [superseded] | sources=S1-T3
S1-T4 Max: dinner.time = 7 pm [active] | sources=S1-T4,S1-T3,S3-T2
```

Shown for "What time is the birthday dinner?" (`dinner.time@S3`, a question about now):

```text
S1-T2 Max: dinner.restaurant = Cedar Kitchen [active] | sources=S1-T2,S2-T4,S3-T4
S1-T3 Lina: dinner.time = 7 pm [superseded] | sources=S1-T3
S1-T4 Max: dinner.time = 7 pm [active] | sources=S1-T4,S1-T3,S3-T2
```
