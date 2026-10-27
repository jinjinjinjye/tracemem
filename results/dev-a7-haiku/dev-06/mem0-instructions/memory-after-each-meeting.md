# mem0-instructions: memory after each meeting (dev-06, Haiku, freeze-deck settings, k = 4)

For each meeting: the whole memory after it, then, for each question about the present asked after it, the 4 lines the answering model was shown (k = 4: the 4 records closest to the question). A question about an earlier meeting or about history has its exact input in answerer-inputs.jsonl.

## After S1: the whole memory (4 records)

```text
S1-T2 Felix: model.asr = Current Mem0 memory: model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2) | sources=S1-T2
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
```

Shown for `audio.segmentation@S1`:

```text
S1-T2 Felix: model.asr = Current Mem0 memory: model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2) | sources=S1-T2
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
```

Shown for `model.asr@S1`:

```text
S1-T2 Felix: model.asr = Current Mem0 memory: model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2) | sources=S1-T2
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
```

## After S2: the whole memory (7 records)

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
S2-T4 Rhea: model.asr = Current Mem0 memory: model.asr (project lecture-captions): Whisper small chosen as the recognizer, per Rhea (S2-T4) | sources=S2-T4,S1-T2
S2-T4 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)", "after": "model.asr (project lecture-captions): Whisper small chosen as the recognizer, per Rhea (S2-T4)"} | sources=S2-T4,S1-T2
S2-T6 Dana: output.format = Current Mem0 memory: Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value) | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value)"} | sources=S2-T6
```

Shown for `audio.segmentation@S2`:

```text
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
S2-T6 Dana: output.format = Current Mem0 memory: Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value) | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value)"} | sources=S2-T6
```

Shown for `model.asr@S2`:

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
S2-T6 Dana: output.format = Current Mem0 memory: Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value) | sources=S2-T6
```

Shown for `output.format@S2`:

```text
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
S2-T6 Dana: output.format = Current Mem0 memory: Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value) | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value)"} | sources=S2-T6
```

## After S3: the whole memory (9 records)

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
S2-T4 Rhea: model.asr = Current Mem0 memory: model.asr (project lecture-captions): Whisper small chosen as the recognizer, per Rhea (S2-T4) | sources=S2-T4,S1-T2
S2-T4 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)", "after": "model.asr (project lecture-captions): Whisper small chosen as the recognizer, per Rhea (S2-T4)"} | sources=S2-T4,S1-T2
S2-T6 Dana: output.format = Current Mem0 memory: Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value) | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value)"} | sources=S2-T6
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed) | sources=S3-T3
S3-T3 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed)"} | sources=S3-T3
```

Shown for `audio.segmentation@S3`:

```text
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed) | sources=S3-T3
S3-T3 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed)"} | sources=S3-T3
```

Shown for `model.asr@S3`:

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S2-T6 Dana: output.format = Current Mem0 memory: Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value) | sources=S2-T6
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed) | sources=S3-T3
```

Shown for `model.asr@S3-previous`:

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S2-T6 Dana: output.format = Current Mem0 memory: Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value) | sources=S2-T6
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed) | sources=S3-T3
```

Shown for `output.format@S3`:

```text
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
S2-T6 Dana: output.format = Current Mem0 memory: Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value) | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value)"} | sources=S2-T6
```

## After S4: the whole memory (11 records)

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
S2-T4 Rhea: model.asr = Current Mem0 memory: model.asr (project lecture-captions): Whisper small chosen as the recognizer, per Rhea (S2-T4) | sources=S2-T4,S1-T2
S2-T4 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)", "after": "model.asr (project lecture-captions): Whisper small chosen as the recognizer, per Rhea (S2-T4)"} | sources=S2-T4,S1-T2
S2-T6 Dana: output.format = Current Mem0 memory: Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value) | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value)"} | sources=S2-T6
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed) | sources=S3-T3
S3-T3 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed)"} | sources=S3-T3
S4-T3 Rhea: output.format = Current Mem0 memory: Active output.format = WebVTT for project lecture-captions (committed by Rhea in S4-T3: "we export WebVTT instead of SRT from now on") | sources=S4-T3
S4-T3 Rhea: output.format = {"mem0_history": "ADD", "before": null, "after": "Active output.format = WebVTT for project lecture-captions (committed by Rhea in S4-T3: \"we export WebVTT instead of SRT from now on\")"} | sources=S4-T3
```

Shown for `audio.segmentation@S4`:

```text
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed) | sources=S3-T3
S3-T3 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed)"} | sources=S3-T3
```

Shown for `audio.segmentation@S4-previous`:

```text
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): fixed 30-second chunks"} | sources=S1-T4
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed) | sources=S3-T3
S3-T3 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed)"} | sources=S3-T3
```

Shown for `model.asr@S4`:

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "model.asr (project lecture-captions): wav2vec 2.0 chosen as the recognizer, per Felix (S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): fixed 30-second chunks | sources=S1-T4
S2-T6 Dana: output.format = Current Mem0 memory: Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value) | sources=S2-T6
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation (project lecture-captions): proposed voice activity detection split (ADD-proposed, not yet confirmed) | sources=S3-T3
```

Shown for `output.format@S4`:

```text
S2-T6 Dana: output.format = Current Mem0 memory: Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value) | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Proposed output.format = SRT for project lecture-captions (suggested by Dana; not yet adopted as the settled value)"} | sources=S2-T6
S4-T3 Rhea: output.format = Current Mem0 memory: Active output.format = WebVTT for project lecture-captions (committed by Rhea in S4-T3: "we export WebVTT instead of SRT from now on") | sources=S4-T3
S4-T3 Rhea: output.format = {"mem0_history": "ADD", "before": null, "after": "Active output.format = WebVTT for project lecture-captions (committed by Rhea in S4-T3: \"we export WebVTT instead of SRT from now on\")"} | sources=S4-T3
```
