# report-c15 ("Preparing a Dumpling Workshop"): TraceMem's memory at each meeting with questions

Run 1 of 3 on Claude Haiku 5.5 at the final frozen settings (freeze-v1). For each meeting after which questions were asked: TraceMem's whole memory at that point, then, for each question, the lines the answering model was shown. A question about now was shown the 4 memory lines closest to it (all of them when memory held fewer); a question about the past was shown every line that fitted (here, all of them).

How to read a line: `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) and `declined` (a dispute that lost).

## After meeting 1 (S1): the whole memory (2 records)

```text
S1-T1 Aisha: task.recipe_cards = open [active] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [active] | sources=S1-T2
```

Shown for "What is the status of our ingredient-check task?" (`task.ingredient_check@S1`, a question about now):

```text
S1-T1 Aisha: task.recipe_cards = open [active] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [active] | sources=S1-T2
```

Shown for "What is the status of the recipe-card task?" (`task.recipe_cards@S1`, a question about now):

```text
S1-T1 Aisha: task.recipe_cards = open [active] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [active] | sources=S1-T2
```

## After meeting 2 (S2): the whole memory (3 records)

```text
S1-T1 Aisha: task.recipe_cards = open [superseded] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [active] | sources=S1-T2
S2-T1 Aisha: task.recipe_cards = blocked [active] | sources=S2-T1
```

Shown for "What is the status of our ingredient-check task?" (`task.ingredient_check@S2`, a question about now):

```text
S1-T1 Aisha: task.recipe_cards = open [superseded] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [active] | sources=S1-T2
S2-T1 Aisha: task.recipe_cards = blocked [active] | sources=S2-T1
```

Shown for "What is the status of the recipe-card task?" (`task.recipe_cards@S2`, a question about now):

```text
S1-T1 Aisha: task.recipe_cards = open [superseded] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [active] | sources=S1-T2
S2-T1 Aisha: task.recipe_cards = blocked [active] | sources=S2-T1
```

## After meeting 3 (S3): the whole memory (5 records)

```text
S1-T1 Aisha: task.recipe_cards = open [superseded] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [superseded] | sources=S1-T2
S2-T1 Aisha: task.recipe_cards = blocked [superseded] | sources=S2-T1
S3-T2 Aisha: task.recipe_cards = open [active] | sources=S3-T2
S3-T3 Leah: task.ingredient_check = cancelled [active] | sources=S3-T3
```

Shown for "What is the status of our ingredient-check task?" (`task.ingredient_check@S3`, a question about now):

```text
S1-T2 Dmitri: task.ingredient_check = open [superseded] | sources=S1-T2
S2-T1 Aisha: task.recipe_cards = blocked [superseded] | sources=S2-T1
S3-T2 Aisha: task.recipe_cards = open [active] | sources=S3-T2
S3-T3 Leah: task.ingredient_check = cancelled [active] | sources=S3-T3
```

Shown for "What is the status of the recipe-card task?" (`task.recipe_cards@S3`, a question about now):

```text
S1-T1 Aisha: task.recipe_cards = open [superseded] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [superseded] | sources=S1-T2
S2-T1 Aisha: task.recipe_cards = blocked [superseded] | sources=S2-T1
S3-T2 Aisha: task.recipe_cards = open [active] | sources=S3-T2
```

## After meeting 4 (S4): the whole memory (6 records)

```text
S1-T1 Aisha: task.recipe_cards = open [superseded] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [superseded] | sources=S1-T2
S2-T1 Aisha: task.recipe_cards = blocked [superseded] | sources=S2-T1
S3-T2 Aisha: task.recipe_cards = open [active] | sources=S3-T2
S3-T3 Leah: task.ingredient_check = cancelled [active] | sources=S3-T3
S4-T2 Dmitri: task.ingredient_check = open [proposed] | sources=S4-T2
```

Shown for "What is the status of our ingredient-check task?" (`task.ingredient_check@S4`, a question about now):

```text
S1-T2 Dmitri: task.ingredient_check = open [superseded] | sources=S1-T2
S2-T1 Aisha: task.recipe_cards = blocked [superseded] | sources=S2-T1
S3-T3 Leah: task.ingredient_check = cancelled [active] | sources=S3-T3
S4-T2 Dmitri: task.ingredient_check = open [proposed] | sources=S4-T2
```

Shown for "What is the status of the recipe-card task?" (`task.recipe_cards@S4`, a question about now):

```text
S1-T1 Aisha: task.recipe_cards = open [superseded] | sources=S1-T1
S2-T1 Aisha: task.recipe_cards = blocked [superseded] | sources=S2-T1
S3-T2 Aisha: task.recipe_cards = open [active] | sources=S3-T2
S4-T2 Dmitri: task.ingredient_check = open [proposed] | sources=S4-T2
```

## After meeting 5 (S5): the whole memory (7 records)

```text
S1-T1 Aisha: task.recipe_cards = open [superseded] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [superseded] | sources=S1-T2
S2-T1 Aisha: task.recipe_cards = blocked [superseded] | sources=S2-T1
S3-T2 Aisha: task.recipe_cards = open [superseded] | sources=S3-T2
S3-T3 Leah: task.ingredient_check = cancelled [active] | sources=S3-T3,S5-T4
S4-T2 Dmitri: task.ingredient_check = open [proposed] | sources=S4-T2
S5-T1 Aisha: task.recipe_cards = completed [active] | sources=S5-T1
```

Shown for "What is the status of our ingredient-check task?" (`task.ingredient_check@S5`, a question about now):

```text
S1-T2 Dmitri: task.ingredient_check = open [superseded] | sources=S1-T2
S3-T3 Leah: task.ingredient_check = cancelled [active] | sources=S3-T3,S5-T4
S4-T2 Dmitri: task.ingredient_check = open [proposed] | sources=S4-T2
S5-T1 Aisha: task.recipe_cards = completed [active] | sources=S5-T1
```

Shown for "What status, if any, did the ingredient-check task have before the current one?" (`task.ingredient_check@S5-previous`, a question about the past):

```text
S1-T1 Aisha: task.recipe_cards = open [superseded] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [superseded] | sources=S1-T2
S2-T1 Aisha: task.recipe_cards = blocked [superseded] | sources=S2-T1
S3-T2 Aisha: task.recipe_cards = open [superseded] | sources=S3-T2
S3-T3 Leah: task.ingredient_check = cancelled [active] | sources=S3-T3,S5-T4
S4-T2 Dmitri: task.ingredient_check = open [proposed] | sources=S4-T2
S5-T1 Aisha: task.recipe_cards = completed [active] | sources=S5-T1
```

Shown for "What is the status of the recipe-card task?" (`task.recipe_cards@S5`, a question about now):

```text
S1-T1 Aisha: task.recipe_cards = open [superseded] | sources=S1-T1
S2-T1 Aisha: task.recipe_cards = blocked [superseded] | sources=S2-T1
S3-T2 Aisha: task.recipe_cards = open [superseded] | sources=S3-T2
S5-T1 Aisha: task.recipe_cards = completed [active] | sources=S5-T1
```

Shown for "What status, if any, did the recipe-card task have before the current one?" (`task.recipe_cards@S5-previous`, a question about the past):

```text
S1-T1 Aisha: task.recipe_cards = open [superseded] | sources=S1-T1
S1-T2 Dmitri: task.ingredient_check = open [superseded] | sources=S1-T2
S2-T1 Aisha: task.recipe_cards = blocked [superseded] | sources=S2-T1
S3-T2 Aisha: task.recipe_cards = open [superseded] | sources=S3-T2
S3-T3 Leah: task.ingredient_check = cancelled [active] | sources=S3-T3,S5-T4
S4-T2 Dmitri: task.ingredient_check = open [proposed] | sources=S4-T2
S5-T1 Aisha: task.recipe_cards = completed [active] | sources=S5-T1
```
