# dev-02

## S1 (2026-10-06)
S1-T1 Bruno: Hi, for the leaf-disease classifier, let's fine-tune ResNet-50 as the backbone. It is what the course tutorial uses, no?  
S1-T2 SiHui: And for split, we just shuffle all photos. Do a random 80/20.  
S1-T3 Wendy: I'll go photograph the sick leaves in the campus garden this week and label them, so we get some real field photos also.  
S1-T4 Bruno: Perfetto, a couple of hundred will be plenty.  
S1-T5 SiHui: I make the data loader work tonight.  

## S2 (2026-10-09)
S2-T1 SiHui: Before I start training: Tuesday we already agreed on EfficientNet-B0, not ResNet-50. I wrote it down.  
S2-T2 Bruno: Mamma mia, that's not how I remember it. I thought it was ResNet-50. Let's not argue now, I will look for my notes, eh.  
S2-T3 Wendy: Honestly I cannot remember which one we chose. Can we sort it out next meeting?  
S2-T4 Wendy: Also, the garden photos are stuck. The campus garden is closed for pesticide spraying this whole week.  
S2-T5 SiHui: So troublesome. I just keep cleaning up the loader first.  

## S3 (2026-10-13)
S3-T1 SiHui: Weekend I run quick check on validation fold: EfficientNet-B0 got about 93% accuracy.  
S3-T2 Bruno: Ah, and ResNet-50 got 92% on the same fold, so it is basically a tie.  
S3-T3 Wendy: Since it's a tie, maybe we try MobileNetV3 instead? Small enough to run on a phone.  
S3-T4 Bruno: Maybeee, but I would rather we settle the first two before we throw in a third option.  
S3-T5 Wendy: Good news on the photos, by the way. The garden reopened yesterday, so I'm back out there taking them.  
S3-T6 Wendy: Oh, one more thing. We agreed to split the photos by plant, not randomly. I'm quite sure that's what we said.  
S3-T7 SiHui: No, I set up myself, it is a random 80/20 split. That is what we are using.  
S3-T8 Wendy: Okay can, random split then. I must have mixed it up.  
S3-T9 Bruno: OK. We will settle the backbone on Friday, then.  

## S4 (2026-10-16)
S4-T1 Bruno: I found the notes from our first meeting, and they do say ResNet-50. But EfficientNet-B0 did a bit better, so let's just switch to EfficientNet-B0 for good.  
S4-T2 SiHui: Good for me. EfficientNet-B0 it is.  
S4-T3 Wendy: The garden photos are done. 240 leaves, all labelled and uploaded.  
S4-T4 Bruno: Brava! Nice work. To be fair, ResNet-50 was never a bad pick, it was only a point behind.  
S4-T5 SiHui: True. I start the full training run tonight.  

## Questions (answer each from the dialogue alone: a value, `none` or `disputed`; see the guide)
- after S1: How are we splitting the leaf photos into training and test sets?
- after S1: Which backbone are we using for the leaf-disease classifier?
- after S1: What is the status of the campus-garden photos?
- after S2: How are we splitting the leaf photos into training and test sets?
- after S2: Which backbone are we using for the leaf-disease classifier?
- after S2: What is the status of the campus-garden photos?
- after S3: How are we splitting the leaf photos into training and test sets?
- after S3: Which backbone are we using for the leaf-disease classifier?
- after S3: What is the status of the campus-garden photos?
- after S4: How are we splitting the leaf photos into training and test sets?
- after S4: Which train/test split, if any, did we use for the leaf photos before the current one?
- after S4: Which backbone are we using for the leaf-disease classifier?
- after S4 (as of S3): What was the state of the backbone choice at the end of the third meeting?
- after S4: Which backbone, if any, did we use for the leaf-disease classifier before the current one?
- after S4: What is the status of the campus-garden photos?
