# report-c18 ("Booking a Slot at the Repair Café"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (2 records)

```text
S1-T1 Imani: booking.method = paper signup sheet [active] | sources=S1-T1
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
```

Shown for "What visitor booking method is currently confirmed?" (`booking.method@S1`, a question about now):

```text
S1-T1 Imani: booking.method = paper signup sheet [active] | sources=S1-T1
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
```

Shown for "How long is each volunteer shift?" (`shift.length@S1`, a question about now):

```text
S1-T1 Imani: booking.method = paper signup sheet [active] | sources=S1-T1
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
```

## After meeting 2 (S2): the whole memory (3 records)

```text
S1-T1 Imani: booking.method = paper signup sheet [active] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [proposed] | sources=S2-T1
```

Shown for "What visitor booking method is currently confirmed?" (`booking.method@S2`, a question about now):

```text
S1-T1 Imani: booking.method = paper signup sheet [active] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [proposed] | sources=S2-T1
```

Shown for "How long is each volunteer shift?" (`shift.length@S2`, a question about now):

```text
S1-T1 Imani: booking.method = paper signup sheet [active] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [proposed] | sources=S2-T1
```

## After meeting 3 (S3): the whole memory (3 records)

```text
S1-T1 Imani: booking.method = paper signup sheet [active] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [proposed] | sources=S2-T1
```

Shown for "What visitor booking method is currently confirmed?" (`booking.method@S3`, a question about now):

```text
S1-T1 Imani: booking.method = paper signup sheet [active] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [proposed] | sources=S2-T1
```

Shown for "How long is each volunteer shift?" (`shift.length@S3`, a question about now):

```text
S1-T1 Imani: booking.method = paper signup sheet [active] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [proposed] | sources=S2-T1
```

## After meeting 4 (S4): the whole memory (4 records)

```text
S1-T1 Imani: booking.method = paper signup sheet [superseded] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [superseded] | sources=S2-T1
S4-T3 Imani: booking.method = online booking form [active] | sources=S4-T3,S2-T1
```

Shown for "What visitor booking method is currently confirmed?" (`booking.method@S4`, a question about now):

```text
S1-T1 Imani: booking.method = paper signup sheet [superseded] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [superseded] | sources=S2-T1
S4-T3 Imani: booking.method = online booking form [active] | sources=S4-T3,S2-T1
```

Shown for "How long is each volunteer shift?" (`shift.length@S4`, a question about now):

```text
S1-T1 Imani: booking.method = paper signup sheet [superseded] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [superseded] | sources=S2-T1
S4-T3 Imani: booking.method = online booking form [active] | sources=S4-T3,S2-T1
```

## After meeting 5 (S5): the whole memory (4 records)

```text
S1-T1 Imani: booking.method = paper signup sheet [superseded] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [superseded] | sources=S2-T1
S4-T3 Imani: booking.method = online booking form [active] | sources=S4-T3,S2-T1,S5-T1
```

Shown for "What visitor booking method is currently confirmed?" (`booking.method@S5`, a question about now):

```text
S1-T1 Imani: booking.method = paper signup sheet [superseded] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [superseded] | sources=S2-T1
S4-T3 Imani: booking.method = online booking form [active] | sources=S4-T3,S2-T1,S5-T1
```

Shown for "Which visitor booking method, if any, did we use before the current one?" (`booking.method@S5-previous`, a question about the past):

```text
S1-T1 Imani: booking.method = paper signup sheet [superseded] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [superseded] | sources=S2-T1
S4-T3 Imani: booking.method = online booking form [active] | sources=S4-T3,S2-T1,S5-T1
```

Shown for "How long is each volunteer shift?" (`shift.length@S5`, a question about now):

```text
S1-T1 Imani: booking.method = paper signup sheet [superseded] | sources=S1-T1,S2-T4
S1-T4 Beatrice: shift.length = 2 hours [active] | sources=S1-T4
S2-T1 Oscar: booking.method = online booking form [superseded] | sources=S2-T1
S4-T3 Imani: booking.method = online booking form [active] | sources=S4-T3,S2-T1,S5-T1
```
