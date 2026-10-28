# deck-c09 ("Testing an AI Revision Helper"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer). This scenario has no question about the past.

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (2 records)

```text
S1-T1 Nina: test.material = cleaned-up lecture notes [superseded] | sources=S1-T1
S1-T5 Arun: test.material = cleaned-up lecture notes [active] | sources=S1-T5,S1-T1
```

Shown for "What is the main evaluation criterion?" (`eval.main_criterion@S1`, a question about now):

```text
S1-T1 Nina: test.material = cleaned-up lecture notes [superseded] | sources=S1-T1
S1-T5 Arun: test.material = cleaned-up lecture notes [active] | sources=S1-T5,S1-T1
```

Shown for "What material are we using for this round of testing?" (`test.material@S1`, a question about now):

```text
S1-T1 Nina: test.material = cleaned-up lecture notes [superseded] | sources=S1-T1
S1-T5 Arun: test.material = cleaned-up lecture notes [active] | sources=S1-T5,S1-T1
```

## After meeting 2 (S2): the whole memory (5 records)

```text
S1-T1 Nina: test.material = cleaned-up lecture notes [superseded] | sources=S1-T1
S1-T5 Arun: test.material = cleaned-up lecture notes [active] | sources=S1-T5,S1-T1,S2-T2
S2-T1 Beth: test.material = public question-and-answer dataset [proposed] | sources=S2-T1
S2-T4 Beth: eval.main_criterion = factual accuracy [superseded] | sources=S2-T4
S2-T5 Nina: eval.main_criterion = factual accuracy [active] | sources=S2-T5,S2-T4
```

Shown for "What is the main evaluation criterion?" (`eval.main_criterion@S2`, a question about now):

```text
S1-T5 Arun: test.material = cleaned-up lecture notes [active] | sources=S1-T5,S1-T1,S2-T2
S2-T1 Beth: test.material = public question-and-answer dataset [proposed] | sources=S2-T1
S2-T4 Beth: eval.main_criterion = factual accuracy [superseded] | sources=S2-T4
S2-T5 Nina: eval.main_criterion = factual accuracy [active] | sources=S2-T5,S2-T4
```

Shown for "What material are we using for this round of testing?" (`test.material@S2`, a question about now):

```text
S1-T1 Nina: test.material = cleaned-up lecture notes [superseded] | sources=S1-T1
S1-T5 Arun: test.material = cleaned-up lecture notes [active] | sources=S1-T5,S1-T1,S2-T2
S2-T1 Beth: test.material = public question-and-answer dataset [proposed] | sources=S2-T1
S2-T4 Beth: eval.main_criterion = factual accuracy [superseded] | sources=S2-T4
```

## After meeting 3 (S3): the whole memory (6 records)

```text
S1-T1 Nina: test.material = cleaned-up lecture notes [superseded] | sources=S1-T1
S1-T5 Arun: test.material = cleaned-up lecture notes [active] | sources=S1-T5,S1-T1,S2-T2
S2-T1 Beth: test.material = public question-and-answer dataset [proposed] | sources=S2-T1
S2-T4 Beth: eval.main_criterion = factual accuracy [superseded] | sources=S2-T4
S2-T5 Nina: eval.main_criterion = factual accuracy [active] | sources=S2-T5,S2-T4
S3-T1 Arun: test.material = cleaned-up lecture notes [proposed] | sources=S3-T1
```

Shown for "What is the main evaluation criterion?" (`eval.main_criterion@S3`, a question about now):

```text
S2-T1 Beth: test.material = public question-and-answer dataset [proposed] | sources=S2-T1
S2-T4 Beth: eval.main_criterion = factual accuracy [superseded] | sources=S2-T4
S2-T5 Nina: eval.main_criterion = factual accuracy [active] | sources=S2-T5,S2-T4
S3-T1 Arun: test.material = cleaned-up lecture notes [proposed] | sources=S3-T1
```

Shown for "What material are we using for this round of testing?" (`test.material@S3`, a question about now):

```text
S1-T1 Nina: test.material = cleaned-up lecture notes [superseded] | sources=S1-T1
S1-T5 Arun: test.material = cleaned-up lecture notes [active] | sources=S1-T5,S1-T1,S2-T2
S2-T1 Beth: test.material = public question-and-answer dataset [proposed] | sources=S2-T1
S3-T1 Arun: test.material = cleaned-up lecture notes [proposed] | sources=S3-T1
```
