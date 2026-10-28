# report-b11 ("Pet-sitting preparation progresses unevenly"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (4 records)

```text
S1-T1 Emi: task.pet_food = open [active] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [proposed] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
```

Shown for "What is the status of the key handover?" (`task.key_handover@S1`, a question about now):

```text
S1-T1 Emi: task.pet_food = open [active] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [proposed] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
```

Shown for "What is the status of the pet-food purchase?" (`task.pet_food@S1`, a question about now):

```text
S1-T1 Emi: task.pet_food = open [active] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [proposed] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
```

Shown for "When is the first pet-sitting visit?" (`visit.first_date@S1`, a question about now):

```text
S1-T1 Emi: task.pet_food = open [active] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [proposed] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
```

## After meeting 2 (S2): the whole memory (4 records)

```text
S1-T1 Emi: task.pet_food = open [active] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [proposed] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
```

Shown for "What is the status of the key handover?" (`task.key_handover@S2`, a question about now):

```text
S1-T1 Emi: task.pet_food = open [active] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [proposed] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
```

Shown for "What is the status of the pet-food purchase?" (`task.pet_food@S2`, a question about now):

```text
S1-T1 Emi: task.pet_food = open [active] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [proposed] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
```

Shown for "When is the first pet-sitting visit?" (`visit.first_date@S2`, a question about now):

```text
S1-T1 Emi: task.pet_food = open [active] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [proposed] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
```

## After meeting 3 (S3): the whole memory (5 records)

```text
S1-T1 Emi: task.pet_food = open [superseded] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [proposed] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
S3-T1 Emi: task.pet_food = completed [active] | sources=S3-T1
```

Shown for "What is the status of the key handover?" (`task.key_handover@S3`, a question about now):

```text
S1-T1 Emi: task.pet_food = open [superseded] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [proposed] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
```

Shown for "What is the status of the pet-food purchase?" (`task.pet_food@S3`, a question about now):

```text
S1-T1 Emi: task.pet_food = open [superseded] | sources=S1-T1
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
S3-T1 Emi: task.pet_food = completed [active] | sources=S3-T1
```

Shown for "When is the first pet-sitting visit?" (`visit.first_date@S3`, a question about now):

```text
S1-T1 Emi: task.pet_food = open [superseded] | sources=S1-T1
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3
S3-T1 Emi: task.pet_food = completed [active] | sources=S3-T1
```

## After meeting 4 (S4): the whole memory (6 records)

```text
S1-T1 Emi: task.pet_food = open [superseded] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [superseded] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3,S4-T5
S3-T1 Emi: task.pet_food = completed [active] | sources=S3-T1,S4-T2
S4-T2 Emi: task.key_handover = open [active] | sources=S4-T2,S1-T2
```

Shown for "What is the status of the key handover?" (`task.key_handover@S4`, a question about now):

```text
S1-T2 Farid: task.key_handover = open [superseded] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3,S4-T5
S4-T2 Emi: task.key_handover = open [active] | sources=S4-T2,S1-T2
```

Shown for "What is the status of the pet-food purchase?" (`task.pet_food@S4`, a question about now):

```text
S1-T1 Emi: task.pet_food = open [superseded] | sources=S1-T1
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3,S4-T5
S3-T1 Emi: task.pet_food = completed [active] | sources=S3-T1,S4-T2
```

Shown for "What status, if any, did the pet-food purchase have before the current one?" (`task.pet_food@S4-previous`, a question about the past):

```text
S1-T1 Emi: task.pet_food = open [superseded] | sources=S1-T1
S1-T2 Farid: task.key_handover = open [superseded] | sources=S1-T2
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3,S4-T5
S3-T1 Emi: task.pet_food = completed [active] | sources=S3-T1,S4-T2
S4-T2 Emi: task.key_handover = open [active] | sources=S4-T2,S1-T2
```

Shown for "When is the first pet-sitting visit?" (`visit.first_date@S4`, a question about now):

```text
S1-T1 Emi: task.pet_food = open [superseded] | sources=S1-T1
S1-T3 Emi: visit.first_date = 15 November [superseded] | sources=S1-T3
S1-T4 Farid: visit.first_date = 15 November [active] | sources=S1-T4,S1-T3,S4-T5
S3-T1 Emi: task.pet_food = completed [active] | sources=S3-T1,S4-T2
```
