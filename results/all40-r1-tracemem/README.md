# TraceMem's per-question files: run 1 on the 40 test scenarios

*For E, to pick 2 or 3 real failure cases for the deck (your task E5, the failure examples). Made on 28 Oct, offline, from run 1's saved replies: no model was called and no run was repeated.*

## What this is

You asked for TraceMem's answers, resolver logs (the logs of TraceMem's resolver, the model call that decides how to store each statement), memory snapshots and answering-model inputs from the deck's earlier test run. That run has been replaced: the deck's 20 test scenarios and the report's 20 are now one set of 40 test scenarios, all run at the final frozen settings (the git tag `freeze-v1`). These folders hold the same kinds of files for TraceMem on **run 1 of 3** on all 40.

- **Start with the table below**: every question TraceMem answered wrong in run 1. Pick your 2 or 3 cases there.
- **For each case**, open its scenario folder (the link in the table). `memory-after-each-meeting.md` shows what TraceMem remembered after each meeting and which lines the answering model was shown; `memory-write-calls.jsonl` shows how each statement was stored, with the model's reason. The meetings' dialogue is in the scenario file, `benchmark/scenarios/test/<scenario>-….yaml` (for example [`deck-b01-suggestion-after-decision.yaml`](../../benchmark/scenarios/test/deck-b01-suggestion-after-decision.yaml)).
- **Please don't rerun anything**: these are the final runs' own results, and a rerun would give different replies.

## What was run

| | |
|---|---|
| System | TraceMem (`tracemem-controlled`): a memory that keeps every version of each decision, each with a status |
| Model | Claude Haiku 5.5, both for storing statements and for answering |
| Scenarios | the 40 test scenarios: the deck's 20 (`deck-…`) and the report's 20 (`report-…`); 350 questions in all |
| Settings | the final frozen settings (`freeze-v1`). Every system in the comparison is handed the same statements from each meeting (which item, which value). Only TraceMem and Mem0 (an open-source memory library, compared in two set-ups) decide, each with a model call, how to store a statement; the other two systems keep every statement as it comes (all four other systems are described under "A contrast with another system" below). A question about now is shown the 4 memory lines closest to it; a question about the past is shown every line. |
| Run | run 1 of 3; each run starts with an empty store of saved replies |
| When | the deck's 20 on 28 Oct, 13:03 to 13:21; the report's 20 on 28 Oct, 02:15 to 02:34 (Singapore time), with the same code and settings |

In run 1 TraceMem answered 314 of 350 questions right (the deck's 20: 138 of 156; the report's 20: 176 of 194).

## Every question TraceMem answered wrong in run 1 (36 of 350)

"After meeting" is the meeting after which the question was asked (S2 = meeting 2). The last column says how the scorer classed the answer, in plain words, with its class name (`docs/metrics.md`, section 3).

