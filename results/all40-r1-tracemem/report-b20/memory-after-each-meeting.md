# report-b20 ("The mysterious low-temperature peak"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (7 records)

```text
S1-T1 Lin: comparison.primary_temperature = 25°C [active] | sources=S1-T1
S1-T2 Sam: outcome.main = initial capacity [proposed] | sources=S1-T2
S1-T3 Noor: outcome.main = capacity retention after 100 cycles [superseded] | sources=S1-T3
S1-T4 Alex: outcome.main = capacity retention after 100 cycles [active] | sources=S1-T4,S1-T3
S1-T5 Lin: data.batch = batch B [active] | sources=S1-T5,S1-T6
S1-T6 Sam: comparison.primary_temperature = 25°C [proposed] | sources=S1-T6
S1-T6 Sam: outcome.main = capacity retention after 100 cycles [proposed] | sources=S1-T6
```

Shown for "Which temperature are we using for the primary comparison?" (`comparison.primary_temperature@S1`, a question about now):

```text
S1-T1 Lin: comparison.primary_temperature = 25°C [active] | sources=S1-T1
S1-T2 Sam: outcome.main = initial capacity [proposed] | sources=S1-T2
S1-T4 Alex: outcome.main = capacity retention after 100 cycles [active] | sources=S1-T4,S1-T3
S1-T6 Sam: comparison.primary_temperature = 25°C [proposed] | sources=S1-T6
```

Shown for "Which batch are we using for both materials?" (`data.batch@S1`, a question about now):

```text
S1-T3 Noor: outcome.main = capacity retention after 100 cycles [superseded] | sources=S1-T3
S1-T4 Alex: outcome.main = capacity retention after 100 cycles [active] | sources=S1-T4,S1-T3
S1-T5 Lin: data.batch = batch B [active] | sources=S1-T5,S1-T6
S1-T6 Sam: outcome.main = capacity retention after 100 cycles [proposed] | sources=S1-T6
```

Shown for "What is our main outcome measure?" (`outcome.main@S1`, a question about now):

```text
S1-T2 Sam: outcome.main = initial capacity [proposed] | sources=S1-T2
S1-T3 Noor: outcome.main = capacity retention after 100 cycles [superseded] | sources=S1-T3
S1-T4 Alex: outcome.main = capacity retention after 100 cycles [active] | sources=S1-T4,S1-T3
S1-T6 Sam: outcome.main = capacity retention after 100 cycles [proposed] | sources=S1-T6
```

## After meeting 2 (S2): the whole memory (8 records)

```text
S1-T1 Lin: comparison.primary_temperature = 25°C [active] | sources=S1-T1
S1-T2 Sam: outcome.main = initial capacity [proposed] | sources=S1-T2
S1-T3 Noor: outcome.main = capacity retention after 100 cycles [superseded] | sources=S1-T3
S1-T4 Alex: outcome.main = capacity retention after 100 cycles [active] | sources=S1-T4,S1-T3,S2-T6
S1-T5 Lin: data.batch = batch B [active] | sources=S1-T5,S1-T6
S1-T6 Sam: comparison.primary_temperature = 25°C [proposed] | sources=S1-T6
S1-T6 Sam: outcome.main = capacity retention after 100 cycles [proposed] | sources=S1-T6
S2-T1 Sam: comparison.primary_temperature = 10°C [contested] | sources=S2-T1
```

Shown for "Which temperature are we using for the primary comparison?" (`comparison.primary_temperature@S2`, a question about now):

```text
S1-T1 Lin: comparison.primary_temperature = 25°C [active] | sources=S1-T1
S1-T2 Sam: outcome.main = initial capacity [proposed] | sources=S1-T2
S1-T6 Sam: comparison.primary_temperature = 25°C [proposed] | sources=S1-T6
S2-T1 Sam: comparison.primary_temperature = 10°C [contested] | sources=S2-T1
```

Shown for "Which batch are we using for both materials?" (`data.batch@S2`, a question about now):

```text
S1-T3 Noor: outcome.main = capacity retention after 100 cycles [superseded] | sources=S1-T3
S1-T4 Alex: outcome.main = capacity retention after 100 cycles [active] | sources=S1-T4,S1-T3,S2-T6
S1-T5 Lin: data.batch = batch B [active] | sources=S1-T5,S1-T6
S1-T6 Sam: outcome.main = capacity retention after 100 cycles [proposed] | sources=S1-T6
```

Shown for "What is our main outcome measure?" (`outcome.main@S2`, a question about now):

```text
S1-T2 Sam: outcome.main = initial capacity [proposed] | sources=S1-T2
S1-T3 Noor: outcome.main = capacity retention after 100 cycles [superseded] | sources=S1-T3
S1-T4 Alex: outcome.main = capacity retention after 100 cycles [active] | sources=S1-T4,S1-T3,S2-T6
S1-T6 Sam: outcome.main = capacity retention after 100 cycles [proposed] | sources=S1-T6
```

