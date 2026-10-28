# deck-c04 ("Dinner After the Museum"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer). This scenario has no question about the past.

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (4 records)

```text
S1-T1 Lily: dinner.main_dish = Beijing roast duck [superseded] | sources=S1-T1
S1-T2 Mark: dinner.main_dish = Beijing roast duck [active] | sources=S1-T2,S1-T1,S1-T5
S1-T4 Lily: dinner.vegetable_side = smashed cucumber [superseded] | sources=S1-T4
S1-T5 Chen: dinner.vegetable_side = smashed cucumber [active] | sources=S1-T5,S1-T4
```

Shown for "What main dish have we chosen for this dinner?" (`dinner.main_dish@S1`, a question about now):

```text
S1-T1 Lily: dinner.main_dish = Beijing roast duck [superseded] | sources=S1-T1
S1-T2 Mark: dinner.main_dish = Beijing roast duck [active] | sources=S1-T2,S1-T1,S1-T5
S1-T4 Lily: dinner.vegetable_side = smashed cucumber [superseded] | sources=S1-T4
S1-T5 Chen: dinner.vegetable_side = smashed cucumber [active] | sources=S1-T5,S1-T4
```

Shown for "What vegetable side are we ordering?" (`dinner.vegetable_side@S1`, a question about now):

```text
S1-T1 Lily: dinner.main_dish = Beijing roast duck [superseded] | sources=S1-T1
S1-T2 Mark: dinner.main_dish = Beijing roast duck [active] | sources=S1-T2,S1-T1,S1-T5
S1-T4 Lily: dinner.vegetable_side = smashed cucumber [superseded] | sources=S1-T4
S1-T5 Chen: dinner.vegetable_side = smashed cucumber [active] | sources=S1-T5,S1-T4
```

## After meeting 2 (S2): the whole memory (4 records)

```text
S1-T1 Lily: dinner.main_dish = Beijing roast duck [superseded] | sources=S1-T1
S1-T2 Mark: dinner.main_dish = Beijing roast duck [active] | sources=S1-T2,S1-T1,S1-T5
S1-T4 Lily: dinner.vegetable_side = smashed cucumber [superseded] | sources=S1-T4
S1-T5 Chen: dinner.vegetable_side = smashed cucumber [active] | sources=S1-T5,S1-T4
```

Shown for "What main dish have we chosen for this dinner?" (`dinner.main_dish@S2`, a question about now):

```text
S1-T1 Lily: dinner.main_dish = Beijing roast duck [superseded] | sources=S1-T1
S1-T2 Mark: dinner.main_dish = Beijing roast duck [active] | sources=S1-T2,S1-T1,S1-T5
S1-T4 Lily: dinner.vegetable_side = smashed cucumber [superseded] | sources=S1-T4
S1-T5 Chen: dinner.vegetable_side = smashed cucumber [active] | sources=S1-T5,S1-T4
```

Shown for "What vegetable side are we ordering?" (`dinner.vegetable_side@S2`, a question about now):

```text
S1-T1 Lily: dinner.main_dish = Beijing roast duck [superseded] | sources=S1-T1
S1-T2 Mark: dinner.main_dish = Beijing roast duck [active] | sources=S1-T2,S1-T1,S1-T5
S1-T4 Lily: dinner.vegetable_side = smashed cucumber [superseded] | sources=S1-T4
S1-T5 Chen: dinner.vegetable_side = smashed cucumber [active] | sources=S1-T5,S1-T4
```

## After meeting 3 (S3): the whole memory (4 records)

```text
S1-T1 Lily: dinner.main_dish = Beijing roast duck [superseded] | sources=S1-T1
S1-T2 Mark: dinner.main_dish = Beijing roast duck [active] | sources=S1-T2,S1-T1,S1-T5,S3-T1
S1-T4 Lily: dinner.vegetable_side = smashed cucumber [superseded] | sources=S1-T4
S1-T5 Chen: dinner.vegetable_side = smashed cucumber [active] | sources=S1-T5,S1-T4,S3-T1
```

Shown for "What main dish have we chosen for this dinner?" (`dinner.main_dish@S3`, a question about now):

```text
S1-T1 Lily: dinner.main_dish = Beijing roast duck [superseded] | sources=S1-T1
S1-T2 Mark: dinner.main_dish = Beijing roast duck [active] | sources=S1-T2,S1-T1,S1-T5,S3-T1
S1-T4 Lily: dinner.vegetable_side = smashed cucumber [superseded] | sources=S1-T4
S1-T5 Chen: dinner.vegetable_side = smashed cucumber [active] | sources=S1-T5,S1-T4,S3-T1
```

Shown for "What vegetable side are we ordering?" (`dinner.vegetable_side@S3`, a question about now):

```text
S1-T1 Lily: dinner.main_dish = Beijing roast duck [superseded] | sources=S1-T1
S1-T2 Mark: dinner.main_dish = Beijing roast duck [active] | sources=S1-T2,S1-T1,S1-T5,S3-T1
S1-T4 Lily: dinner.vegetable_side = smashed cucumber [superseded] | sources=S1-T4
S1-T5 Chen: dinner.vegetable_side = smashed cucumber [active] | sources=S1-T5,S1-T4,S3-T1
```