| # | Scenario | Kind of scenario | After meeting | Question | Right answer | TraceMem's answer | What went wrong |
|---|---|---|---|---|---|---|---|
| 1 | [deck-b01](deck-b01/) (Planning a team dinner) | a suggestion after a decision | S3 | Which venue is currently confirmed for the team dinner? (`dinner.venue@S3`) | Orchard Café | Harbour Café | gave a suggestion or a disputed value as if it were decided (`unconfirmed_as_current`) |
| 2 | [deck-b02](deck-b02/) (A cheaper family holiday is suggested) | a suggestion after a decision | S2 | Which destination is currently agreed for the family holiday? (`trip.destination@S2`) | Kyoto | nothing settled | said nothing is settled, but something was settled or disputed (`missed`) |
| 3 | [deck-b02](deck-b02/) (A cheaper family holiday is suggested) | a suggestion after a decision | S3 | Which destination, if any, did we agree on for the family holiday before the current one? (`trip.destination@S3-previous`) | Kyoto | no answer (gave up) | declined to answer (`abstained`) |
| 4 | [deck-b05](deck-b05/) (An old registration date is recalled) | later recollections, reports and questions about the past | S1 | What is the current registration deadline? (`registration.deadline@S1`) | 10 November | nothing settled † | said nothing is settled, but something was settled or disputed (`missed`) |
| 5 | [deck-b05](deck-b05/) (An old registration date is recalled) | later recollections, reports and questions about the past | S2 | What is the current registration deadline? (`registration.deadline@S2`) | 10 November | nothing settled † | said nothing is settled, but something was settled or disputed (`missed`) |
| 6 | [deck-b05](deck-b05/) (An old registration date is recalled) | later recollections, reports and questions about the past | S4 | What is the registration fee? (`registration.fee@S4`) | nothing settled | no answer (gave up) | declined to answer (`abstained`) |
| 7 | [deck-b08](deck-b08/) (A bus time changes but cabin access does not) | a similar item of the same kind, decided later | S1 | What is the bus departure time? (`bus.departure@S1`) | 7 am | nothing settled | said nothing is settled, but something was settled or disputed (`missed`) |
| 8 | [deck-b08](deck-b08/) (A bus time changes but cabin access does not) | a similar item of the same kind, decided later | S4 | Which bus departure time, if any, did we have before the current one? (`bus.departure@S4-previous`) | 7 am | no earlier value (it never changed) † | said there was no earlier value, but there was one (`missed`) |
| 9 | [deck-b09](deck-b09/) (Two office rooms have different delivery dates) | a similar item of the same kind, decided later | S4 | What is the meeting-room furniture delivery date? (`delivery.meeting_room@S4`) | 25 November | no answer (gave up) | declined to answer (`abstained`) |
| 10 | [deck-b09](deck-b09/) (Two office rooms have different delivery dates) | a similar item of the same kind, decided later | S5 | What is the meeting-room furniture delivery date? (`delivery.meeting_room@S5`) | 17 November | no answer (gave up) | declined to answer (`abstained`) |
| 11 | [deck-c01](deck-c01/) (An Evening at the Giant Wild Goose Pagoda) | a suggestion after a decision | S3 | How are we travelling to the Giant Wild Goose Pagoda? (`trip.transport@S3`) | metro | nothing settled | said nothing is settled, but something was settled or disputed (`missed`) |
| 12 | [deck-c02](deck-c02/) (The Neighbourhood News Update) | a second speaker disputing a decision | S1 | What format have we chosen for the update? (`update.format@S1`) | nothing settled | no answer (gave up) | declined to answer (`abstained`) |
| 13 | [deck-c02](deck-c02/) (The Neighbourhood News Update) | a second speaker disputing a decision | S2 | What topic has the team settled on for the update? (`update.topic@S2`) | disputed | hot weather | the team disagreed, but it picked one side (`false_certainty`) |
| 14 | [deck-c02](deck-c02/) (The Neighbourhood News Update) | a second speaker disputing a decision | S3 | What topic has the team settled on for the update? (`update.topic@S3`) | disputed | hot weather | the team disagreed, but it picked one side (`false_certainty`) |
| 15 | [deck-c07](deck-c07/) (Friday Football) | a change stated without replacement words | S3 | Where is the football game planned to take place? (`game.venue@S3`) | indoor court at the sports hall | no answer (gave up) | declined to answer (`abstained`) |
| 16 | [deck-c09](deck-c09/) (Testing an AI Revision Helper) | a suggestion after a decision | S1 | What is the main evaluation criterion? (`eval.main_criterion@S1`) | nothing settled | no answer (gave up) | declined to answer (`abstained`) |
| 17 | [deck-c10](deck-c10/) (Saturday Movie Night) | later recollections, reports and questions about the past | S2 | Which film are we watching on Saturday? (`outing.film@S2`) | Inside Out 2 | no answer (gave up) | declined to answer (`abstained`) |
| 18 | [deck-c10](deck-c10/) (Saturday Movie Night) | later recollections, reports and questions about the past | S3 | Which film are we watching on Saturday? (`outing.film@S3`) | Inside Out 2 | no answer (gave up) | declined to answer (`abstained`) |
| 19 | [report-b11](report-b11/) (Pet-sitting preparation progresses unevenly) | tasks that open, get blocked, finish or are cancelled | S1 | What is the status of the key handover? (`task.key_handover@S1`) | open | nothing settled | said nothing is settled, but something was settled or disputed (`missed`) |
| 20 | [report-b11](report-b11/) (Pet-sitting preparation progresses unevenly) | tasks that open, get blocked, finish or are cancelled | S2 | What is the status of the key handover? (`task.key_handover@S2`) | open | nothing settled | said nothing is settled, but something was settled or disputed (`missed`) |
| 21 | [report-b11](report-b11/) (Pet-sitting preparation progresses unevenly) | tasks that open, get blocked, finish or are cancelled | S3 | What is the status of the key handover? (`task.key_handover@S3`) | open | nothing settled | said nothing is settled, but something was settled or disputed (`missed`) |
| 22 | [report-b12](report-b12/) (A club agreement survives repeated paraphrases) | a suggestion after a decision | S1 | What is the refreshment budget for the gathering? (`refreshments.budget@S1`) | SGD 80 | nothing settled | said nothing is settled, but something was settled or disputed (`missed`) |
| 23 | [report-b12](report-b12/) (A club agreement survives repeated paraphrases) | a suggestion after a decision | S2 | What is the refreshment budget for the gathering? (`refreshments.budget@S2`) | SGD 80 | nothing settled | said nothing is settled, but something was settled or disputed (`missed`) |
| 24 | [report-b12](report-b12/) (A club agreement survives repeated paraphrases) | a suggestion after a decision | S3 | What date has been chosen for the gathering? (`gathering.date@S3`) | nothing settled | no answer (gave up) | declined to answer (`abstained`) |
| 25 | [report-b12](report-b12/) (A club agreement survives repeated paraphrases) | a suggestion after a decision | S3 | What is the refreshment budget for the gathering? (`refreshments.budget@S3`) | SGD 80 | nothing settled | said nothing is settled, but something was settled or disputed (`missed`) |
| 26 | [report-b14](report-b14/) (An exhibition print size is deliberately revised) | a change stated without replacement words | S2 | What print size are we using for the exhibition? (`prints.size@S2`) | A2 | no answer (gave up) | declined to answer (`abstained`) |
| 27 | [report-b14](report-b14/) (An exhibition print size is deliberately revised) | a change stated without replacement words | S3 | What print size are we using for the exhibition? (`prints.size@S3`) | A2 | no answer (gave up) | declined to answer (`abstained`) |
| 28 | [report-b15](report-b15/) (A pop-up packaging choice changes twice) | a change stated as "X instead of Y" | S3 | What packaging are we using for the pop-up orders? (`packaging.type@S3`) | plastic bags | paper bags | gave an old value that had been replaced (`stale`) |
| 29 | [report-b19](report-b19/) (The missing readings are changing the story) | a change stated as "X instead of Y" | S3 | How are we handling missing temperature data in the main analysis? (`missing.handling@S3`) | drop incomplete hourly records | no answer (gave up) | declined to answer (`abstained`) |
| 30 | [report-c12](report-c12/) (A Birthday Surprise for Grandma) | a second speaker disputing a decision | S1 | What birthday-card format have we chosen? (`card.format@S1`) | nothing settled | no answer (gave up) | declined to answer (`abstained`) |
| 31 | [report-c12](report-c12/) (A Birthday Surprise for Grandma) | a second speaker disputing a decision | S2 | What cake flavour has the family settled on? (`cake.flavour@S2`) | disputed | lemon | the team disagreed, but it picked one side (`false_certainty`) |
| 32 | [report-c12](report-c12/) (A Birthday Surprise for Grandma) | a second speaker disputing a decision | S3 | What cake flavour has the family settled on? (`cake.flavour@S3`) | disputed | lemon | the team disagreed, but it picked one side (`false_certainty`) |
| 33 | [report-c12](report-c12/) (A Birthday Surprise for Grandma) | a second speaker disputing a decision | S4 | What cake flavour has the family settled on? (`cake.flavour@S4`) | disputed | lemon | the team disagreed, but it picked one side (`false_certainty`) |
| 34 | [report-c12](report-c12/) (A Birthday Surprise for Grandma) | a second speaker disputing a decision | S5 | What cake flavour has the family settled on? (`cake.flavour@S5`) | disputed | lemon | the team disagreed, but it picked one side (`false_certainty`) |
| 35 | [report-c14](report-c14/) (Music for the Charity Fair) | later recollections, reports and questions about the past | S1 | What closing song have we chosen? (`song.closing@S1`) | nothing settled | no answer (gave up) | declined to answer (`abstained`) |
| 36 | [report-c17](report-c17/) (The Community Garden Watering Rota) | a change stated without replacement words | S4 | Who is responsible for Monday watering? (`watering.monday@S4`) | Tessa | no answer (gave up) | declined to answer (`abstained`) |

