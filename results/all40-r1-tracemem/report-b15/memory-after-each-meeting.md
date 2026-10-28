# report-b15 ("A pop-up packaging choice changes twice"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (4 records)

```text
S1-T1 Rhea: packaging.type = paper bags [superseded] | sources=S1-T1
S1-T2 Sol: packaging.type = paper bags [active] | sources=S1-T2,S1-T1
S1-T3 Tariq: collection.window = 2 to 4 pm [superseded] | sources=S1-T3
S1-T4 Rhea, Sol: collection.window = 2 to 4 pm [active] | sources=S1-T4,S1-T3
```

Shown for "When do customers collect their orders?" (`collection.window@S1`, a question about now):

```text
S1-T1 Rhea: packaging.type = paper bags [superseded] | sources=S1-T1
S1-T2 Sol: packaging.type = paper bags [active] | sources=S1-T2,S1-T1
S1-T3 Tariq: collection.window = 2 to 4 pm [superseded] | sources=S1-T3
S1-T4 Rhea, Sol: collection.window = 2 to 4 pm [active] | sources=S1-T4,S1-T3
```

Shown for "What packaging are we using for the pop-up orders?" (`packaging.type@S1`, a question about now):

```text
S1-T1 Rhea: packaging.type = paper bags [superseded] | sources=S1-T1
S1-T2 Sol: packaging.type = paper bags [active] | sources=S1-T2,S1-T1
S1-T3 Tariq: collection.window = 2 to 4 pm [superseded] | sources=S1-T3
S1-T4 Rhea, Sol: collection.window = 2 to 4 pm [active] | sources=S1-T4,S1-T3
```

## After meeting 2 (S2): the whole memory (5 records)

```text
S1-T1 Rhea: packaging.type = paper bags [superseded] | sources=S1-T1
S1-T2 Sol: packaging.type = paper bags [superseded] | sources=S1-T2,S1-T1
S1-T3 Tariq: collection.window = 2 to 4 pm [superseded] | sources=S1-T3
S1-T4 Rhea, Sol: collection.window = 2 to 4 pm [active] | sources=S1-T4,S1-T3
S2-T1 Sol: packaging.type = cardboard boxes [active] | sources=S2-T1,S2-T2
```

Shown for "When do customers collect their orders?" (`collection.window@S2`, a question about now):

```text
S1-T1 Rhea: packaging.type = paper bags [superseded] | sources=S1-T1
S1-T3 Tariq: collection.window = 2 to 4 pm [superseded] | sources=S1-T3
S1-T4 Rhea, Sol: collection.window = 2 to 4 pm [active] | sources=S1-T4,S1-T3
S2-T1 Sol: packaging.type = cardboard boxes [active] | sources=S2-T1,S2-T2
```

Shown for "What packaging are we using for the pop-up orders?" (`packaging.type@S2`, a question about now):

```text
S1-T1 Rhea: packaging.type = paper bags [superseded] | sources=S1-T1
S1-T2 Sol: packaging.type = paper bags [superseded] | sources=S1-T2,S1-T1
S1-T3 Tariq: collection.window = 2 to 4 pm [superseded] | sources=S1-T3
S2-T1 Sol: packaging.type = cardboard boxes [active] | sources=S2-T1,S2-T2
```

## After meeting 3 (S3): the whole memory (8 records)

```text
S1-T1 Rhea: packaging.type = paper bags [superseded] | sources=S1-T1
S1-T2 Sol: packaging.type = paper bags [superseded] | sources=S1-T2,S1-T1
S1-T3 Tariq: collection.window = 2 to 4 pm [superseded] | sources=S1-T3
S1-T4 Rhea, Sol: collection.window = 2 to 4 pm [active] | sources=S1-T4,S1-T3
S2-T1 Sol: packaging.type = cardboard boxes [superseded] | sources=S2-T1,S2-T2
S3-T2 Rhea: packaging.type = paper bags [active] | sources=S3-T2
S3-T3 Sol: packaging.type = plastic bags [proposed] | sources=S3-T3
S3-T4 Tariq: packaging.type = plastic bags [proposed] | sources=S3-T4
```

Shown for "When do customers collect their orders?" (`collection.window@S3`, a question about now):

```text
S1-T1 Rhea: packaging.type = paper bags [superseded] | sources=S1-T1
S1-T3 Tariq: collection.window = 2 to 4 pm [superseded] | sources=S1-T3
S1-T4 Rhea, Sol: collection.window = 2 to 4 pm [active] | sources=S1-T4,S1-T3
S3-T2 Rhea: packaging.type = paper bags [active] | sources=S3-T2
```

Shown for "What packaging are we using for the pop-up orders?" (`packaging.type@S3`, a question about now):

```text
S1-T1 Rhea: packaging.type = paper bags [superseded] | sources=S1-T1
S1-T2 Sol: packaging.type = paper bags [superseded] | sources=S1-T2,S1-T1
S2-T1 Sol: packaging.type = cardboard boxes [superseded] | sources=S2-T1,S2-T2
S3-T2 Rhea: packaging.type = paper bags [active] | sources=S3-T2
```

Shown for "Which packaging, if any, did we use for the pop-up orders before the current one?" (`packaging.type@S3-previous`, a question about the past):

```text
S1-T1 Rhea: packaging.type = paper bags [superseded] | sources=S1-T1
S1-T2 Sol: packaging.type = paper bags [superseded] | sources=S1-T2,S1-T1
S1-T3 Tariq: collection.window = 2 to 4 pm [superseded] | sources=S1-T3
S1-T4 Rhea, Sol: collection.window = 2 to 4 pm [active] | sources=S1-T4,S1-T3
S2-T1 Sol: packaging.type = cardboard boxes [superseded] | sources=S2-T1,S2-T2
S3-T2 Rhea: packaging.type = paper bags [active] | sources=S3-T2
S3-T3 Sol: packaging.type = plastic bags [proposed] | sources=S3-T3
S3-T4 Tariq: packaging.type = plastic bags [proposed] | sources=S3-T4
```
