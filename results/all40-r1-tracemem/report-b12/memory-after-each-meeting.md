# report-b12 ("A club agreement survives repeated paraphrases"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer). This scenario has no question about the past.

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (4 records)

```text
S1-T1 Gus: gathering.venue = Maple Room [superseded] | sources=S1-T1
S1-T2 Holly: gathering.venue = Maple Room [active] | sources=S1-T2,S1-T1
S1-T3 Idris: refreshments.budget = SGD 80 [proposed] | sources=S1-T3
S1-T4 Juno: refreshments.budget = SGD 80 [proposed] | sources=S1-T4
```

Shown for "Which room are we using for the board-game gathering?" (`gathering.venue@S1`, a question about now):

```text
S1-T1 Gus: gathering.venue = Maple Room [superseded] | sources=S1-T1
S1-T2 Holly: gathering.venue = Maple Room [active] | sources=S1-T2,S1-T1
S1-T3 Idris: refreshments.budget = SGD 80 [proposed] | sources=S1-T3
S1-T4 Juno: refreshments.budget = SGD 80 [proposed] | sources=S1-T4
```

Shown for "What is the refreshment budget for the gathering?" (`refreshments.budget@S1`, a question about now):

```text
S1-T1 Gus: gathering.venue = Maple Room [superseded] | sources=S1-T1
S1-T2 Holly: gathering.venue = Maple Room [active] | sources=S1-T2,S1-T1
S1-T3 Idris: refreshments.budget = SGD 80 [proposed] | sources=S1-T3
S1-T4 Juno: refreshments.budget = SGD 80 [proposed] | sources=S1-T4
```

## After meeting 2 (S2): the whole memory (5 records)

```text
S1-T1 Gus: gathering.venue = Maple Room [superseded] | sources=S1-T1
S1-T2 Holly: gathering.venue = Maple Room [active] | sources=S1-T2,S1-T1
S1-T3 Idris: refreshments.budget = SGD 80 [proposed] | sources=S1-T3
S1-T4 Juno: refreshments.budget = SGD 80 [proposed] | sources=S1-T4
S2-T3 Kian: refreshments.budget = SGD 200 [proposed] | sources=S2-T3
```

Shown for "Which room are we using for the board-game gathering?" (`gathering.venue@S2`, a question about now):

```text
S1-T1 Gus: gathering.venue = Maple Room [superseded] | sources=S1-T1
S1-T2 Holly: gathering.venue = Maple Room [active] | sources=S1-T2,S1-T1
S1-T4 Juno: refreshments.budget = SGD 80 [proposed] | sources=S1-T4
S2-T3 Kian: refreshments.budget = SGD 200 [proposed] | sources=S2-T3
```

Shown for "What is the refreshment budget for the gathering?" (`refreshments.budget@S2`, a question about now):

```text
S1-T1 Gus: gathering.venue = Maple Room [superseded] | sources=S1-T1
S1-T3 Idris: refreshments.budget = SGD 80 [proposed] | sources=S1-T3
S1-T4 Juno: refreshments.budget = SGD 80 [proposed] | sources=S1-T4
S2-T3 Kian: refreshments.budget = SGD 200 [proposed] | sources=S2-T3
```

## After meeting 3 (S3): the whole memory (6 records)

```text
S1-T1 Gus: gathering.venue = Maple Room [superseded] | sources=S1-T1
S1-T2 Holly: gathering.venue = Maple Room [active] | sources=S1-T2,S1-T1
S1-T3 Idris: refreshments.budget = SGD 80 [proposed] | sources=S1-T3
S1-T4 Juno: refreshments.budget = SGD 80 [proposed] | sources=S1-T4
S2-T3 Kian: refreshments.budget = SGD 200 [proposed] | sources=S2-T3
S3-T1 Idris: gathering.venue = Cinnamon Room [proposed] | sources=S3-T1
```

Shown for "What date has been chosen for the gathering?" (`gathering.date@S3`, a question about now):

```text
S1-T1 Gus: gathering.venue = Maple Room [superseded] | sources=S1-T1
S1-T2 Holly: gathering.venue = Maple Room [active] | sources=S1-T2,S1-T1
S2-T3 Kian: refreshments.budget = SGD 200 [proposed] | sources=S2-T3
S3-T1 Idris: gathering.venue = Cinnamon Room [proposed] | sources=S3-T1
```

Shown for "Which room are we using for the board-game gathering?" (`gathering.venue@S3`, a question about now):

```text
S1-T1 Gus: gathering.venue = Maple Room [superseded] | sources=S1-T1
S1-T2 Holly: gathering.venue = Maple Room [active] | sources=S1-T2,S1-T1
S1-T4 Juno: refreshments.budget = SGD 80 [proposed] | sources=S1-T4
S3-T1 Idris: gathering.venue = Cinnamon Room [proposed] | sources=S3-T1
```

Shown for "What is the refreshment budget for the gathering?" (`refreshments.budget@S3`, a question about now):

```text
S1-T1 Gus: gathering.venue = Maple Room [superseded] | sources=S1-T1
S1-T3 Idris: refreshments.budget = SGD 80 [proposed] | sources=S1-T3
S1-T4 Juno: refreshments.budget = SGD 80 [proposed] | sources=S1-T4
S2-T3 Kian: refreshments.budget = SGD 200 [proposed] | sources=S2-T3
```