† For these 3 questions the reply saved for TraceMem's request is the other TraceMem system's (see "How the files were rebuilt" below). The answer shown, and `answer` in `answerer-inputs.jsonl`, are TraceMem's own, from the run's log; the saved reply is kept beside it and marked.

By kind of mistake:

| What went wrong | Questions |
|---|---|
| declined to answer (`abstained`) | 16 |
| said nothing is settled, but something was settled or disputed (`missed`) | 11 |
| the team disagreed, but it picked one side (`false_certainty`) | 6 |
| gave a suggestion or a disputed value as if it were decided (`unconfirmed_as_current`) | 1 |
| said there was no earlier value, but there was one (`missed`) | 1 |
| gave an old value that had been replaced (`stale`) | 1 |

## Files in each scenario folder

| File | What it holds |
|---|---|
| `memory-after-each-meeting.md` | Start here. For each meeting: TraceMem's whole memory after it, then, for each question asked after it, the lines the answering model was shown. |
| `memory-after-each-meeting.json` | The same memory as records (item, value, status, source turns), with the lines shown for each question. |
| `answerer-inputs.jsonl` | One line per question: the question, the right answer (`expected`), the scorer's class (`outcome`), the whole memory, the lines shown, TraceMem's answer as the run logged it, `answer` (token counts in `answer.usage`), and every message sent to the answering model with its reply (`attempts`). An answer gets another attempt, up to 2 in all, when the model call itself fails (a passing provider error or a time-out; the same messages are sent again), or when the reply is incomplete or malformed, its status does not fit its value, it repeats a citation or cites a turn not among the lines shown, it gives a settled answer although the lines shown hold an open dispute about that item, or it gives a settled answer about now without citing both its decision and the earlier record it grew from (`src/tracemem/systems/comparison.py`); if the last attempt fails too, TraceMem gives no answer. In run 1, 4 of 350 questions had a second attempt, all 4 for a settled answer about now that did not cite both its decision and the earlier record it grew from, and all 4 were then answered right. |
| `memory-write-calls.jsonl` | One line per statement TraceMem stored, in order: the meeting, the statement (speaker, words, item, value), the exact messages sent to TraceMem's resolver (the model call that decides how to store a statement), its reply, and `operation_tracemem_applied`, the change TraceMem made, with the model's reason (`rationale`). `call` is the call's place among all the scenario's model calls, counting from 0, answer calls included (so a gap in the numbers is a call to the answering model). |
| `run-answers.jsonl` | The run's own log of answers: question, right answer, TraceMem's answer with its explanation (`text`), and the scorer's class. |
| `run-candidates.jsonl` | The run's own log of the statements TraceMem was handed, one per line. |
| `run-ops.jsonl` | The run's own log of memory changes, one per statement: the operation (ADD makes a new record, either settled or only suggested; KEEP confirms the current decision; SUPERSEDE replaces it; FLAG records a dispute), the records it targets, and the model's reason. |
| `run-resolver_events.jsonl` | One line per statement: whether the change was applied and how many model calls it took (1 for every statement in run 1; no resolver call failed: 0 errors logged). |
| `run-resolver_analysis.jsonl` | One line per statement where something went wrong, with the expected change and what was wrong (`errors`): either the change differs from the expected one (`wrong_label`: another operation, or ADD with another status; `wrong_sources`: other source turns; `wrong_targets`: other records targeted), or the item's state in memory after it differs from the expected state (`wrong_state`), or both (30 of the 50 lines). In 10 of the 50 lines across the 40 folders the change itself was right (`exact_operation_correct: true`) and only `wrong_state` is listed: the item was already in the wrong state from an earlier change. The file is empty when every change, and the state after it, matched. |

