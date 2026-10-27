# mem0-classic: memory after each meeting (dev-06, Haiku, freeze-deck settings, k = 4)

For each meeting: the whole memory after it, then, for each question about the present asked after it, the 4 lines the answering model was shown (k = 4: the 4 records closest to the question). A question about an earlier meeting or about history has its exact input in answerer-inputs.jsonl.

## After S1: the whole memory (4 records)

```text
S1-T2 Felix: model.asr = Current Mem0 memory: For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2) | sources=S1-T2
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks. | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks."} | sources=S1-T4
```

Shown for `audio.segmentation@S1`:

```text
S1-T2 Felix: model.asr = Current Mem0 memory: For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2) | sources=S1-T2
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks. | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks."} | sources=S1-T4
```

Shown for `model.asr@S1`:

```text
S1-T2 Felix: model.asr = Current Mem0 memory: For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2) | sources=S1-T2
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks. | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks."} | sources=S1-T4
```

## After S2: the whole memory (7 records)

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks. | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks."} | sources=S1-T4
S2-T4 Rhea: model.asr = Current Mem0 memory: For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4) | sources=S2-T4,S1-T2
S2-T4 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)", "after": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4)"} | sources=S2-T4,S1-T2
S2-T6 Dana: output.format = Current Mem0 memory: Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses. | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses."} | sources=S2-T6
```

Shown for `audio.segmentation@S2`:

```text
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks. | sources=S1-T4
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks."} | sources=S1-T4
S2-T6 Dana: output.format = Current Mem0 memory: Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses. | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses."} | sources=S2-T6
```

Shown for `model.asr@S2`:

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks. | sources=S1-T4
S2-T4 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)", "after": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4)"} | sources=S2-T4,S1-T2
S2-T6 Dana: output.format = Current Mem0 memory: Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses. | sources=S2-T6
```

Shown for `output.format@S2`:

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S2-T4 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)", "after": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4)"} | sources=S2-T4,S1-T2
S2-T6 Dana: output.format = Current Mem0 memory: Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses. | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses."} | sources=S2-T6
```

## After S3: the whole memory (8 records)

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks."} | sources=S1-T4
S2-T4 Rhea: model.asr = Current Mem0 memory: For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4) | sources=S2-T4,S1-T2
S2-T4 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)", "after": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4)"} | sources=S2-T4,S1-T2
S2-T6 Dana: output.format = Current Mem0 memory: Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses. | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses."} | sources=S2-T6
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go. | sources=S3-T3,S1-T4
S3-T3 Rhea: audio.segmentation = {"mem0_history": "UPDATE", "before": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks.", "after": "audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go."} | sources=S3-T3,S1-T4
```

Shown for `audio.segmentation@S3`:

```text
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks."} | sources=S1-T4
S2-T6 Dana: output.format = Current Mem0 memory: Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses. | sources=S2-T6
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go. | sources=S3-T3,S1-T4
S3-T3 Rhea: audio.segmentation = {"mem0_history": "UPDATE", "before": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks.", "after": "audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go."} | sources=S3-T3,S1-T4
```

Shown for `model.asr@S3`:

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S2-T4 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)", "after": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4)"} | sources=S2-T4,S1-T2
S2-T6 Dana: output.format = Current Mem0 memory: Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses. | sources=S2-T6
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go. | sources=S3-T3,S1-T4
```

Shown for `model.asr@S3-previous`:

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S2-T4 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)", "after": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4)"} | sources=S2-T4,S1-T2
S2-T6 Dana: output.format = Current Mem0 memory: Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses. | sources=S2-T6
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go. | sources=S3-T3,S1-T4
```

Shown for `output.format@S3`:

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S2-T4 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)", "after": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4)"} | sources=S2-T4,S1-T2
S2-T6 Dana: output.format = Current Mem0 memory: Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses. | sources=S2-T6
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses."} | sources=S2-T6
```

## After S4: the whole memory (12 records)

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks."} | sources=S1-T4
S2-T4 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)", "after": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4)"} | sources=S2-T4,S1-T2
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses."} | sources=S2-T6
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go. | sources=S3-T3,S1-T4
S3-T3 Rhea: audio.segmentation = {"mem0_history": "UPDATE", "before": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks.", "after": "audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go."} | sources=S3-T3,S1-T4
S4-T3 Rhea: output.format = Current Mem0 memory: Project lecture-captions: output.format is WebVTT. Rhea said to export WebVTT instead of SRT from now on, since the conversion is just a header line and a different timestamp format. | sources=S4-T3,S2-T6
S4-T3 Rhea: output.format = {"mem0_history": "UPDATE", "before": "Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses.", "after": "Project lecture-captions: output.format is WebVTT. Rhea said to export WebVTT instead of SRT from now on, since the conversion is just a header line and a different timestamp format."} | sources=S4-T3,S2-T6
S4-T5 Rhea: audio.segmentation = Current Mem0 memory: Progress report (project: lecture-captions, speaker: Rhea): ASR model is Whisper small, and captions are output as WebVTT. | sources=S4-T5
S4-T5 Rhea: model.asr = Current Mem0 memory: For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better; audio is split with voice activity detection and captions are output as WebVTT (speaker: Rhea, source turns: S2-T4, S4-T5) | sources=S4-T5,S1-T2,S2-T4
S4-T5 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4)", "after": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better; audio is split with voice activity detection and captions are output as WebVTT (speaker: Rhea, source turns: S2-T4, S4-T5)"} | sources=S4-T5,S1-T2,S2-T4
S4-T5 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "Progress report (project: lecture-captions, speaker: Rhea): ASR model is Whisper small, and captions are output as WebVTT."} | sources=S4-T5
```

