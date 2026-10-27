# mem0-classic: memory after each meeting (pilot-01, A5 repeat 1)

Each block is the memory text the answering model saw for the questions about the present asked after that meeting, exactly as sent. The budget held every record, so it is the whole memory. A question about the state at an earlier meeting may see less: its exact input is in answerer-inputs.jsonl.

## After S1 (6 records)

```text
S1-T1 Mei: model.sentiment = Current Mem0 memory: Decided to use BERT for the sentiment classifier because it is the safe choice. | sources=S1-T1
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "Decided to use BERT for the sentiment classifier because it is the safe choice."} | sources=S1-T1
S1-T2 Arun: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S1-T2",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S1-T2"],
  "speaker": "Arun",
  "text": "Sounds good. What do we report, plain accuracy?",
  "value": "accuracy"
} | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S1-T2\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S1-T2\"],\n  \"speaker\": \"Arun\",\n  \"text\": \"Sounds good. What do we report, plain accuracy?\",\n  \"value\": \"accuracy\"\n}"} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S1-T3",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S1-T3"],
  "speaker": "Mei",
  "text": "Yes, accuracy as the main metric for now.",
  "value": "accuracy"
} | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S1-T3\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S1-T3\"],\n  \"speaker\": \"Mei\",\n  \"text\": \"Yes, accuracy as the main metric for now.\",\n  \"value\": \"accuracy\"\n}"} | sources=S1-T3
```

## After S2 (8 records)

```text
S1-T1 Mei: model.sentiment = Current Mem0 memory: Decided to use BERT for the sentiment classifier because it is the safe choice. | sources=S1-T1
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "Decided to use BERT for the sentiment classifier because it is the safe choice."} | sources=S1-T1
S1-T2 Arun: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S1-T2",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S1-T2"],
  "speaker": "Arun",
  "text": "Sounds good. What do we report, plain accuracy?",
  "value": "accuracy"
} | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S1-T2\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S1-T2\"],\n  \"speaker\": \"Arun\",\n  \"text\": \"Sounds good. What do we report, plain accuracy?\",\n  \"value\": \"accuracy\"\n}"} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S1-T3",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S1-T3"],
  "speaker": "Mei",
  "text": "Yes, accuracy as the main metric for now.",
  "value": "accuracy"
} | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S1-T3\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S1-T3\"],\n  \"speaker\": \"Mei\",\n  \"text\": \"Yes, accuracy as the main metric for now.\",\n  \"value\": \"accuracy\"\n}"} | sources=S1-T3
S2-T5 Mei: model.ner = Current Mem0 memory: Separately, for the NER part we'll use a spaCy model. | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "Separately, for the NER part we'll use a spaCy model."} | sources=S2-T5
```

## After S3 (13 records)

```text
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "Decided to use BERT for the sentiment classifier because it is the safe choice."} | sources=S1-T1
S1-T2 Arun: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S1-T2",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S1-T2"],
  "speaker": "Arun",
  "text": "Sounds good. What do we report, plain accuracy?",
  "value": "accuracy"
} | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S1-T2\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S1-T2\"],\n  \"speaker\": \"Arun\",\n  \"text\": \"Sounds good. What do we report, plain accuracy?\",\n  \"value\": \"accuracy\"\n}"} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S1-T3",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S1-T3"],
  "speaker": "Mei",
  "text": "Yes, accuracy as the main metric for now.",
  "value": "accuracy"
} | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S1-T3\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S1-T3\"],\n  \"speaker\": \"Mei\",\n  \"text\": \"Yes, accuracy as the main metric for now.\",\n  \"value\": \"accuracy\"\n}"} | sources=S1-T3
S2-T5 Mei: model.ner = Current Mem0 memory: Separately, for the NER part we'll use a spaCy model. | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "Separately, for the NER part we'll use a spaCy model."} | sources=S2-T5
S3-T2 Mei: model.sentiment = Current Mem0 memory: Changed the sentiment classifier from BERT to DistilBERT, as BERT misses the latency limit. | sources=S3-T2,S1-T1
S3-T2 Mei: model.sentiment = {"mem0_history": "UPDATE", "before": "Decided to use BERT for the sentiment classifier because it is the safe choice.", "after": "Changed the sentiment classifier from BERT to DistilBERT, as BERT misses the latency limit."} | sources=S3-T2,S1-T1
S3-T3 Arun: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S3-T3",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S3-T3"],
  "speaker": "Arun",
  "text": "With an 80/20 split, accuracy will flatter us. Should we use macro-F1?",
  "value": "macro-F1"
} | sources=S3-T3
S3-T3 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S3-T3\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S3-T3\"],\n  \"speaker\": \"Arun\",\n  \"text\": \"With an 80/20 split, accuracy will flatter us. Should we use macro-F1?\",\n  \"value\": \"macro-F1\"\n}"} | sources=S3-T3
S3-T4 Mei: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S3-T4",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S3-T4"],
  "speaker": "Mei",
  "text": "Agreed, macro-F1 is the primary metric from now on.",
  "value": "macro-F1"
} | sources=S3-T4
S3-T4 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S3-T4\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S3-T4\"],\n  \"speaker\": \"Mei\",\n  \"text\": \"Agreed, macro-F1 is the primary metric from now on.\",\n  \"value\": \"macro-F1\"\n}"} | sources=S3-T4
```