The five `run-…` files are this scenario's rows of the run's own logs, copied byte for byte.

The two long fixed prompts are stored once, in [`prompts/`](prompts/): the answer prompt every system uses and TraceMem's resolver prompt. A message stored there appears in the JSON files as `{"role": …, "content_file": …, "sha256": …}`; the file's SHA-256 (a fingerprint of its text: any change to the text changes it) equals the given hash.

**Reading a memory line.** `S1-T6 Grace: dinner.venue = Orchard Café [active] | sources=S1-T6,S1-T2` (from deck-b01, "Planning a team dinner") means: the record was made at meeting 1, turn 6, by Grace; it says the dinner venue is Orchard Café; TraceMem holds it as the current decision; and it rests on turns S1-T6 (Grace: "Agreed. We should go for this promotion! Are the rest ok?") and S1-T2 (Maya: "How do you all think about Orchard Café."). The word in brackets is the record's status: `active` (the current decision), `proposed` (a suggestion nobody has decided on), `contested` (an open dispute against the current decision), `superseded` (replaced by a later decision) or `declined` (a dispute that lost).

## How the files were rebuilt, and why they are TraceMem's own

The run saved its answers and logs, but not the memory after each meeting or the exact text sent to the model. The memory and the messages were rebuilt offline on 28 Oct from run 1's saved replies: TraceMem's code, with the run's scenario files and settings, was stepped through each scenario, and each request to the model was answered with the reply the run had saved for it instead of calling the model. No model was called and nothing was spent: 0 of 675 requests lacked a saved reply, and 0 embeddings (the numbers used to find the closest memory lines) were missing.

