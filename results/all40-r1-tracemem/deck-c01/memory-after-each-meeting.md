# deck-c01 ("An Evening at the Giant Wild Goose Pagoda"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (2 records)

```text
S1-T1 Wang: trip.transport = metro [active] | sources=S1-T1,S1-T5
S1-T4 Wang: trip.meeting_time = 5 pm [active] | sources=S1-T4,S1-T5
```

Shown for "What time are we meeting on Saturday?" (`trip.meeting_time@S1`, a question about now):

```text
S1-T1 Wang: trip.transport = metro [active] | sources=S1-T1,S1-T5
S1-T4 Wang: trip.meeting_time = 5 pm [active] | sources=S1-T4,S1-T5
```

Shown for "How are we travelling to the Giant Wild Goose Pagoda?" (`trip.transport@S1`, a question about now):

```text
S1-T1 Wang: trip.transport = metro [active] | sources=S1-T1,S1-T5
S1-T4 Wang: trip.meeting_time = 5 pm [active] | sources=S1-T4,S1-T5
```

## After meeting 2 (S2): the whole memory (3 records)

```text
S1-T1 Wang: trip.transport = metro [active] | sources=S1-T1,S1-T5
S1-T4 Wang: trip.meeting_time = 5 pm [active] | sources=S1-T4,S1-T5
S2-T1 Zhou: trip.transport = taxi [proposed] | sources=S2-T1
```

Shown for "What time are we meeting on Saturday?" (`trip.meeting_time@S2`, a question about now):

```text
S1-T1 Wang: trip.transport = metro [active] | sources=S1-T1,S1-T5
S1-T4 Wang: trip.meeting_time = 5 pm [active] | sources=S1-T4,S1-T5
S2-T1 Zhou: trip.transport = taxi [proposed] | sources=S2-T1
```

Shown for "How are we travelling to the Giant Wild Goose Pagoda?" (`trip.transport@S2`, a question about now):

```text
S1-T1 Wang: trip.transport = metro [active] | sources=S1-T1,S1-T5
S1-T4 Wang: trip.meeting_time = 5 pm [active] | sources=S1-T4,S1-T5
S2-T1 Zhou: trip.transport = taxi [proposed] | sources=S2-T1
```

## After meeting 3 (S3): the whole memory (6 records)

```text
S1-T1 Wang: trip.transport = metro [active] | sources=S1-T1,S1-T5,S3-T5
S1-T4 Wang: trip.meeting_time = 5 pm [superseded] | sources=S1-T4,S1-T5
S2-T1 Zhou: trip.transport = taxi [proposed] | sources=S2-T1
S3-T1 Sun: trip.meeting_time = 6 pm [superseded] | sources=S3-T1
S3-T2 Wang: trip.meeting_time = 6 pm [active] | sources=S3-T2,S3-T1,S3-T3
S3-T3 Zhou: trip.transport = taxi [proposed] | sources=S3-T3
```

Shown for "What time are we meeting on Saturday?" (`trip.meeting_time@S3`, a question about now):

```text
S1-T1 Wang: trip.transport = metro [active] | sources=S1-T1,S1-T5,S3-T5
S1-T4 Wang: trip.meeting_time = 5 pm [superseded] | sources=S1-T4,S1-T5
S3-T1 Sun: trip.meeting_time = 6 pm [superseded] | sources=S3-T1
S3-T2 Wang: trip.meeting_time = 6 pm [active] | sources=S3-T2,S3-T1,S3-T3
```

Shown for "Which meeting time, if any, did we agree on before the current one?" (`trip.meeting_time@S3-previous`, a question about the past):

```text
S1-T1 Wang: trip.transport = metro [active] | sources=S1-T1,S1-T5,S3-T5
S1-T4 Wang: trip.meeting_time = 5 pm [superseded] | sources=S1-T4,S1-T5
S2-T1 Zhou: trip.transport = taxi [proposed] | sources=S2-T1
S3-T1 Sun: trip.meeting_time = 6 pm [superseded] | sources=S3-T1
S3-T2 Wang: trip.meeting_time = 6 pm [active] | sources=S3-T2,S3-T1,S3-T3
S3-T3 Zhou: trip.transport = taxi [proposed] | sources=S3-T3
```

Shown for "How are we travelling to the Giant Wild Goose Pagoda?" (`trip.transport@S3`, a question about now):

```text
S1-T4 Wang: trip.meeting_time = 5 pm [superseded] | sources=S1-T4,S1-T5
S2-T1 Zhou: trip.transport = taxi [proposed] | sources=S2-T1
S3-T2 Wang: trip.meeting_time = 6 pm [active] | sources=S3-T2,S3-T1,S3-T3
S3-T3 Zhou: trip.transport = taxi [proposed] | sources=S3-T3
```
