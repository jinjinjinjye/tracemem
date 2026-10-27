# mem0-instructions: memory after each meeting (pilot-01, A5 repeat 1)

Each block is the memory text the answering model saw for the questions about the present asked after that meeting, exactly as sent. The budget held every record, so it is the whole memory. A question about the state at an earlier meeting may see less: its exact input is in answerer-inputs.jsonl.

## After S1 (4 records)

```text
S1-T2 Arun: metric.primary = Current Mem0 memory: { "candidate_id": "metric.primary@S1-T2", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S1-T2"], "speaker": "Arun", "text": "Sounds good. What do we report, plain accuracy?", "value": "accuracy" } | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{ \"candidate_id\": \"metric.primary@S1-T2\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S1-T2\"], \"speaker\": \"Arun\", \"text\": \"Sounds good. What do we report, plain accuracy?\", \"value\": \"accuracy\" }"} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: {"candidate_id": "metric.primary@S1-T3", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S1-T3"], "speaker": "Mei", "text": "Yes, accuracy as the main metric for now.", "value": "accuracy"} | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\"candidate_id\": \"metric.primary@S1-T3\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S1-T3\"], \"speaker\": \"Mei\", \"text\": \"Yes, accuracy as the main metric for now.\", \"value\": \"accuracy\"}"} | sources=S1-T3
```

## After S2 (8 records)

```text
S1-T2 Arun: metric.primary = Current Mem0 memory: { "candidate_id": "metric.primary@S1-T2", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S1-T2"], "speaker": "Arun", "text": "Sounds good. What do we report, plain accuracy?", "value": "accuracy" } | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{ \"candidate_id\": \"metric.primary@S1-T2\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S1-T2\"], \"speaker\": \"Arun\", \"text\": \"Sounds good. What do we report, plain accuracy?\", \"value\": \"accuracy\" }"} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: {"candidate_id": "metric.primary@S1-T3", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S1-T3"], "speaker": "Mei", "text": "Yes, accuracy as the main metric for now.", "value": "accuracy"} | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\"candidate_id\": \"metric.primary@S1-T3\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S1-T3\"], \"speaker\": \"Mei\", \"text\": \"Yes, accuracy as the main metric for now.\", \"value\": \"accuracy\"}"} | sources=S1-T3
S2-T3 Arun: model.sentiment = Current Mem0 memory: Maybe we could try DistilBERT? It might be faster. | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "Maybe we could try DistilBERT? It might be faster."} | sources=S2-T3
S2-T5 Mei: model.ner = Current Mem0 memory: "Separately, for the NER part we'll use a spaCy model.", value: "spaCy" | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "\"Separately, for the NER part we'll use a spaCy model.\", value: \"spaCy\""} | sources=S2-T5
```

## After S3 (14 records)

```text
S1-T2 Arun: metric.primary = Current Mem0 memory: { "candidate_id": "metric.primary@S1-T2", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S1-T2"], "speaker": "Arun", "text": "Sounds good. What do we report, plain accuracy?", "value": "accuracy" } | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{ \"candidate_id\": \"metric.primary@S1-T2\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S1-T2\"], \"speaker\": \"Arun\", \"text\": \"Sounds good. What do we report, plain accuracy?\", \"value\": \"accuracy\" }"} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: {"candidate_id": "metric.primary@S1-T3", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S1-T3"], "speaker": "Mei", "text": "Yes, accuracy as the main metric for now.", "value": "accuracy"} | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\"candidate_id\": \"metric.primary@S1-T3\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S1-T3\"], \"speaker\": \"Mei\", \"text\": \"Yes, accuracy as the main metric for now.\", \"value\": \"accuracy\"}"} | sources=S1-T3
S2-T3 Arun: model.sentiment = Current Mem0 memory: Maybe we could try DistilBERT? It might be faster. | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "Maybe we could try DistilBERT? It might be faster."} | sources=S2-T3
S2-T5 Mei: model.ner = Current Mem0 memory: "Separately, for the NER part we'll use a spaCy model.", value: "spaCy" | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "\"Separately, for the NER part we'll use a spaCy model.\", value: \"spaCy\""} | sources=S2-T5
S3-T2 Mei: model.sentiment = Current Mem0 memory: Then we switch the sentiment classifier to DistilBERT, since BERT misses the latency limit. | sources=S3-T2
S3-T2 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "Then we switch the sentiment classifier to DistilBERT, since BERT misses the latency limit."} | sources=S3-T2
S3-T3 Arun: metric.primary = Current Mem0 memory: {"candidate_id": "metric.primary@S3-T3", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S3-T3"], "speaker": "Arun", "text": "With an 80/20 split, accuracy will flatter us. Should we use macro-F1?", "value": "macro-F1"} | sources=S3-T3
S3-T3 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\"candidate_id\": \"metric.primary@S3-T3\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S3-T3\"], \"speaker\": \"Arun\", \"text\": \"With an 80/20 split, accuracy will flatter us. Should we use macro-F1?\", \"value\": \"macro-F1\"}"} | sources=S3-T3
S3-T4 Mei: metric.primary = Current Mem0 memory: { "candidate_id": "metric.primary@S3-T4", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S3-T4"], "speaker": "Mei", "text": "Agreed, macro-F1 is the primary metric from now on.", "value": "macro-F1" } | sources=S3-T4
S3-T4 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{ \"candidate_id\": \"metric.primary@S3-T4\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S3-T4\"], \"speaker\": \"Mei\", \"text\": \"Agreed, macro-F1 is the primary metric from now on.\", \"value\": \"macro-F1\" }"} | sources=S3-T4
```

