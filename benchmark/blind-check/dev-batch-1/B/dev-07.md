# dev-07

## S1 (2026-10-06)
S1-T1 Ines: Right, so for the readmission model, let's start with logistic regression. Clinicians can actually read the coefficients, which is rather important.  
S1-T2 Omar: Uh, yes, that sounds fine by me. For the evaluation, we'll just do a standard random 80/20 split of the discharges, nothing too complicated.  
S1-T3 Greta: And AUROC is our headline metric. That's what all the standard readmission papers report.  
S1-T4 Ines: Brilliant. Greta, are you alright with cleaning up the discharge table this week?  
S1-T5 Greta: Yep, definitely. Should have it done by Friday.  
S1-T6 Omar: I'll go ahead and get the training script going in the meantime, then.  

## S2 (2026-10-09)
S2-T1 Greta: The table's clean. Just a heads up though, a lot of patients come back more than once. Some even have six or seven separate stays.  
S2-T2 Omar: Oh, right... that's actually a bit of a problem for our test numbers. The same person could end up on both sides.  
S2-T3 Ines: Exactly. So from now on, we split by patient. All of one person's stays have to go to the same side.  
S2-T4 Omar: Yes, that makes total sense. I'll redo the folds tonight and rerun everything for you.  
S2-T5 Greta: Sounds like a plan. I'll start drafting the cohort section in the meantime.  

## S3 (2026-10-13)
S3-T1 Omar: I've reran it with the new folds. The model is kind of stuck at about 0.68, and even when I pile on more features, it barely moves.  
S3-T2 Greta: Makes sense, to be honest. A linear model can't really pick up things like age interacting with the number of prior stays.  
S3-T3 Ines: Right, in that case, we're going with XGBoost for the model. Trees should naturally catch those interactions without us having to hand-build them.  
S3-T4 Omar: Okay, sure. I'll port the pipeline over tonight.  
S3-T5 Greta: One more thing to note. Only about 11% of discharges actually get readmitted within 30 days.  
S3-T6 Ines: Hm. Which means our headline number could look perfectly decent even when the model is barely finding anyone. That won't do.  
S3-T7 Greta: Exactly. So AUPRC is our main metric from now on. It actually tracks how well we catch the rare positives.  
S3-T8 Ines: Completely agreed.  
S3-T9 Omar: I'll make sure to put it first in the results table, then.  

## S4 (2026-10-16)
S4-T1 Greta: I touched base with the discharge team at the partner hospital. They'd be running this on next year's patients, so they really care how it performs on future discharges.  
S4-T2 Ines: That's a very fair point. Then we split by discharge date instead: train on everything up to June, test on July to September.  
S4-T3 Omar: Um, Ines... doesn't that put some patients on both sides again?  
S4-T4 Ines: A few, quite possibly. But that's exactly what it will look like once it's actually deployed on the wards, right?  
S4-T5 Omar: Ah, I see. Okay, I'll rebuild the train and test sets this afternoon.  
S4-T6 Ines: Perfect. So for the presentation slides: we're on XGBoost, and we lead with AUPRC.  
S4-T7 Greta: Got it. I'll handle the plots once Omar's numbers come in.  

## Questions (answer each from the dialogue alone: a value, `none` or `disputed`; see the guide)
- after S1: What is our primary evaluation metric?
- after S1: Which model are we using to predict readmissions?
- after S1: How are we splitting the data for evaluation?
- after S2: What is our primary evaluation metric?
- after S2: Which model are we using to predict readmissions?
- after S2: How are we splitting the data for evaluation?
- after S3: What is our primary evaluation metric?
- after S3: Which primary evaluation metric, if any, did we use before the current one?
- after S3: Which model are we using to predict readmissions?
- after S3: How are we splitting the data for evaluation?
- after S4: What is our primary evaluation metric?
- after S4: Which model are we using to predict readmissions?
- after S4 (as of S2): What was the state of the readmission-model choice at the end of the second meeting?
- after S4: How are we splitting the data for evaluation?
- after S4: Which data split, if any, did we use for evaluation before the current one?
