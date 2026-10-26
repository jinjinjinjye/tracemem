# tracemem-controlled: memory after each meeting (dev-06, Haiku, freeze-deck settings, k = 4)

For each meeting: the whole memory after it, then, for each question about the present asked after it, the 4 lines the answering model was shown (k = 4: the 4 records closest to the question). A question about an earlier meeting or about history has its exact input in answerer-inputs.jsonl.

## After S1: the whole memory (2 records)

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [active] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [active] | sources=S1-T4
```

Shown for `audio.segmentation@S1`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [active] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [active] | sources=S1-T4
```

Shown for `model.asr@S1`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [active] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [active] | sources=S1-T4
```

## After S2: the whole memory (4 records)

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [active] | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small [active] | sources=S2-T4
S2-T6 Dana: output.format = SRT [active] | sources=S2-T6
```

Shown for `audio.segmentation@S2`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [active] | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small [active] | sources=S2-T4
S2-T6 Dana: output.format = SRT [active] | sources=S2-T6
```

Shown for `model.asr@S2`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [active] | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small [active] | sources=S2-T4
S2-T6 Dana: output.format = SRT [active] | sources=S2-T6
```

Shown for `output.format@S2`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [active] | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small [active] | sources=S2-T4
S2-T6 Dana: output.format = SRT [active] | sources=S2-T6
```

## After S3: the whole memory (5 records)

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [superseded] | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small [active] | sources=S2-T4
S2-T6 Dana: output.format = SRT [active] | sources=S2-T6
S3-T3 Rhea: audio.segmentation = voice activity detection [active] | sources=S3-T3
```

Shown for `audio.segmentation@S3`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [superseded] | sources=S1-T4
S2-T6 Dana: output.format = SRT [active] | sources=S2-T6
S3-T3 Rhea: audio.segmentation = voice activity detection [active] | sources=S3-T3
```

Shown for `model.asr@S3`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [superseded] | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small [active] | sources=S2-T4
S3-T3 Rhea: audio.segmentation = voice activity detection [active] | sources=S3-T3
```

Shown for `model.asr@S3-previous`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [superseded] | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small [active] | sources=S2-T4
S3-T3 Rhea: audio.segmentation = voice activity detection [active] | sources=S3-T3
```

Shown for `output.format@S3`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [superseded] | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small [active] | sources=S2-T4
S2-T6 Dana: output.format = SRT [active] | sources=S2-T6
```

## After S4: the whole memory (6 records)

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [superseded] | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small [active] | sources=S2-T4,S4-T5
S2-T6 Dana: output.format = SRT [superseded] | sources=S2-T6
S3-T3 Rhea: audio.segmentation = voice activity detection [active] | sources=S3-T3,S4-T5
S4-T3 Rhea: output.format = WebVTT [active] | sources=S4-T3,S4-T5
```

Shown for `audio.segmentation@S4`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [superseded] | sources=S1-T4
S3-T3 Rhea: audio.segmentation = voice activity detection [active] | sources=S3-T3,S4-T5
S4-T3 Rhea: output.format = WebVTT [active] | sources=S4-T3,S4-T5
```

Shown for `audio.segmentation@S4-previous`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [superseded] | sources=S1-T4
S2-T6 Dana: output.format = SRT [superseded] | sources=S2-T6
S3-T3 Rhea: audio.segmentation = voice activity detection [active] | sources=S3-T3,S4-T5
```

Shown for `model.asr@S4`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [superseded] | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small [active] | sources=S2-T4,S4-T5
S3-T3 Rhea: audio.segmentation = voice activity detection [active] | sources=S3-T3,S4-T5
```

Shown for `output.format@S4`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 [superseded] | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks [superseded] | sources=S1-T4
S2-T6 Dana: output.format = SRT [superseded] | sources=S2-T6
S4-T3 Rhea: output.format = WebVTT [active] | sources=S4-T3,S4-T5
```
