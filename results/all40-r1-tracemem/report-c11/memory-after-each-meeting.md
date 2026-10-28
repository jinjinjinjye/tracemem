# report-c11 ("A Neighbourhood Book Swap"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (3 records)

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S1-T4 Iris: swap.label_colour = blue [active] | sources=S1-T4,S1-T3
```

Shown for "What colour exchange labels are we using?" (`swap.label_colour@S1`, a question about now):

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S1-T4 Iris: swap.label_colour = blue [active] | sources=S1-T4,S1-T3
```

Shown for "Where are we holding the book swap?" (`swap.venue@S1`, a question about now):

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S1-T4 Iris: swap.label_colour = blue [active] | sources=S1-T4,S1-T3
```

## After meeting 2 (S2): the whole memory (4 records)

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S1-T4 Iris: swap.label_colour = blue [active] | sources=S1-T4,S1-T3
S2-T1 Felix: swap.venue = courtyard [proposed] | sources=S2-T1
```

Shown for "What colour exchange labels are we using?" (`swap.label_colour@S2`, a question about now):

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S1-T4 Iris: swap.label_colour = blue [active] | sources=S1-T4,S1-T3
S2-T1 Felix: swap.venue = courtyard [proposed] | sources=S2-T1
```

Shown for "Where are we holding the book swap?" (`swap.venue@S2`, a question about now):

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S1-T4 Iris: swap.label_colour = blue [active] | sources=S1-T4,S1-T3
S2-T1 Felix: swap.venue = courtyard [proposed] | sources=S2-T1
```

## After meeting 3 (S3): the whole memory (5 records)

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S1-T4 Iris: swap.label_colour = blue [active] | sources=S1-T4,S1-T3
S2-T1 Felix: swap.venue = courtyard [proposed] | sources=S2-T1
S3-T3 Felix: swap.venue = courtyard [proposed] | sources=S3-T3
```

Shown for "What colour exchange labels are we using?" (`swap.label_colour@S3`, a question about now):

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S1-T4 Iris: swap.label_colour = blue [active] | sources=S1-T4,S1-T3
S2-T1 Felix: swap.venue = courtyard [proposed] | sources=S2-T1
```

Shown for "Where are we holding the book swap?" (`swap.venue@S3`, a question about now):

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S2-T1 Felix: swap.venue = courtyard [proposed] | sources=S2-T1
S3-T3 Felix: swap.venue = courtyard [proposed] | sources=S3-T3
```

## After meeting 4 (S4): the whole memory (7 records)

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S1-T4 Iris: swap.label_colour = blue [superseded] | sources=S1-T4,S1-T3
S2-T1 Felix: swap.venue = courtyard [proposed] | sources=S2-T1
S3-T3 Felix: swap.venue = courtyard [proposed] | sources=S3-T3
S4-T1 Dalia: swap.label_colour = yellow [superseded] | sources=S4-T1
S4-T2 Iris: swap.label_colour = yellow [active] | sources=S4-T2,S4-T1,S4-T4
```

Shown for "What colour exchange labels are we using?" (`swap.label_colour@S4`, a question about now):

```text
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S1-T4 Iris: swap.label_colour = blue [superseded] | sources=S1-T4,S1-T3
S4-T1 Dalia: swap.label_colour = yellow [superseded] | sources=S4-T1
S4-T2 Iris: swap.label_colour = yellow [active] | sources=S4-T2,S4-T1,S4-T4
```

Shown for "Which label colour, if any, did we use before the current one?" (`swap.label_colour@S4-previous`, a question about the past):

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S1-T4 Iris: swap.label_colour = blue [superseded] | sources=S1-T4,S1-T3
S2-T1 Felix: swap.venue = courtyard [proposed] | sources=S2-T1
S3-T3 Felix: swap.venue = courtyard [proposed] | sources=S3-T3
S4-T1 Dalia: swap.label_colour = yellow [superseded] | sources=S4-T1
S4-T2 Iris: swap.label_colour = yellow [active] | sources=S4-T2,S4-T1,S4-T4
```

Shown for "Where are we holding the book swap?" (`swap.venue@S4`, a question about now):

```text
S1-T1 Iris: swap.venue = community lounge [active] | sources=S1-T1
S1-T3 Dalia: swap.label_colour = blue [superseded] | sources=S1-T3
S2-T1 Felix: swap.venue = courtyard [proposed] | sources=S2-T1
S3-T3 Felix: swap.venue = courtyard [proposed] | sources=S3-T3
```
