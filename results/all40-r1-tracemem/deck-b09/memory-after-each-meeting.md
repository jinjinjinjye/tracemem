# deck-b09 ("Two office rooms have different delivery dates"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (5 records)

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [active] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T4 Yuri: delivery.meeting_room = 21 November [superseded] | sources=S1-T4
S1-T5 Xia: delivery.meeting_room = 21 November [active] | sources=S1-T5,S1-T4
```

Shown for "What is the meeting-room furniture delivery date?" (`delivery.meeting_room@S1`, a question about now):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T4 Yuri: delivery.meeting_room = 21 November [superseded] | sources=S1-T4
S1-T5 Xia: delivery.meeting_room = 21 November [active] | sources=S1-T5,S1-T4
```

Shown for "What is the training-room furniture delivery date?" (`delivery.training_room@S1`, a question about now):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [active] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T4 Yuri: delivery.meeting_room = 21 November [superseded] | sources=S1-T4
```

## After meeting 2 (S2): the whole memory (6 records)

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T4 Yuri: delivery.meeting_room = 21 November [superseded] | sources=S1-T4
S1-T5 Xia: delivery.meeting_room = 21 November [active] | sources=S1-T5,S1-T4
S2-T1 Vik: delivery.training_room = 15 November [active] | sources=S2-T1,S2-T2
```

Shown for "What is the meeting-room furniture delivery date?" (`delivery.meeting_room@S2`, a question about now):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T4 Yuri: delivery.meeting_room = 21 November [superseded] | sources=S1-T4
S1-T5 Xia: delivery.meeting_room = 21 November [active] | sources=S1-T5,S1-T4
```

Shown for "What is the training-room furniture delivery date?" (`delivery.training_room@S2`, a question about now):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S2-T1 Vik: delivery.training_room = 15 November [active] | sources=S2-T1,S2-T2
```

## After meeting 3 (S3): the whole memory (7 records)

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T4 Yuri: delivery.meeting_room = 21 November [superseded] | sources=S1-T4
S1-T5 Xia: delivery.meeting_room = 21 November [active] | sources=S1-T5,S1-T4,S3-T5
S2-T1 Vik: delivery.training_room = 15 November [active] | sources=S2-T1,S2-T2
S3-T3 Yuri: delivery.meeting_room = 10 November [declined] | sources=S3-T3
```

Shown for "What is the meeting-room furniture delivery date?" (`delivery.meeting_room@S3`, a question about now):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T4 Yuri: delivery.meeting_room = 21 November [superseded] | sources=S1-T4
S1-T5 Xia: delivery.meeting_room = 21 November [active] | sources=S1-T5,S1-T4,S3-T5
```

Shown for "What is the training-room furniture delivery date?" (`delivery.training_room@S3`, a question about now):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S2-T1 Vik: delivery.training_room = 15 November [active] | sources=S2-T1,S2-T2
```

## After meeting 4 (S4): the whole memory (9 records)

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T4 Yuri: delivery.meeting_room = 21 November [superseded] | sources=S1-T4
S1-T5 Xia: delivery.meeting_room = 21 November [superseded] | sources=S1-T5,S1-T4,S3-T5
S2-T1 Vik: delivery.training_room = 15 November [active] | sources=S2-T1,S2-T2
S3-T3 Yuri: delivery.meeting_room = 10 November [declined] | sources=S3-T3
S4-T3 Uma: delivery.meeting_room = 25 November [superseded] | sources=S4-T3
S4-T4 Vik: delivery.meeting_room = 25 November [active] | sources=S4-T4,S4-T3
```

