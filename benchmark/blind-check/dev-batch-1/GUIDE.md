# Blind check of the new development scenarios (tasks B3 and C3)

You get 4 short files. Each one is a series of team meetings (meeting 1 is S1, meeting 2 is S2, and so on, and each line has a number such as S2-T3, meaning meeting 2, line 3), followed by a list of questions. Please answer every question from the conversation alone. You need nothing else: no command to run and no other file to open.

Each file takes about 10 to 15 minutes.

## How to answer

**Every answer, to every question, is one of three things:**

| Answer | Give it when |
|---|---|
| a value | the team has settled on one, for example `Postgres` |
| `none` | nothing is settled: nobody has decided yet (a suggestion alone does not count) |
| `disputed` | someone claims the team settled on something different, and nobody has resolved it yet |

**For a task, the value is its status**, in one of four words, whatever words the team itself uses:

| Status | The team says the task is… |
|---|---|
| `open` | started, in progress, to do, or restarted |
| `blocked` | stuck, on hold, or waiting for something |
| `completed` | done or finished |
| `cancelled` | dropped or abandoned |

**Each question names the meeting it is asked after**, for example "after S2". Answer as things stood at the end of that meeting, using only what was said up to then. Two kinds of question look further back, and take the same three answers:

- "Which …, if any, did we use before the current one?" asks for the value that the current one replaced, or `none` if nothing was replaced.
- "What was the state of … at the end of the second meeting?" asks what held right after that meeting.

## Rules for the hard cases

1. **A suggestion is not a decision.** "Could we try SQLite instead?" changes nothing until someone agrees to it or decides it. Ask yourself: if everyone said "yes", would the plan change? If so, it is a suggestion.
2. **Saying no to a suggestion is not needed.** If nobody takes a suggestion up, it simply never becomes the answer.
3. **A disagreement stays open until someone settles it.** Once someone says "Hang on, wasn't it MySQL we chose?" about a database already settled as Postgres, the answer is `disputed`, until someone states a choice as final or the other side agrees. "Let's look at the old emails before deciding" does not settle it.
4. **Talking about a value is not choosing it.** "MySQL gave us trouble last year" looks back; it proposes nothing.
5. **An announced change counts.** "I'll pick the migration script up again today" makes the task `open` again.

## What to send back

Copy each question and write your answer after it, like this:

```
scenario-x
after S2: Which database are we using?  Postgres
after S3: What is the status of the migration script?  blocked
```

(These examples, like all the others in this guide, come from no scenario you will read.)

Then, under the heading **Unsure**, list every line or question where you hesitated, and say why in a few words. Those notes matter most: they show where a scenario is unclear.

Send the file to A by 8 pm today, Mon 26 Oct.
