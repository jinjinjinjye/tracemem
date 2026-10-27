"""Print each run's present and past accuracy, strict and with the second score of decision record 0015.

Usage: python scripts/contains_scores.py RUN_FOLDER [RUN_FOLDER ...] [--list]

The second score also accepts a value that contains an accepted value as whole
words and names no wrong value ("LightGBM on lag features" for LightGBM). It is
computed from each run's saved answers.jsonl; no model is called. --list prints
every re-scored answer, so a reader can check each one.
"""

import sys

from tracemem.eval.contains import rescore, score_table
from tracemem.eval.report import load_run


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--list"]
    if not args:
        print(__doc__)
        return 2
    print(score_table(args))
    if "--list" in sys.argv[1:]:
        for folder in args:
            manifest, rows = load_run(folder)
            for before, after in zip(rows, rescore(rows)):
                if before.outcome != after.outcome:
                    print(f"{manifest['system']}\t{before.scenario_id}\t{before.question.question_id}\t"
                          f"{before.answer.value!r}\taccepted: {before.expected.accepted_values}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