Shown for `audio.segmentation@S4`:

```text
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks."} | sources=S1-T4
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go. | sources=S3-T3,S1-T4
S3-T3 Rhea: audio.segmentation = {"mem0_history": "UPDATE", "before": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks.", "after": "audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go."} | sources=S3-T3,S1-T4
S4-T5 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "Progress report (project: lecture-captions, speaker: Rhea): ASR model is Whisper small, and captions are output as WebVTT."} | sources=S4-T5
```

Shown for `audio.segmentation@S4-previous`:

```text
S1-T4 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks."} | sources=S1-T4
S3-T3 Rhea: audio.segmentation = Current Mem0 memory: audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go. | sources=S3-T3,S1-T4
S3-T3 Rhea: audio.segmentation = {"mem0_history": "UPDATE", "before": "audio.segmentation: fixed 30-second chunks (project: lecture-captions, speaker: Rhea). The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks.", "after": "audio.segmentation: split on voice activity detection so cuts land in pauses (project: lecture-captions, speaker: Rhea). The lectures are an hour each, so they are too long to process in one go."} | sources=S3-T3,S1-T4
S4-T5 Rhea: audio.segmentation = {"mem0_history": "ADD", "before": null, "after": "Progress report (project: lecture-captions, speaker: Rhea): ASR model is Whisper small, and captions are output as WebVTT."} | sources=S4-T5
```

Shown for `model.asr@S4`:

```text
S1-T2 Felix: model.asr = {"mem0_history": "ADD", "before": null, "after": "For the lecture-captions project, the model.asr (recognizer) is wav2vec 2.0, using a base checkpoint fine-tuned on LibriSpeech (speaker: Felix, source turn: S1-T2)"} | sources=S1-T2
S4-T5 Rhea: audio.segmentation = Current Mem0 memory: Progress report (project: lecture-captions, speaker: Rhea): ASR model is Whisper small, and captions are output as WebVTT. | sources=S4-T5
S4-T5 Rhea: model.asr = Current Mem0 memory: For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better; audio is split with voice activity detection and captions are output as WebVTT (speaker: Rhea, source turns: S2-T4, S4-T5) | sources=S4-T5,S1-T2,S2-T4
S4-T5 Rhea: model.asr = {"mem0_history": "UPDATE", "before": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better (speaker: Rhea, source turn: S2-T4)", "after": "For the lecture-captions project, the model.asr (recognizer) is Whisper small, chosen over wav2vec 2.0 because it punctuates out of the box and handles accents better; audio is split with voice activity detection and captions are output as WebVTT (speaker: Rhea, source turns: S2-T4, S4-T5)"} | sources=S4-T5,S1-T2,S2-T4
```

Shown for `output.format@S4`:

```text
S2-T6 Dana: output.format = {"mem0_history": "ADD", "before": null, "after": "Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses."} | sources=S2-T6
S4-T3 Rhea: output.format = Current Mem0 memory: Project lecture-captions: output.format is WebVTT. Rhea said to export WebVTT instead of SRT from now on, since the conversion is just a header line and a different timestamp format. | sources=S4-T3,S2-T6
S4-T3 Rhea: output.format = {"mem0_history": "UPDATE", "before": "Project lecture-captions: output.format is SRT. Dana said the lecture portal needs caption files and to export SRT since it's what everyone uses.", "after": "Project lecture-captions: output.format is WebVTT. Rhea said to export WebVTT instead of SRT from now on, since the conversion is just a header line and a different timestamp format."} | sources=S4-T3,S2-T6
S4-T5 Rhea: audio.segmentation = Current Mem0 memory: Progress report (project: lecture-captions, speaker: Rhea): ASR model is Whisper small, and captions are output as WebVTT. | sources=S4-T5
```
