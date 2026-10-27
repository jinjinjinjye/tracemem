# dev-03

## S1 (2026-10-06)
S1-T1 Clara: Okay, plan is user and movie embeddings into a small MLP to predict rating.  
S1-T2 Jonathan: Embedding tables only get sparse updates, so they need their own LR. Let's fix 0.05 for the embeddings.  
S1-T3 Mel: What about the MLP layers on top?  
S1-T4 Jonathan: Hold off on those until the embeddings train properly without blowing up.  
S1-T5 Mel: Noted. I'll write the eval script for the top-10 lists.  
S1-T6 Clara: I'll clean up the ratings file tonight.  

## S2 (2026-10-09)
S2-T1 Clara: Embeddings training fine, loss going down smoothly.  
S2-T2 Mel: Good. So what's the LR for the MLP layers?  
S2-T3 Jonathan: Dense layers usually require a much smaller rate. Let's set the MLP LR at 0.001.  
S2-T4 Clara: Can. I'll update the config.  
S2-T5 Mel: Eval script is stuck though. Not sure how to handle movies that only appear in the test set.  
S2-T6 Jonathan: Good point. We'll check with the TA after Monday's tutorial.  

## S3 (2026-10-14)
S3-T1 Mel: Validation loss climbing after epoch three. MLP is definitely overfitting.  
S3-T2 Jonathan: Then we drop the MLP LR to 0.0003 and add dropout.  
S3-T3 Clara: Okay. Embedding rate stays the same, right?  
S3-T4 Jonathan: Yeah, no change.  
S3-T5 Mel: Also, TA said to just drop movies not in training, so eval script is done.  
S3-T6 Clara: Great. I'll start a long training run tonight.  

## S4 (2026-10-20)
S4-T1 Mel: Since the MLP has dropout now, maybe bump its LR back to 0.001? Might converge faster.  
S4-T2 Clara: Maybe, but bigger issue now. The long run is very noisy, jumps are coming from the embedding tables.  
S4-T3 Jonathan: Then we cut the embedding LR to 0.01. That will stabilize it.  
S4-T4 Mel: Agreed. Frankly, 0.05 was always a bit high for embeddings.  
S4-T5 Clara: I'll rerun tonight and send the curves.  
S4-T6 Jonathan: Noted. See you guys Friday.  

## Questions (answer each from the dialogue alone: a value, `none` or `disputed`; see the guide)
- after S1: What learning rate are we using for the embedding tables?
- after S1: What is the status of the evaluation script?
- after S2: What learning rate are we using for the embedding tables?
- after S2: What learning rate are we using for the MLP layers?
- after S2: What is the status of the evaluation script?
- after S3: What learning rate are we using for the embedding tables?
- after S3: What learning rate are we using for the MLP layers?
- after S3: What is the status of the evaluation script?
- after S4: What learning rate are we using for the embedding tables?
- after S4 (as of S3): What was the state of the embedding learning-rate choice at the end of the third meeting?
- after S4: Which learning rate, if any, did we use for the embedding tables before the current one?
- after S4: What learning rate are we using for the MLP layers?
- after S4 (as of S1): What was the state of the MLP learning-rate choice at the end of the first meeting?
- after S4: Which learning rate, if any, did we use for the MLP layers before the current one?
- after S4: What is the status of the evaluation script?
