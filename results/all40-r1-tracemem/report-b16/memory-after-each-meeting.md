# report-b16 ("A film team accepts an option by reference"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (6 records)

```text
S1-T1 Uma: film.soundtrack = piano track [superseded] | sources=S1-T1
S1-T2 Vik: film.soundtrack = piano track [active] | sources=S1-T2,S1-T1
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T4 Xia: film.location = community studio [active] | sources=S1-T4,S1-T3
S1-T4 Xia: film.final_edit_deadline = 28 November [superseded] | sources=S1-T4
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
```

Shown for "When is the final edit due?" (`film.final_edit_deadline@S1`, a question about now):

```text
S1-T2 Vik: film.soundtrack = piano track [active] | sources=S1-T2,S1-T1
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T4 Xia: film.final_edit_deadline = 28 November [superseded] | sources=S1-T4
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
```

Shown for "Where are we filming?" (`film.location@S1`, a question about now):

```text
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T4 Xia: film.final_edit_deadline = 28 November [superseded] | sources=S1-T4
S1-T4 Xia: film.location = community studio [active] | sources=S1-T4,S1-T3
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
```

Shown for "Which soundtrack are we using for the film?" (`film.soundtrack@S1`, a question about now):

```text
S1-T1 Uma: film.soundtrack = piano track [superseded] | sources=S1-T1
S1-T2 Vik: film.soundtrack = piano track [active] | sources=S1-T2,S1-T1
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
```

## After meeting 2 (S2): the whole memory (7 records)

```text
S1-T1 Uma: film.soundtrack = piano track [superseded] | sources=S1-T1
S1-T2 Vik: film.soundtrack = piano track [active] | sources=S1-T2,S1-T1
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T4 Xia: film.location = community studio [active] | sources=S1-T4,S1-T3
S1-T4 Xia: film.final_edit_deadline = 28 November [superseded] | sources=S1-T4
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
S2-T1 Vik: film.soundtrack = acoustic-guitar track [proposed] | sources=S2-T1
```

Shown for "When is the final edit due?" (`film.final_edit_deadline@S2`, a question about now):

```text
S1-T2 Vik: film.soundtrack = piano track [active] | sources=S1-T2,S1-T1
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T4 Xia: film.final_edit_deadline = 28 November [superseded] | sources=S1-T4
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
```

Shown for "Where are we filming?" (`film.location@S2`, a question about now):

```text
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T4 Xia: film.location = community studio [active] | sources=S1-T4,S1-T3
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
S2-T1 Vik: film.soundtrack = acoustic-guitar track [proposed] | sources=S2-T1
```

Shown for "Which soundtrack are we using for the film?" (`film.soundtrack@S2`, a question about now):

```text
S1-T1 Uma: film.soundtrack = piano track [superseded] | sources=S1-T1
S1-T2 Vik: film.soundtrack = piano track [active] | sources=S1-T2,S1-T1
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
S2-T1 Vik: film.soundtrack = acoustic-guitar track [proposed] | sources=S2-T1
```

## After meeting 3 (S3): the whole memory (8 records)

```text
S1-T1 Uma: film.soundtrack = piano track [superseded] | sources=S1-T1
S1-T2 Vik: film.soundtrack = piano track [superseded] | sources=S1-T2,S1-T1
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T4 Xia: film.location = community studio [active] | sources=S1-T4,S1-T3
S1-T4 Xia: film.final_edit_deadline = 28 November [superseded] | sources=S1-T4
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
S2-T1 Vik: film.soundtrack = acoustic-guitar track [superseded] | sources=S2-T1
S3-T2 Uma: film.soundtrack = acoustic-guitar track [active] | sources=S3-T2,S2-T1
```

Shown for "When is the final edit due?" (`film.final_edit_deadline@S3`, a question about now):

