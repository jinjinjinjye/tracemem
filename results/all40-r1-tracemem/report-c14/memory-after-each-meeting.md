# report-c14 ("Music for the Charity Fair"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer). This scenario has no question about the past.

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (1 records)

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
```

Shown for "What closing song have we chosen?" (`song.closing@S1`, a question about now):

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
```

Shown for "What song will open our charity fair?" (`song.opening@S1`, a question about now):

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
```

## After meeting 2 (S2): the whole memory (3 records)

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
S2-T1 Farah: song.closing = Lean on Me [superseded] | sources=S2-T1
S2-T3 Ruby: song.closing = Lean on Me [active] | sources=S2-T3,S2-T1,S2-T4
```

Shown for "What song will close our charity fair?" (`song.closing@S2`, a question about now):

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
S2-T1 Farah: song.closing = Lean on Me [superseded] | sources=S2-T1
S2-T3 Ruby: song.closing = Lean on Me [active] | sources=S2-T3,S2-T1,S2-T4
```

Shown for "What song will open our charity fair?" (`song.opening@S2`, a question about now):

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
S2-T1 Farah: song.closing = Lean on Me [superseded] | sources=S2-T1
S2-T3 Ruby: song.closing = Lean on Me [active] | sources=S2-T3,S2-T1,S2-T4
```

## After meeting 3 (S3): the whole memory (3 records)

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
S2-T1 Farah: song.closing = Lean on Me [superseded] | sources=S2-T1
S2-T3 Ruby: song.closing = Lean on Me [active] | sources=S2-T3,S2-T1,S2-T4
```

Shown for "What song will close our charity fair?" (`song.closing@S3`, a question about now):

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
S2-T1 Farah: song.closing = Lean on Me [superseded] | sources=S2-T1
S2-T3 Ruby: song.closing = Lean on Me [active] | sources=S2-T3,S2-T1,S2-T4
```

Shown for "What song will open our charity fair?" (`song.opening@S3`, a question about now):

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
S2-T1 Farah: song.closing = Lean on Me [superseded] | sources=S2-T1
S2-T3 Ruby: song.closing = Lean on Me [active] | sources=S2-T3,S2-T1,S2-T4
```

## After meeting 4 (S4): the whole memory (3 records)

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
S2-T1 Farah: song.closing = Lean on Me [superseded] | sources=S2-T1
S2-T3 Ruby: song.closing = Lean on Me [active] | sources=S2-T3,S2-T1,S2-T4
```

Shown for "What song will close our charity fair?" (`song.closing@S4`, a question about now):

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
S2-T1 Farah: song.closing = Lean on Me [superseded] | sources=S2-T1
S2-T3 Ruby: song.closing = Lean on Me [active] | sources=S2-T3,S2-T1,S2-T4
```

Shown for "What song will open our charity fair?" (`song.opening@S4`, a question about now):

```text
S1-T1 Ruby: song.opening = Here Comes the Sun [active] | sources=S1-T1
S2-T1 Farah: song.closing = Lean on Me [superseded] | sources=S2-T1
S2-T3 Ruby: song.closing = Lean on Me [active] | sources=S2-T3,S2-T1,S2-T4
```