One thing needed care. During the runs, TraceMem ran at the same time as a check version of itself that keeps no history (`tracemem-no-versions`), and the two shared one store of saved replies. The two send exactly the same request to the model whenever the memory a request carries is the same (for storing a statement, the records already held for that statement's item; for an answer, the lines shown), even after their memories differ elsewhere. When both sent such a request before either reply was saved, both were paid for, and the reply saved second replaced the first. So for some requests the saved reply is the other system's. The rebuild therefore:

- gives TraceMem, at each statement, the memory change the run logged for it (`run-ops.jsonl`), so its memory at every question is exactly the run's;
- checks every saved reply against TraceMem's own log. For storing statements, 242 of 321 saved replies are TraceMem's own and 79 are the other system's (73 give the same change in other words, 6 a different change). For answers, 330 of 350 are TraceMem's own and 20 are the other system's (the same status and value in other words; in 1 of them the saved reply also cites turns where TraceMem's own answer cited none). For every one of these 99, the cost log shows the request was paid for twice during the run, and the saved reply gives exactly what the other system logged;
- marks those replies in the files (`saved_reply_is_tracemems_own: false`) and gives TraceMem's own result, from the run's log, beside them.

Before any file was written, the rebuild was checked against the run's own logs; any other difference would have stopped it:

