# dev-01

## S1 (2026-10-06)
S1-T1 Lena: Okay, so the brief is one number per day: total rentals across the whole network for tomorrow.  
S1-T2 Tomas: Right. We just go with LightGBM on lag features for the forecast lah. Quick to train and we all know it.  
S1-T3 Lena: Can. And we'll score it on MAE, since it's in bikes per day and anyone can read that.  
S1-T4 Lena: Farah, can you help pull the daily weather and join it to the rental counts?  
S1-T5 Farah: Can, I'll grab it from the city weather archive tonight.  
S1-T6 Tomas: Swee, see you all Friday.  

## S2 (2026-10-09)
S2-T1 Tomas: The first LightGBM run finished already. Not bad on normal days, but completely miss the holiday dips.  
S2-T2 Farah: Hmm, maybe we try Prophet? Apparently it handles holidays out of the box leh.  
S2-T3 Lena: Can consider. I'd want to see some numbers first before we change anything though.  
S2-T4 Farah: Also hor, I'm stuck on the weather join. The archive keep timing out every time I pull for the full year.  
S2-T5 Tomas: One more thing. MAE treats every day the same, but the rebalancing crews mostly care about the big peak days. Should we score on RMSE instead?  
S2-T6 Lena: Maybe. Let me think about it over the weekend first.  

## S3 (2026-10-13)
S3-T1 Farah: Good news, the weather join is done. I split the requests by month then it went through.  
S3-T2 Tomas: Nice, I've rerun everything with temperature and rain added inside.  
S3-T3 Tomas: The errors on the summer peaks are still massive, and our current metric completely hides it.  
S3-T4 Lena: Okay lah, you've convinced me. From now on RMSE is our main metric.  
S3-T5 Farah: I'll go redo the comparison table with the new metric then.  
S3-T6 Lena: Great. We meet Friday and plan the write-up.  

## S4 (2026-10-16)
S4-T1 Lena: For the write-up: the model is LightGBM and we report RMSE.  
S4-T2 Tomas: I'll draft out the methods section this weekend.  
S4-T3 Farah: Looking back hor, Prophet probably would've handled the holidays better, but we never got around to trying it.  
S4-T4 Lena: Maybe lor. Either way, it's too late to change anything now.  
S4-T5 Tomas: Agreed. I'll send the draft around by Monday.  

## Questions (answer each from the dialogue alone: a value, `none` or `disputed`; see the guide)
- after S1: What is our main evaluation metric for the forecast?
- after S1: Which model are we using for the daily demand forecast?
- after S1: What is the status of the weather join?
- after S2: What is our main evaluation metric for the forecast?
- after S2: Which model are we using for the daily demand forecast?
- after S2: What is the status of the weather join?
- after S3: What is our main evaluation metric for the forecast?
- after S3: Which model are we using for the daily demand forecast?
- after S3: What is the status of the weather join?
- after S4: What is our main evaluation metric for the forecast?
- after S4 (as of S2): What was the state of the main-metric choice at the end of the second meeting?
- after S4: Which model are we using for the daily demand forecast?
- after S4 (as of S3): What was the state of the demand-model choice at the end of the third meeting?
- after S4: Which model, if any, did we use for the daily demand forecast before the current one?
- after S4: What is the status of the weather join?