Shown for "What is the meeting-room furniture delivery date?" (`delivery.meeting_room@S4`, a question about now):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T5 Xia: delivery.meeting_room = 21 November [superseded] | sources=S1-T5,S1-T4,S3-T5
S4-T3 Uma: delivery.meeting_room = 25 November [superseded] | sources=S4-T3
```

Shown for "What is the training-room furniture delivery date?" (`delivery.training_room@S4`, a question about now):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [superseded] | sources=S1-T1
S2-T1 Vik: delivery.training_room = 15 November [active] | sources=S2-T1,S2-T2
S4-T3 Uma: delivery.meeting_room = 25 November [superseded] | sources=S4-T3
```

## After meeting 5 (S5): the whole memory (10 records)

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T4 Yuri: delivery.meeting_room = 21 November [superseded] | sources=S1-T4
S1-T5 Xia: delivery.meeting_room = 21 November [superseded] | sources=S1-T5,S1-T4,S3-T5
S2-T1 Vik: delivery.training_room = 15 November [active] | sources=S2-T1,S2-T2
S3-T3 Yuri: delivery.meeting_room = 10 November [declined] | sources=S3-T3
S4-T3 Uma: delivery.meeting_room = 25 November [superseded] | sources=S4-T3
S4-T4 Vik: delivery.meeting_room = 25 November [superseded] | sources=S4-T4,S4-T3
S5-T1 Yuri: delivery.meeting_room = 17 November [active] | sources=S5-T1
```

Shown for "What is the meeting-room furniture delivery date?" (`delivery.meeting_room@S5`, a question about now):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S4-T3 Uma: delivery.meeting_room = 25 November [superseded] | sources=S4-T3
S4-T4 Vik: delivery.meeting_room = 25 November [superseded] | sources=S4-T4,S4-T3
```

Shown for "Which meeting-room delivery date, if any, did we have before the current one?" (`delivery.meeting_room@S5-previous`, a question about the past):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T4 Yuri: delivery.meeting_room = 21 November [superseded] | sources=S1-T4
S1-T5 Xia: delivery.meeting_room = 21 November [superseded] | sources=S1-T5,S1-T4,S3-T5
S2-T1 Vik: delivery.training_room = 15 November [active] | sources=S2-T1,S2-T2
S3-T3 Yuri: delivery.meeting_room = 10 November [declined] | sources=S3-T3
S4-T3 Uma: delivery.meeting_room = 25 November [superseded] | sources=S4-T3
S4-T4 Vik: delivery.meeting_room = 25 November [superseded] | sources=S4-T4,S4-T3
S5-T1 Yuri: delivery.meeting_room = 17 November [active] | sources=S5-T1
```

Shown for "What is the training-room furniture delivery date?" (`delivery.training_room@S5`, a question about now):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [superseded] | sources=S1-T1
S2-T1 Vik: delivery.training_room = 15 November [active] | sources=S2-T1,S2-T2
S4-T3 Uma: delivery.meeting_room = 25 November [superseded] | sources=S4-T3
```

Shown for "Which training-room delivery date, if any, did we have before the current one?" (`delivery.training_room@S5-previous`, a question about the past):

```text
S1-T1 Uma: delivery.meeting_room = 10 November [superseded] | sources=S1-T1
S1-T1 Uma: delivery.training_room = 12 November [superseded] | sources=S1-T1
S1-T3 Xia: delivery.meeting_room = 20 November [proposed] | sources=S1-T3
S1-T4 Yuri: delivery.meeting_room = 21 November [superseded] | sources=S1-T4
S1-T5 Xia: delivery.meeting_room = 21 November [superseded] | sources=S1-T5,S1-T4,S3-T5
S2-T1 Vik: delivery.training_room = 15 November [active] | sources=S2-T1,S2-T2
S3-T3 Yuri: delivery.meeting_room = 10 November [declined] | sources=S3-T3
S4-T3 Uma: delivery.meeting_room = 25 November [superseded] | sources=S4-T3
S4-T4 Vik: delivery.meeting_room = 25 November [superseded] | sources=S4-T4,S4-T3
S5-T1 Yuri: delivery.meeting_room = 17 November [active] | sources=S5-T1
```