| Run's log | The deck's 20 | The report's 20 |
|---|---|---|
| `answers.jsonl` (here `run-answers.jsonl`) | 145 of 156 equal; status, value and outcome equal in 156 of 156 | 185 of 194 equal; status, value and outcome equal in 194 of 194 |
| `candidates.jsonl` (here `run-candidates.jsonl`) | 155 of 155 | 166 of 166 |
| `ops.jsonl` (here `run-ops.jsonl`) | 155 of 155 | 166 of 166 |
| `resolver_events.jsonl` (here `run-resolver_events.jsonl`) | 155 of 155 | 166 of 166 |
| `resolver_scores.jsonl` (the score of every memory change against the expected one; not copied here, as `run-resolver_analysis.jsonl` holds its lines where something went wrong) | 155 of 155 | 166 of 166 |
| `resolver_analysis.jsonl` (here `run-resolver_analysis.jsonl`) | 18 of 18 | 32 of 32 |
| `metrics.json` (the run's summary scores; not copied here) | equal except `citation_validity`: it counts 146 answers that cite at least one turn in the run and 147 in the rebuild, 100% of them valid in both | equal |

Token counts are left out of the comparison, because a saved reply carries none. In `answers.jsonl` every answer not counted equal differs only in its wording or cited turns, as explained above.

In `metrics.json` for the deck's 20, the one difference is in `citation_validity`, which checks that cited turns are real turns the system had already seen (`docs/metrics.md`, Evidence). It counts the answers that cite at least one turn: 146 in the run and 147 in the rebuild, with 100% of them valid in both. The extra answer is deck-b03 ("A wedding venue remains only an alternative"), question `reception.venue@S3` ("Which reception venue is currently selected?"): TraceMem's own answer cited no turn, while the saved reply, the other system's, cites S1-T1 (Isha: "I propose Willow Hall for the reception."), S1-T4 (Zoe: "Oh icic, have you considered Willow Hall?"), S2-T1 (Zoe: "What about Lake Pavilion instead of Willow Hall?") and S3-T2 (Zoe: "Could that make Lake Pavilion worth another look?").

The rows for `ops.jsonl`, `resolver_events.jsonl`, `resolver_scores.jsonl` and `resolver_analysis.jsonl` agree by construction: the rebuild applies the run's logged change at each statement, so they could differ only through a fault in the rebuild itself. The `candidates.jsonl` row checks that the statements handed to TraceMem are the scenario files' own. The independent evidence is the `answers.jsonl` row, where each answer is the saved reply to a request rebuilt from that memory, and the check of each saved write reply above.

So every answer, scorer's class and memory change in these folders is TraceMem's own from run 1.

## A contrast with another system

Similar files could be made for the other four systems in the comparison, if you want to show how another memory handled the same case: similarity (keeps every statement as a memory line with no status, and shows the answering model the lines closest in meaning to the question), similarity + recency (the same, but favouring newer lines), Mem0 (an open-source memory library, version 1.0.11, whose own model call adds, updates or deletes memories as each statement arrives) and Mem0 + instructions (Mem0 with the project's rules on decisions, suggestions and disputes added to its prompt).

The method used here cannot be applied to the other four systems as it stands: it must be adapted for each one first. It was built for TraceMem: it gives TraceMem, at each statement, the memory change its run logged, in TraceMem's own form, which the other systems do not use; and it checks saved replies only against the other TraceMem system. Some of the other systems' saved replies are also another system's, sometimes with a different answer and score: an earlier check on the report's 20 found this for similarity and similarity + recency. That check also drove all four other systems through the report's 20 from run 1's saved replies, offline, and no request lacked a saved reply. For the deck's 20, whether every request has a saved reply has not been checked. Ask, naming the scenarios.
