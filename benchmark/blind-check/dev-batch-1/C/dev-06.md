# dev-06

## S1 (2026-10-06)
S1-T1 Rhea: Okay... goal is captions for the department's recorded lectures. Forty hours of audio to get through. Sigh.  
S1-T2 Felix: For the recognizer, just use wav2vec 2.0. Got a base checkpoint fine-tuned on LibriSpeech already, so can start straight away. Let's just get this over with.  
S1-T3 Dana: Yeah, whatever. Works for me.  
S1-T4 Rhea: The lectures are an hour each... too long to push through at one go. Just cut them into fixed 30-second chunks.  
S1-T5 Dana: I guess I'll hand-correct transcripts for three lectures. Just so we have a baseline.  
S1-T6 Felix: Right. Same time Friday then.  

## S2 (2026-10-09)
S2-T1 Dana: Reference transcripts for those three lectures are done. Dropped them in the shared folder. That took forever.  
S2-T2 Felix: First pass is done. Word error rate is like 34 percent. And the output got zero punctuation or capitals. Great.  
S2-T3 Dana: It also completely messes up the lecturer's accent and literally every stats term. 'Heteroscedasticity' comes out as four random words. So dumb.  
S2-T4 Rhea: Haiz, like that how to submit... Right, decision: we're switching to Whisper small instead of wav2vec 2.0 lah. It punctuates out of the box and handles the accents way better.  
S2-T5 Felix: Fine lor. I'll just rerun the three lectures over the weekend. Weekend gone.  
S2-T6 Dana: Oh, by the way, the lecture portal needs caption files. Let's just export SRT, it's what everyone uses anyway.  
S2-T7 Rhea: Sure... whatever is easiest.  

## S3 (2026-10-13)
S3-T1 Felix: The rerun's done. Word error rate down to 14 percent. Punctuation actually looks decent for once.  
S3-T2 Dana: Most of the errors left are right at the cut points, though. Words are literally getting sliced in half every thirty seconds. Annoying.  
S3-T3 Rhea: Aiyah... Okay, then we split on voice activity detection instead of the fixed 30-second chunks, ya? So the cuts land in the pauses.  
S3-T4 Felix: Makes sense. Lecturers pause all the time anyway.  
S3-T5 Dana: Ugh. I'll rewrite the segmentation script tonight, I guess.  

## S4 (2026-10-16)
S4-T1 Dana: New segments are in. We're at 11 percent on the three reference lectures now. So that's something.  
S4-T2 Felix: Bad news from the portal side. I uploaded a test caption file and the player shows nothing. Turns out it doesn't even read our files at all sia. Waste my time.  
S4-T3 Rhea: Haiz, why always got problem one... Okay, then we export WebVTT instead of SRT from now on lah. The conversion is just a header line and different timestamp format.  
S4-T4 Dana: I can patch the export script today. Whatever.  
S4-T5 Rhea: Great... So for the progress report: Whisper small, split with voice activity detection, captions as WebVTT. Hope nothing else goes wrong.  
S4-T6 Felix: I'll just put the numbers table together.  

## Questions (answer each from the dialogue alone: a value, `none` or `disputed`; see the guide)
- after S1: How are we splitting the lecture audio before transcribing it?
- after S1: Which speech-to-text model are we using for the lecture recordings?
- after S2: How are we splitting the lecture audio before transcribing it?
- after S2: Which speech-to-text model are we using for the lecture recordings?
- after S2: Which caption file format are we exporting?
- after S3: How are we splitting the lecture audio before transcribing it?
- after S3: Which speech-to-text model are we using for the lecture recordings?
- after S3: Which speech-to-text model, if any, did we use for the lecture recordings before the current one?
- after S3: Which caption file format are we exporting?
- after S4: How are we splitting the lecture audio before transcribing it?
- after S4: Which audio-splitting method, if any, did we use for the lecture recordings before the current one?
- after S4: Which speech-to-text model are we using for the lecture recordings?
- after S4: Which caption file format are we exporting?
- after S4 (as of S2): What was the state of the caption-format choice at the end of the second meeting?
