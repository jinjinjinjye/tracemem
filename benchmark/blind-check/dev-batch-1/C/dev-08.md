# dev-08

## S1 (2026-10-06)
S1-T1 Mel: Right, let's just get this over with. The idea is to map what the campus paper has been writing about over the last five years.  
S1-T2 Joel: I'll handle downloading the archive from the paper's website this week. It's around four thousand articles, but I'll get it sorted straight away for you.  
S1-T3 Hiro: For the model... maybe we could use LDA to start? It's the one we all know from class...  
S1-T4 Mel: Yeah, let's just go with LDA for now. It's quick to set up.  
S1-T5 Joel: Spot on. How do we tell if the topics are actually any good, though? I was thinking maybe C_v coherence, like in the lecture notes?  
S1-T6 Mel: Could be. Let me read up on it myself before we commit to anything.  

## S2 (2026-10-09)
S2-T1 Joel: Bit of bad news, I'm afraid. The paper's site started rate-limiting me, so the archive download is stuck at about a third.  
S2-T2 Mel: Ugh. Great. One of the editors is in my tutorial, I'll just ask her about it.  
S2-T3 Hiro: Meanwhile, I ran LDA on the third we have. Half the topics are mush... like sports and campus events in one bucket. I was looking at it for a while.  
S2-T4 Hiro: Maybe BERTopic would do better? It works off embeddings... so short news pieces might cluster more cleanly.  
S2-T5 Joel: Maybe, mate, but I'd want the full archive in before we change anything prematurely.  
S2-T6 Mel: Fair. Oh, and I read up on the idea from Tuesday. Let's go with C_v coherence to score the topics and just move on.  

## S3 (2026-10-13)
S3-T1 Mel: I spoke to the editors. They are fine with us scraping, as long as it's slow and overnight. So that's settled.  
S3-T2 Joel: Brilliant work. I've already restarted the archive download based on that.  
S3-T3 Joel: I'll make absolutely sure it's done by Friday.  
S3-T4 Hiro: I stayed up over the weekend trying BERTopic on a sample of five hundred articles... Sports and campus events finally came out as separate topics. The clusters look nice.  
S3-T5 Joel: Right, or we could maybe try NMF? It's actually a lot lighter than anything with embeddings, which is just more efficient.  
S3-T6 Mel: Let's not add a third option yet. We'll compare properly once the full archive is in. Let's just stick to the plan.  

## S4 (2026-10-16)
S4-T1 Joel: Just to update, the archive download finished last night. All 4,100 articles are in the shared folder, all sorted.  
S4-T2 Hiro: And I ran BERTopic on the whole archive. About forty minutes on my laptop... and the topics still look very clean.  
S4-T3 Mel: Then that settles it. We're switching to BERTopic, like Hiro proposed last week. Let's wrap this up.  
S4-T4 Joel: Absolutely fine by me. The scoring stays C_v coherence, then.  
S4-T5 Mel: Good. Same time on Tuesday. Just bring your topic lists and keep the chat to a minimum.  

## Questions (answer each from the dialogue alone: a value, `none` or `disputed`; see the guide)
- after S1: Which measure are we using to score the topics?
- after S1: Which topic model are we using for the articles?
- after S1: What is the status of the archive download?
- after S2: Which measure are we using to score the topics?
- after S2: Which topic model are we using for the articles?
- after S2: What is the status of the archive download?
- after S3: Which measure are we using to score the topics?
- after S3: Which topic model are we using for the articles?
- after S3: What is the status of the archive download?
- after S4: Which measure are we using to score the topics?
- after S4 (as of S1): What was the state of the topic-scoring choice at the end of the first meeting?
- after S4: Which topic model are we using for the articles?
- after S4: Which topic model, if any, did we use for the articles before the current one?
- after S4: What is the status of the archive download?