## After meeting 3 (S3): the whole memory (10 records)

```text
S1-T1 Lin: comparison.primary_temperature = 25°C [superseded] | sources=S1-T1
S1-T2 Sam: outcome.main = initial capacity [proposed] | sources=S1-T2
S1-T3 Noor: outcome.main = capacity retention after 100 cycles [superseded] | sources=S1-T3
S1-T4 Alex: outcome.main = capacity retention after 100 cycles [active] | sources=S1-T4,S1-T3,S2-T6,S3-T6
S1-T5 Lin: data.batch = batch B [active] | sources=S1-T5,S1-T6,S3-T6
S1-T6 Sam: comparison.primary_temperature = 25°C [proposed] | sources=S1-T6
S1-T6 Sam: outcome.main = capacity retention after 100 cycles [proposed] | sources=S1-T6
S2-T1 Sam: comparison.primary_temperature = 10°C [superseded] | sources=S2-T1
S3-T2 Lin: comparison.primary_temperature = 10°C [active] | sources=S3-T2,S2-T1,S3-T6
S3-T2 Lin: comparison.secondary_temperature = 25°C [active] | sources=S3-T2
```

Shown for "Which temperature are we using for the primary comparison?" (`comparison.primary_temperature@S3`, a question about now):

```text
S1-T1 Lin: comparison.primary_temperature = 25°C [superseded] | sources=S1-T1
S1-T6 Sam: comparison.primary_temperature = 25°C [proposed] | sources=S1-T6
S2-T1 Sam: comparison.primary_temperature = 10°C [superseded] | sources=S2-T1
S3-T2 Lin: comparison.primary_temperature = 10°C [active] | sources=S3-T2,S2-T1,S3-T6
```

Shown for "Which temperature, if any, did we use for the primary comparison before the current one?" (`comparison.primary_temperature@S3-previous`, a question about the past):

```text
S1-T1 Lin: comparison.primary_temperature = 25°C [superseded] | sources=S1-T1
S1-T2 Sam: outcome.main = initial capacity [proposed] | sources=S1-T2
S1-T3 Noor: outcome.main = capacity retention after 100 cycles [superseded] | sources=S1-T3
S1-T4 Alex: outcome.main = capacity retention after 100 cycles [active] | sources=S1-T4,S1-T3,S2-T6,S3-T6
S1-T5 Lin: data.batch = batch B [active] | sources=S1-T5,S1-T6,S3-T6
S1-T6 Sam: comparison.primary_temperature = 25°C [proposed] | sources=S1-T6
S1-T6 Sam: outcome.main = capacity retention after 100 cycles [proposed] | sources=S1-T6
S2-T1 Sam: comparison.primary_temperature = 10°C [superseded] | sources=S2-T1
S3-T2 Lin: comparison.primary_temperature = 10°C [active] | sources=S3-T2,S2-T1,S3-T6
S3-T2 Lin: comparison.secondary_temperature = 25°C [active] | sources=S3-T2
```

Shown for "Which temperature are we using for the secondary analysis?" (`comparison.secondary_temperature@S3`, a question about now):

```text
S1-T6 Sam: comparison.primary_temperature = 25°C [proposed] | sources=S1-T6
S2-T1 Sam: comparison.primary_temperature = 10°C [superseded] | sources=S2-T1
S3-T2 Lin: comparison.primary_temperature = 10°C [active] | sources=S3-T2,S2-T1,S3-T6
S3-T2 Lin: comparison.secondary_temperature = 25°C [active] | sources=S3-T2
```

Shown for "Which batch are we using for both materials?" (`data.batch@S3`, a question about now):

```text
S1-T3 Noor: outcome.main = capacity retention after 100 cycles [superseded] | sources=S1-T3
S1-T4 Alex: outcome.main = capacity retention after 100 cycles [active] | sources=S1-T4,S1-T3,S2-T6,S3-T6
S1-T5 Lin: data.batch = batch B [active] | sources=S1-T5,S1-T6,S3-T6
S1-T6 Sam: outcome.main = capacity retention after 100 cycles [proposed] | sources=S1-T6
```

Shown for "What is our main outcome measure?" (`outcome.main@S3`, a question about now):

```text
S1-T2 Sam: outcome.main = initial capacity [proposed] | sources=S1-T2
S1-T3 Noor: outcome.main = capacity retention after 100 cycles [superseded] | sources=S1-T3
S1-T4 Alex: outcome.main = capacity retention after 100 cycles [active] | sources=S1-T4,S1-T3,S2-T6,S3-T6
S1-T6 Sam: outcome.main = capacity retention after 100 cycles [proposed] | sources=S1-T6
```
