# report-c16 ("Moving to the New Flat"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (3 records)

```text
S1-T1 Bianca: move.containers = cardboard boxes [active] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [active] | sources=S1-T4,S1-T3
```

Shown for "What are we using to pack our belongings?" (`move.containers@S1`, a question about now):

```text
S1-T1 Bianca: move.containers = cardboard boxes [active] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [active] | sources=S1-T4,S1-T3
```

Shown for "What time is the van pickup?" (`van.pickup@S1`, a question about now):

```text
S1-T1 Bianca: move.containers = cardboard boxes [active] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [active] | sources=S1-T4,S1-T3
```

## After meeting 2 (S2): the whole memory (4 records)

```text
S1-T1 Bianca: move.containers = cardboard boxes [superseded] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [active] | sources=S1-T4,S1-T3
S2-T2 Bianca: move.containers = reusable plastic crates [active] | sources=S2-T2,S2-T4
```

Shown for "What are we using to pack our belongings?" (`move.containers@S2`, a question about now):

```text
S1-T1 Bianca: move.containers = cardboard boxes [superseded] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [active] | sources=S1-T4,S1-T3
S2-T2 Bianca: move.containers = reusable plastic crates [active] | sources=S2-T2,S2-T4
```

Shown for "What time is the van pickup?" (`van.pickup@S2`, a question about now):

```text
S1-T1 Bianca: move.containers = cardboard boxes [superseded] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [active] | sources=S1-T4,S1-T3
S2-T2 Bianca: move.containers = reusable plastic crates [active] | sources=S2-T2,S2-T4
```

## After meeting 3 (S3): the whole memory (4 records)

```text
S1-T1 Bianca: move.containers = cardboard boxes [superseded] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [active] | sources=S1-T4,S1-T3,S3-T4
S2-T2 Bianca: move.containers = reusable plastic crates [active] | sources=S2-T2,S2-T4
```

Shown for "What are we using to pack our belongings?" (`move.containers@S3`, a question about now):

```text
S1-T1 Bianca: move.containers = cardboard boxes [superseded] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [active] | sources=S1-T4,S1-T3,S3-T4
S2-T2 Bianca: move.containers = reusable plastic crates [active] | sources=S2-T2,S2-T4
```

Shown for "What time is the van pickup?" (`van.pickup@S3`, a question about now):

```text
S1-T1 Bianca: move.containers = cardboard boxes [superseded] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [active] | sources=S1-T4,S1-T3,S3-T4
S2-T2 Bianca: move.containers = reusable plastic crates [active] | sources=S2-T2,S2-T4
```

## After meeting 4 (S4): the whole memory (5 records)

```text
S1-T1 Bianca: move.containers = cardboard boxes [superseded] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [superseded] | sources=S1-T4,S1-T3,S3-T4
S2-T2 Bianca: move.containers = reusable plastic crates [active] | sources=S2-T2,S2-T4
S4-T2 Theo: van.pickup = 2 pm [active] | sources=S4-T2,S4-T3
```

Shown for "What are we using to pack our belongings?" (`move.containers@S4`, a question about now):

```text
S1-T1 Bianca: move.containers = cardboard boxes [superseded] | sources=S1-T1
S1-T4 Bianca: van.pickup = 10 am [superseded] | sources=S1-T4,S1-T3,S3-T4
S2-T2 Bianca: move.containers = reusable plastic crates [active] | sources=S2-T2,S2-T4
S4-T2 Theo: van.pickup = 2 pm [active] | sources=S4-T2,S4-T3
```

Shown for "Which containers, if any, did we use to pack our belongings before the current ones?" (`move.containers@S4-previous`, a question about the past):

```text
S1-T1 Bianca: move.containers = cardboard boxes [superseded] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [superseded] | sources=S1-T4,S1-T3,S3-T4
S2-T2 Bianca: move.containers = reusable plastic crates [active] | sources=S2-T2,S2-T4
S4-T2 Theo: van.pickup = 2 pm [active] | sources=S4-T2,S4-T3
```

Shown for "What time is the van pickup?" (`van.pickup@S4`, a question about now):

```text
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [superseded] | sources=S1-T4,S1-T3,S3-T4
S2-T2 Bianca: move.containers = reusable plastic crates [active] | sources=S2-T2,S2-T4
S4-T2 Theo: van.pickup = 2 pm [active] | sources=S4-T2,S4-T3
```

Shown for "Which pickup time, if any, did we book before the current one?" (`van.pickup@S4-previous`, a question about the past):

```text
S1-T1 Bianca: move.containers = cardboard boxes [superseded] | sources=S1-T1
S1-T3 Ravi: van.pickup = 10 am [superseded] | sources=S1-T3
S1-T4 Bianca: van.pickup = 10 am [superseded] | sources=S1-T4,S1-T3,S3-T4
S2-T2 Bianca: move.containers = reusable plastic crates [active] | sources=S2-T2,S2-T4
S4-T2 Theo: van.pickup = 2 pm [active] | sources=S4-T2,S4-T3
```
