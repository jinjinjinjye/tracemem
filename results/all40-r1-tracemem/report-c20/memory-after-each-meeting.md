# report-c20 ("Tote Bags for the Community Stall"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (3 records)

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [active] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
```

Shown for "What fabric are we using for the tote bags?" (`tote.fabric@S1`, a question about now):

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [active] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
```

Shown for "What colour handles are we using for the tote bags?" (`tote.handle_colour@S1`, a question about now):

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [active] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
```

## After meeting 2 (S2): the whole memory (4 records)

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [superseded] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
S2-T2 Rosa: tote.fabric = canvas [active] | sources=S2-T2,S2-T3,S2-T4
```

Shown for "What fabric are we using for the tote bags?" (`tote.fabric@S2`, a question about now):

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [superseded] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
S2-T2 Rosa: tote.fabric = canvas [active] | sources=S2-T2,S2-T3,S2-T4
```

Shown for "What colour handles are we using for the tote bags?" (`tote.handle_colour@S2`, a question about now):

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [superseded] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
S2-T2 Rosa: tote.fabric = canvas [active] | sources=S2-T2,S2-T3,S2-T4
```

## After meeting 3 (S3): the whole memory (4 records)

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [superseded] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
S2-T2 Rosa: tote.fabric = canvas [active] | sources=S2-T2,S2-T3,S2-T4
```

Shown for "What fabric are we using for the tote bags?" (`tote.fabric@S3`, a question about now):

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [superseded] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
S2-T2 Rosa: tote.fabric = canvas [active] | sources=S2-T2,S2-T3,S2-T4
```

Shown for "What colour handles are we using for the tote bags?" (`tote.handle_colour@S3`, a question about now):

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [superseded] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
S2-T2 Rosa: tote.fabric = canvas [active] | sources=S2-T2,S2-T3,S2-T4
```

## After meeting 4 (S4): the whole memory (6 records)

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [superseded] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
S2-T2 Rosa: tote.fabric = canvas [active] | sources=S2-T2,S2-T3,S2-T4
S4-T1 Sienna: tote.fabric = canvas [proposed] | sources=S4-T1
S4-T1 Sienna: tote.handle_colour = navy blue [proposed] | sources=S4-T1
```

Shown for "What fabric are we using for the tote bags?" (`tote.fabric@S4`, a question about now):

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [superseded] | sources=S1-T1,S1-T4
S2-T2 Rosa: tote.fabric = canvas [active] | sources=S2-T2,S2-T3,S2-T4
S4-T1 Sienna: tote.fabric = canvas [proposed] | sources=S4-T1
S4-T1 Sienna: tote.handle_colour = navy blue [proposed] | sources=S4-T1
```

Shown for "What colour handles are we using for the tote bags?" (`tote.handle_colour@S4`, a question about now):

```text
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
S4-T1 Sienna: tote.fabric = canvas [proposed] | sources=S4-T1
S4-T1 Sienna: tote.handle_colour = navy blue [proposed] | sources=S4-T1
```

## After meeting 5 (S5): the whole memory (6 records)

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [superseded] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
S2-T2 Rosa: tote.fabric = canvas [active] | sources=S2-T2,S2-T3,S2-T4
S4-T1 Sienna: tote.fabric = canvas [proposed] | sources=S4-T1
S4-T1 Sienna: tote.handle_colour = navy blue [proposed] | sources=S4-T1
```

Shown for "What fabric are we using for the tote bags?" (`tote.fabric@S5`, a question about now):

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [superseded] | sources=S1-T1,S1-T4
S2-T2 Rosa: tote.fabric = canvas [active] | sources=S2-T2,S2-T3,S2-T4
S4-T1 Sienna: tote.fabric = canvas [proposed] | sources=S4-T1
S4-T1 Sienna: tote.handle_colour = navy blue [proposed] | sources=S4-T1
```

Shown for "Which fabric, if any, did we use for the tote bags before the current one?" (`tote.fabric@S5-previous`, a question about the past):

```text
S1-T1 Sienna: tote.fabric = lightweight cotton [superseded] | sources=S1-T1,S1-T4
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
S2-T2 Rosa: tote.fabric = canvas [active] | sources=S2-T2,S2-T3,S2-T4
S4-T1 Sienna: tote.fabric = canvas [proposed] | sources=S4-T1
S4-T1 Sienna: tote.handle_colour = navy blue [proposed] | sources=S4-T1
```

Shown for "What colour handles are we using for the tote bags?" (`tote.handle_colour@S5`, a question about now):

```text
S1-T3 Rosa: tote.handle_colour = navy blue [superseded] | sources=S1-T3
S1-T4 Sienna: tote.handle_colour = navy blue [active] | sources=S1-T4,S1-T3
S4-T1 Sienna: tote.fabric = canvas [proposed] | sources=S4-T1
S4-T1 Sienna: tote.handle_colour = navy blue [proposed] | sources=S4-T1
```
