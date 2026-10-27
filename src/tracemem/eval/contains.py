"""A second score beside the strict one: a value that contains an accepted value (decision record 0015).

The strict scorer (``classify.py``) stays the reported number: the value field
must hold the value alone (docs/metrics.md, section 1). Some systems copy a
phrase from their memory into the value ("LightGBM on lag features" for
LightGBM), which the strict scorer counts as a wrong value. This score
re-labels such an answer as correct, so a reader can see how much of a gap is
formatting rather than memory.

The rule changes only answers scored ``wrong_other`` on a question whose gold
is a settled value. Such an answer counts as correct when its value contains
an accepted value as whole words and names no stale, unconfirmed, confusable
or current value. The guard keeps it cautious: "LightGBM instead of Prophet"
stays wrong. Every other outcome is left as the strict scorer set it.
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from tracemem.eval.bootstrap import bootstrap
from tracemem.eval.metrics import ScoredAnswer, current_accuracy, historical_accuracy
from tracemem.eval.report import load_run
from tracemem.schema import normalise


def _names(value: str, forms: list[str]) -> bool:
    """True when one of the forms occurs in the value as whole words."""
    return any(form and re.search(r"(?<![a-z0-9])" + re.escape(form) + r"(?![a-z0-9])", value) for form in forms)


def contains_outcome(row: ScoredAnswer) -> str:
    if row.outcome != "wrong_other" or row.expected.expected_status != "answer" or row.answer.status != "answer":
        return row.outcome
    value = normalise(row.answer.value)
    e = row.expected
    wrong = e.stale_values + e.unconfirmed_values + e.confusable_values + e.current_values
    if _names(value, e.accepted_values) and not _names(value, wrong):
        return "correct"
    return row.outcome


def rescore(rows: list[ScoredAnswer]) -> list[ScoredAnswer]:
    return [replace(r, outcome=contains_outcome(r)) for r in rows]


def score_table(folders: list[str | Path], n: int = 2000, stratify: bool = True) -> str:
    """Present and past accuracy of each run, strict and with the second score, with 95% intervals."""
    lines = ["| run | present, strict | present, contains | past, strict | past, contains | re-scored |",
             "|---|---|---|---|---|---|"]
    for folder in folders:
        manifest, rows = load_run(folder)
        loose = rescore(rows)
        cells = []
        for metric in (current_accuracy, historical_accuracy):
            for chosen in (rows, loose):
                interval = bootstrap(metric, chosen, n=n, stratify=stratify)
                cells.append(f"{interval.fmt()} (q. {metric(chosen).n})")
        changed = sum(a.outcome != b.outcome for a, b in zip(rows, loose))
        lines.append(f"| {manifest['system']} ({Path(folder).name}) | " + " | ".join(cells) + f" | {changed} |")
    lines += ["", "Strict is the reported score (docs/metrics.md, section 1). 'Contains' also accepts a value that "
              "contains an accepted value as whole words and names no wrong value (decision record 0015). "
              "Intervals: 95% scenario bootstrap, shown when at least 5 scenarios contribute."]
    return "\n".join(lines)
