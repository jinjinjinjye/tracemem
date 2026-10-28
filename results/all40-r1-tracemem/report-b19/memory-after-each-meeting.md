# report-b19 ("The missing readings are changing the story"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (3 records)

```text
S1-T1 Researcher: missing.handling = drop incomplete hourly records [active] | sources=S1-T1
S1-T3 Researcher: data.resolution = hourly [active] | sources=S1-T3
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5
```

Shown for "Which locations are we comparing in the main comparison?" (`comparison.main@S1`, a question about now):

```text
S1-T1 Researcher: missing.handling = drop incomplete hourly records [active] | sources=S1-T1
S1-T3 Researcher: data.resolution = hourly [active] | sources=S1-T3
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5
```

Shown for "What time resolution are we using for the temperature measurements?" (`data.resolution@S1`, a question about now):

```text
S1-T1 Researcher: missing.handling = drop incomplete hourly records [active] | sources=S1-T1
S1-T3 Researcher: data.resolution = hourly [active] | sources=S1-T3
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5
```

Shown for "How are we handling missing temperature data in the main analysis?" (`missing.handling@S1`, a question about now):

```text
S1-T1 Researcher: missing.handling = drop incomplete hourly records [active] | sources=S1-T1
S1-T3 Researcher: data.resolution = hourly [active] | sources=S1-T3
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5
```

## After meeting 2 (S2): the whole memory (6 records)

```text
S1-T1 Researcher: missing.handling = drop incomplete hourly records [superseded] | sources=S1-T1
S1-T3 Researcher: data.resolution = hourly [active] | sources=S1-T3,S2-T5
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5,S2-T6
S2-T2 Agent: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T2
S2-T3 Researcher: missing.handling = linear interpolation of short gaps [active] | sources=S2-T3,S2-T2,S2-T6
S2-T4 Agent: data.resolution = daily averages [proposed] | sources=S2-T4
```

Shown for "Which locations are we comparing in the main comparison?" (`comparison.main@S2`, a question about now):

```text
S1-T3 Researcher: data.resolution = hourly [active] | sources=S1-T3,S2-T5
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5,S2-T6
S2-T2 Agent: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T2
S2-T3 Researcher: missing.handling = linear interpolation of short gaps [active] | sources=S2-T3,S2-T2,S2-T6
```

Shown for "What time resolution are we using for the temperature measurements?" (`data.resolution@S2`, a question about now):

```text
S1-T3 Researcher: data.resolution = hourly [active] | sources=S1-T3,S2-T5
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5,S2-T6
S2-T3 Researcher: missing.handling = linear interpolation of short gaps [active] | sources=S2-T3,S2-T2,S2-T6
S2-T4 Agent: data.resolution = daily averages [proposed] | sources=S2-T4
```

Shown for "How are we handling missing temperature data in the main analysis?" (`missing.handling@S2`, a question about now):

```text
S1-T1 Researcher: missing.handling = drop incomplete hourly records [superseded] | sources=S1-T1
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5,S2-T6
S2-T2 Agent: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T2
S2-T3 Researcher: missing.handling = linear interpolation of short gaps [active] | sources=S2-T3,S2-T2,S2-T6
```

## After meeting 3 (S3): the whole memory (8 records)

```text
S1-T1 Researcher: missing.handling = drop incomplete hourly records [superseded] | sources=S1-T1
S1-T3 Researcher: data.resolution = hourly [active] | sources=S1-T3,S2-T5,S3-T6
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5,S2-T6,S3-T6
S2-T2 Agent: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T2
S2-T3 Researcher: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T3,S2-T2,S2-T6
S2-T4 Agent: data.resolution = daily averages [proposed] | sources=S2-T4
S3-T2 Agent: missing.handling = interpolation of gaps up to one hour [proposed] | sources=S3-T2
S3-T3 Researcher: missing.handling = drop incomplete hourly records [active] | sources=S3-T3
```

Shown for "Which locations are we comparing in the main comparison?" (`comparison.main@S3`, a question about now):

```text
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5,S2-T6,S3-T6
S2-T2 Agent: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T2
S2-T3 Researcher: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T3,S2-T2,S2-T6
S3-T2 Agent: missing.handling = interpolation of gaps up to one hour [proposed] | sources=S3-T2
```

Shown for "What time resolution are we using for the temperature measurements?" (`data.resolution@S3`, a question about now):

```text
S1-T3 Researcher: data.resolution = hourly [active] | sources=S1-T3,S2-T5,S3-T6
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5,S2-T6,S3-T6
S2-T3 Researcher: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T3,S2-T2,S2-T6
S2-T4 Agent: data.resolution = daily averages [proposed] | sources=S2-T4
```

Shown for "How are we handling missing temperature data in the main analysis?" (`missing.handling@S3`, a question about now):

```text
S1-T1 Researcher: missing.handling = drop incomplete hourly records [superseded] | sources=S1-T1
S2-T2 Agent: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T2
S2-T3 Researcher: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T3,S2-T2,S2-T6
S3-T2 Agent: missing.handling = interpolation of gaps up to one hour [proposed] | sources=S3-T2
```

Shown for "Which way of handling missing temperature data, if any, did we use before the current one?" (`missing.handling@S3-previous`, a question about the past):

```text
S1-T1 Researcher: missing.handling = drop incomplete hourly records [superseded] | sources=S1-T1
S1-T3 Researcher: data.resolution = hourly [active] | sources=S1-T3,S2-T5,S3-T6
S1-T5 Researcher: comparison.main = rooftop versus street-level sensors [active] | sources=S1-T5,S2-T6,S3-T6
S2-T2 Agent: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T2
S2-T3 Researcher: missing.handling = linear interpolation of short gaps [superseded] | sources=S2-T3,S2-T2,S2-T6
S2-T4 Agent: data.resolution = daily averages [proposed] | sources=S2-T4
S3-T2 Agent: missing.handling = interpolation of gaps up to one hour [proposed] | sources=S3-T2
S3-T3 Researcher: missing.handling = drop incomplete hourly records [active] | sources=S3-T3
```