```text
S1-T2 Vik: film.soundtrack = piano track [superseded] | sources=S1-T2,S1-T1
S1-T4 Xia: film.final_edit_deadline = 28 November [superseded] | sources=S1-T4
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
S3-T2 Uma: film.soundtrack = acoustic-guitar track [active] | sources=S3-T2,S2-T1
```

Shown for "Where are we filming?" (`film.location@S3`, a question about now):

```text
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T4 Xia: film.location = community studio [active] | sources=S1-T4,S1-T3
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
S3-T2 Uma: film.soundtrack = acoustic-guitar track [active] | sources=S3-T2,S2-T1
```

Shown for "Which soundtrack are we using for the film?" (`film.soundtrack@S3`, a question about now):

```text
S1-T1 Uma: film.soundtrack = piano track [superseded] | sources=S1-T1
S1-T2 Vik: film.soundtrack = piano track [superseded] | sources=S1-T2,S1-T1
S2-T1 Vik: film.soundtrack = acoustic-guitar track [superseded] | sources=S2-T1
S3-T2 Uma: film.soundtrack = acoustic-guitar track [active] | sources=S3-T2,S2-T1
```

## After meeting 4 (S4): the whole memory (8 records)

```text
S1-T1 Uma: film.soundtrack = piano track [superseded] | sources=S1-T1
S1-T2 Vik: film.soundtrack = piano track [superseded] | sources=S1-T2,S1-T1
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T4 Xia: film.location = community studio [active] | sources=S1-T4,S1-T3
S1-T4 Xia: film.final_edit_deadline = 28 November [superseded] | sources=S1-T4
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
S2-T1 Vik: film.soundtrack = acoustic-guitar track [superseded] | sources=S2-T1
S3-T2 Uma: film.soundtrack = acoustic-guitar track [active] | sources=S3-T2,S2-T1
```

Shown for "When is the final edit due?" (`film.final_edit_deadline@S4`, a question about now):

```text
S1-T2 Vik: film.soundtrack = piano track [superseded] | sources=S1-T2,S1-T1
S1-T4 Xia: film.final_edit_deadline = 28 November [superseded] | sources=S1-T4
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
S3-T2 Uma: film.soundtrack = acoustic-guitar track [active] | sources=S3-T2,S2-T1
```

Shown for "Where are we filming?" (`film.location@S4`, a question about now):

```text
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T4 Xia: film.location = community studio [active] | sources=S1-T4,S1-T3
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
S3-T2 Uma: film.soundtrack = acoustic-guitar track [active] | sources=S3-T2,S2-T1
```

Shown for "Which soundtrack are we using for the film?" (`film.soundtrack@S4`, a question about now):

```text
S1-T1 Uma: film.soundtrack = piano track [superseded] | sources=S1-T1
S1-T2 Vik: film.soundtrack = piano track [superseded] | sources=S1-T2,S1-T1
S2-T1 Vik: film.soundtrack = acoustic-guitar track [superseded] | sources=S2-T1
S3-T2 Uma: film.soundtrack = acoustic-guitar track [active] | sources=S3-T2,S2-T1
```

Shown for "Which soundtrack, if any, did we use for the film before the current one?" (`film.soundtrack@S4-previous`, a question about the past):

```text
S1-T1 Uma: film.soundtrack = piano track [superseded] | sources=S1-T1
S1-T2 Vik: film.soundtrack = piano track [superseded] | sources=S1-T2,S1-T1
S1-T3 Wen: film.location = community studio [superseded] | sources=S1-T3
S1-T4 Xia: film.final_edit_deadline = 28 November [superseded] | sources=S1-T4
S1-T4 Xia: film.location = community studio [active] | sources=S1-T4,S1-T3
S1-T5 Uma: film.final_edit_deadline = 28 November [active] | sources=S1-T5,S1-T4
S2-T1 Vik: film.soundtrack = acoustic-guitar track [superseded] | sources=S2-T1
S3-T2 Uma: film.soundtrack = acoustic-guitar track [active] | sources=S3-T2,S2-T1
```