## After S4 (17 records)

```text
S1-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "Decided to use BERT for the sentiment classifier because it is the safe choice."} | sources=S1-T1
S1-T2 Arun: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S1-T2",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S1-T2"],
  "speaker": "Arun",
  "text": "Sounds good. What do we report, plain accuracy?",
  "value": "accuracy"
} | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S1-T2\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S1-T2\"],\n  \"speaker\": \"Arun\",\n  \"text\": \"Sounds good. What do we report, plain accuracy?\",\n  \"value\": \"accuracy\"\n}"} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S1-T3",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S1-T3"],
  "speaker": "Mei",
  "text": "Yes, accuracy as the main metric for now.",
  "value": "accuracy"
} | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S1-T3\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S1-T3\"],\n  \"speaker\": \"Mei\",\n  \"text\": \"Yes, accuracy as the main metric for now.\",\n  \"value\": \"accuracy\"\n}"} | sources=S1-T3
S2-T5 Mei: model.ner = Current Mem0 memory: Separately, for the NER part we'll use a spaCy model. | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "Separately, for the NER part we'll use a spaCy model."} | sources=S2-T5
S3-T2 Mei: model.sentiment = Current Mem0 memory: Changed the sentiment classifier from BERT to DistilBERT, as BERT misses the latency limit. | sources=S3-T2,S1-T1
S3-T2 Mei: model.sentiment = {"mem0_history": "UPDATE", "before": "Decided to use BERT for the sentiment classifier because it is the safe choice.", "after": "Changed the sentiment classifier from BERT to DistilBERT, as BERT misses the latency limit."} | sources=S3-T2,S1-T1
S3-T3 Arun: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S3-T3",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S3-T3"],
  "speaker": "Arun",
  "text": "With an 80/20 split, accuracy will flatter us. Should we use macro-F1?",
  "value": "macro-F1"
} | sources=S3-T3
S3-T3 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S3-T3\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S3-T3\"],\n  \"speaker\": \"Arun\",\n  \"text\": \"With an 80/20 split, accuracy will flatter us. Should we use macro-F1?\",\n  \"value\": \"macro-F1\"\n}"} | sources=S3-T3
S3-T4 Mei: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S3-T4",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S3-T4"],
  "speaker": "Mei",
  "text": "Agreed, macro-F1 is the primary metric from now on.",
  "value": "macro-F1"
} | sources=S3-T4
S3-T4 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S3-T4\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S3-T4\"],\n  \"speaker\": \"Mei\",\n  \"text\": \"Agreed, macro-F1 is the primary metric from now on.\",\n  \"value\": \"macro-F1\"\n}"} | sources=S3-T4
S4-T1 Mei: metric.primary = Current Mem0 memory: {
  "candidate_id": "metric.primary@S4-T1",
  "item": "metric.primary",
  "project_id": "sentiment-project",
  "source_turn_ids": ["S4-T1"],
  "speaker": "Mei",
  "text": "For the write-up: we're on DistilBERT, scored with macro-F1.",
  "value": "macro-F1"
} | sources=S4-T1
S4-T1 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\n  \"candidate_id\": \"metric.primary@S4-T1\",\n  \"item\": \"metric.primary\",\n  \"project_id\": \"sentiment-project\",\n  \"source_turn_ids\": [\"S4-T1\"],\n  \"speaker\": \"Mei\",\n  \"text\": \"For the write-up: we're on DistilBERT, scored with macro-F1.\",\n  \"value\": \"macro-F1\"\n}"} | sources=S4-T1
S4-T1 Mei: model.sentiment = Current Mem0 memory: For the write-up: we're on DistilBERT, scored with macro-F1. | sources=S4-T1
S4-T1 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "For the write-up: we're on DistilBERT, scored with macro-F1."} | sources=S4-T1
```