## After S4 (16 records)

```text
S1-T2 Arun: metric.primary = Current Mem0 memory: { "candidate_id": "metric.primary@S1-T2", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S1-T2"], "speaker": "Arun", "text": "Sounds good. What do we report, plain accuracy?", "value": "accuracy" } | sources=S1-T2
S1-T2 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{ \"candidate_id\": \"metric.primary@S1-T2\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S1-T2\"], \"speaker\": \"Arun\", \"text\": \"Sounds good. What do we report, plain accuracy?\", \"value\": \"accuracy\" }"} | sources=S1-T2
S1-T3 Mei: metric.primary = Current Mem0 memory: {"candidate_id": "metric.primary@S1-T3", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S1-T3"], "speaker": "Mei", "text": "Yes, accuracy as the main metric for now.", "value": "accuracy"} | sources=S1-T3
S1-T3 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\"candidate_id\": \"metric.primary@S1-T3\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S1-T3\"], \"speaker\": \"Mei\", \"text\": \"Yes, accuracy as the main metric for now.\", \"value\": \"accuracy\"}"} | sources=S1-T3
S2-T3 Arun: model.sentiment = Current Mem0 memory: Maybe we could try DistilBERT? It might be faster. | sources=S2-T3
S2-T3 Arun: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "Maybe we could try DistilBERT? It might be faster."} | sources=S2-T3
S2-T5 Mei: model.ner = Current Mem0 memory: "Separately, for the NER part we'll use a spaCy model.", value: "spaCy" | sources=S2-T5
S2-T5 Mei: model.ner = {"mem0_history": "ADD", "before": null, "after": "\"Separately, for the NER part we'll use a spaCy model.\", value: \"spaCy\""} | sources=S2-T5
S3-T2 Mei: model.sentiment = Current Mem0 memory: Then we switch the sentiment classifier to DistilBERT, since BERT misses the latency limit. | sources=S3-T2
S3-T2 Mei: model.sentiment = {"mem0_history": "ADD", "before": null, "after": "Then we switch the sentiment classifier to DistilBERT, since BERT misses the latency limit."} | sources=S3-T2
S3-T3 Arun: metric.primary = Current Mem0 memory: {"candidate_id": "metric.primary@S3-T3", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S3-T3"], "speaker": "Arun", "text": "With an 80/20 split, accuracy will flatter us. Should we use macro-F1?", "value": "macro-F1"} | sources=S3-T3
S3-T3 Arun: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{\"candidate_id\": \"metric.primary@S3-T3\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S3-T3\"], \"speaker\": \"Arun\", \"text\": \"With an 80/20 split, accuracy will flatter us. Should we use macro-F1?\", \"value\": \"macro-F1\"}"} | sources=S3-T3
S3-T4 Mei: metric.primary = Current Mem0 memory: { "candidate_id": "metric.primary@S3-T4", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S3-T4"], "speaker": "Mei", "text": "Agreed, macro-F1 is the primary metric from now on.", "value": "macro-F1" } | sources=S3-T4
S3-T4 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{ \"candidate_id\": \"metric.primary@S3-T4\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S3-T4\"], \"speaker\": \"Mei\", \"text\": \"Agreed, macro-F1 is the primary metric from now on.\", \"value\": \"macro-F1\" }"} | sources=S3-T4
S4-T1 Mei: metric.primary = Current Mem0 memory: { "candidate_id": "metric.primary@S4-T1", "item": "metric.primary", "project_id": "sentiment-project", "source_turn_ids": ["S4-T1"], "speaker": "Mei", "text": "For the write-up: we're on DistilBERT, scored with macro-F1.", "value": "macro-F1" } | sources=S4-T1
S4-T1 Mei: metric.primary = {"mem0_history": "ADD", "before": null, "after": "{ \"candidate_id\": \"metric.primary@S4-T1\", \"item\": \"metric.primary\", \"project_id\": \"sentiment-project\", \"source_turn_ids\": [\"S4-T1\"], \"speaker\": \"Mei\", \"text\": \"For the write-up: we're on DistilBERT, scored with macro-F1.\", \"value\": \"macro-F1\" }"} | sources=S4-T1
```
