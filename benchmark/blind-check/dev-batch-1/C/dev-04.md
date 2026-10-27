# dev-04

## S1 (2026-10-06)
S1-T1 Genevieve: Right, for the fraud classifier let's just go with XGBoost. It's the standard pick for this kind of tabular data, so there's no reason to overcomplicate things right now.  
S1-T2 Tom: Sounds good! Just a thought though, fraud is only about 0.2% of the rows. Maybe we could try oversampling the frauds with SMOTE? Just to balance it out a bit.  
S1-T3 Ivy: Need to do something. Otherwise the model just predicts everything as legit.  
S1-T4 Genevieve: I was getting to that. Yes, let's do SMOTE. But we must apply it to the training folds only, otherwise we leak data.  
S1-T5 Genevieve: Also, we will use PR-AUC as the main metric. ROC-AUC always looks great on skewed data no matter what the model actually does, so PR-AUC is more accurate for us.  
S1-T6 Ivy: Makes sense. I'll split data by month so test set is the newest few weeks.  

## S2 (2026-10-09)
S2-T1 Tom: First full run is out! We got 0.71 PR-AUC on the held-out month, quite exciting.  
S2-T2 Ivy: Not bad. Out of curiosity, how does a random forest usually perform on card fraud? Not saying we change.  
S2-T3 Genevieve: Why are we asking about random forest now? Honestly, I have no idea, I've only ever seen boosting used in the standard tutorials anyway.  
S2-T4 Tom: Ah, just sharing! The group who had this dataset last year used class weights instead. They only got 0.55, so we are doing better.  
S2-T5 Genevieve: Exactly, good to know we are ahead then. Our approach is working.  
S2-T6 Ivy: I'll start threshold analysis this week.  

## S3 (2026-10-13)
S3-T1 Ivy: Ran undersampling over the weekend. Kept one in ten legit transactions. PR-AUC went from 0.71 to 0.76, and training is five times faster than SMOTE. Let's switch to undersampling.  
S3-T2 Genevieve: I mean, if the numbers are better and it's faster, agreed, undersampling it is. But the model stays XGBoost, let's be clear on that. We just retrain it with the new data split.  
S3-T3 Tom: Oh man. I actually spent a whole evening tuning the SMOTE neighbours. But it's okay, faster is better.  
S3-T4 Tom: I will rerun the month-by-month evaluation with the new setup tonight, no problem!  
S3-T5 Ivy: Can help to log false positives per merchant category as well?  
S3-T6 Genevieve: Good. Let's touch base again on Friday.  

## S4 (2026-10-16)
S4-T1 Genevieve: Okay, draft summary for the report is as follows: we used XGBoost, trained with undersampling, and scored on PR-AUC. Everyone aligned?  
S4-T2 Tom: Just wondering looking back, should we have given LightGBM a try? Though I know it's too late to switch now anyway.  
S4-T3 Ivy: Results probably about the same. For appendix, ROC-AUC comes out at 0.98. But that number hides how many frauds we actually miss.  
S4-T4 Genevieve: Let's not get sidetracked, keep it to the appendix only. We don't want to confuse the main report. Tom, can you tag the final config?  
S4-T5 Tom: Will do, I'll get it sorted tonight!  

## Questions (answer each from the dialogue alone: a value, `none` or `disputed`; see the guide)
- after S1: What is our primary evaluation metric?
- after S1: Which model are we using for the fraud classifier?
- after S1: How are we handling the class imbalance in training?
- after S2: What is our primary evaluation metric?
- after S2: Which model are we using for the fraud classifier?
- after S2: How are we handling the class imbalance in training?
- after S3: What is our primary evaluation metric?
- after S3: Which model are we using for the fraud classifier?
- after S3: How are we handling the class imbalance in training?
- after S4: What is our primary evaluation metric?
- after S4: Which model are we using for the fraud classifier?
- after S4: Which model, if any, did we use for the fraud classifier before the current one?
- after S4: How are we handling the class imbalance in training?
- after S4 (as of S2): What was the state of the class-imbalance choice at the end of the second meeting?
- after S4: Which method for the class imbalance, if any, did we use before the current one?
