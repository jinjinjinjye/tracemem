# similarity: memory after each meeting (dev-06, Haiku, freeze-deck settings, k = 4)

For each meeting: the whole memory after it, then, for each question about the present asked after it, the 4 lines the answering model was shown (k = 4: the 4 records closest to the question). A question about an earlier meeting or about history has its exact input in answerer-inputs.jsonl.

## After S1: the whole memory (2 records)

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
```

Shown for `audio.segmentation@S1`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
```

Shown for `model.asr@S1`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
```

## After S2: the whole memory (4 records)

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small "Haiz, like that how to submit... Right, decision: we're switching to Whisper small instead of wav2vec 2.0 lah. It punctuates out of the box and handles the accents way better." | sources=S2-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
```

Shown for `audio.segmentation@S2`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small "Haiz, like that how to submit... Right, decision: we're switching to Whisper small instead of wav2vec 2.0 lah. It punctuates out of the box and handles the accents way better." | sources=S2-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
```

Shown for `model.asr@S2`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small "Haiz, like that how to submit... Right, decision: we're switching to Whisper small instead of wav2vec 2.0 lah. It punctuates out of the box and handles the accents way better." | sources=S2-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
```

Shown for `output.format@S2`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small "Haiz, like that how to submit... Right, decision: we're switching to Whisper small instead of wav2vec 2.0 lah. It punctuates out of the box and handles the accents way better." | sources=S2-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
```

## After S3: the whole memory (5 records)

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small "Haiz, like that how to submit... Right, decision: we're switching to Whisper small instead of wav2vec 2.0 lah. It punctuates out of the box and handles the accents way better." | sources=S2-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
S3-T3 Rhea: audio.segmentation = voice activity detection "Aiyah... Okay, then we split on voice activity detection instead of the fixed 30-second chunks, ya? So the cuts land in the pauses." | sources=S3-T3
```

Shown for `audio.segmentation@S3`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
S3-T3 Rhea: audio.segmentation = voice activity detection "Aiyah... Okay, then we split on voice activity detection instead of the fixed 30-second chunks, ya? So the cuts land in the pauses." | sources=S3-T3
```

Shown for `model.asr@S3`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
S3-T3 Rhea: audio.segmentation = voice activity detection "Aiyah... Okay, then we split on voice activity detection instead of the fixed 30-second chunks, ya? So the cuts land in the pauses." | sources=S3-T3
```

Shown for `model.asr@S3-previous`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small "Haiz, like that how to submit... Right, decision: we're switching to Whisper small instead of wav2vec 2.0 lah. It punctuates out of the box and handles the accents way better." | sources=S2-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
```

Shown for `output.format@S3`:

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small "Haiz, like that how to submit... Right, decision: we're switching to Whisper small instead of wav2vec 2.0 lah. It punctuates out of the box and handles the accents way better." | sources=S2-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
```

## After S4: the whole memory (9 records)

```text
S1-T2 Felix: model.asr = wav2vec 2.0 "For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with." | sources=S1-T2
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T4 Rhea: model.asr = Whisper small "Haiz, like that how to submit... Right, decision: we're switching to Whisper small instead of wav2vec 2.0 lah. It punctuates out of the box and handles the accents way better." | sources=S2-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
S3-T3 Rhea: audio.segmentation = voice activity detection "Aiyah... Okay, then we split on voice activity detection instead of the fixed 30-second chunks, ya? So the cuts land in the pauses." | sources=S3-T3
S4-T3 Rhea: output.format = WebVTT "Haiz, why always got problem one... Okay, then we export WebVTT instead of SRT from now on lah. The conversion is just a header line and different timestamp format." | sources=S4-T3
S4-T5 Rhea: model.asr = Whisper small "Great... So for the progress report: Whisper small, split with voice activity detection, captions as WebVTT. Hope nothing else goes wrong." | sources=S4-T5
S4-T5 Rhea: audio.segmentation = voice activity detection "Great... So for the progress report: Whisper small, split with voice activity detection, captions as WebVTT. Hope nothing else goes wrong." | sources=S4-T5
S4-T5 Rhea: output.format = WebVTT "Great... So for the progress report: Whisper small, split with voice activity detection, captions as WebVTT. Hope nothing else goes wrong." | sources=S4-T5
```

Shown for `audio.segmentation@S4`:

```text
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
S3-T3 Rhea: audio.segmentation = voice activity detection "Aiyah... Okay, then we split on voice activity detection instead of the fixed 30-second chunks, ya? So the cuts land in the pauses." | sources=S3-T3
S4-T5 Rhea: audio.segmentation = voice activity detection "Great... So for the progress report: Whisper small, split with voice activity detection, captions as WebVTT. Hope nothing else goes wrong." | sources=S4-T5
```

Shown for `audio.segmentation@S4-previous`:

```text
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
S3-T3 Rhea: audio.segmentation = voice activity detection "Aiyah... Okay, then we split on voice activity detection instead of the fixed 30-second chunks, ya? So the cuts land in the pauses." | sources=S3-T3
S4-T5 Rhea: audio.segmentation = voice activity detection "Great... So for the progress report: Whisper small, split with voice activity detection, captions as WebVTT. Hope nothing else goes wrong." | sources=S4-T5
```

Shown for `model.asr@S4`:

```text
S1-T4 Rhea: audio.segmentation = fixed 30-second chunks "The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks." | sources=S1-T4
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
S4-T5 Rhea: audio.segmentation = voice activity detection "Great... So for the progress report: Whisper small, split with voice activity detection, captions as WebVTT. Hope nothing else goes wrong." | sources=S4-T5
S4-T5 Rhea: model.asr = Whisper small "Great... So for the progress report: Whisper small, split with voice activity detection, captions as WebVTT. Hope nothing else goes wrong." | sources=S4-T5
```

Shown for `output.format@S4`:

```text
S2-T6 Dana: output.format = SRT "Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway." | sources=S2-T6
S4-T3 Rhea: output.format = WebVTT "Haiz, why always got problem one... Okay, then we export WebVTT instead of SRT from now on lah. The conversion is just a header line and different timestamp format." | sources=S4-T3
S4-T5 Rhea: model.asr = Whisper small "Great... So for the progress report: Whisper small, split with voice activity detection, captions as WebVTT. Hope nothing else goes wrong." | sources=S4-T5
S4-T5 Rhea: output.format = WebVTT "Great... So for the progress report: Whisper small, split with voice activity detection, captions as WebVTT. Hope nothing else goes wrong." | sources=S4-T5
```
