"""Comparison tables from saved runs, with scenario-bootstrap intervals."""

from __future__ import annotations

import json
from pathlib import Path

from tracemem.eval.bootstrap import _strata, bootstrap, paired_bootstrap
from tracemem.eval.metrics import METRICS, SUBSETS, ScoredAnswer, episode_weights
from tracemem.schema import Answer, ExpectedAnswer, Question

HEADLINE = [
    ("current_accuracy", "all"),
    ("current_accuracy", "trap_candidate"),
    ("current_accuracy", "no_trap"),
    ("stale_answer_rate", "all"),
    ("incorrect_replacement_rate", "all"),
    ("presented_as_current_rate", "trap_candidate"),
    ("false_certainty_rate", "all"),
    ("false_conflict_rate", "all"),
    ("non_answer_rate", "all"),
    ("historical_accuracy", "all"),
    ("supported_answer_rate", "all"),
]


def load_run(folder: str | Path) -> tuple[dict, list[ScoredAnswer]]:
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    with open(folder / "answers.jsonl", encoding="utf-8") as handle:
        for line in handle:
            data = json.loads(line)
            rows.append(
                ScoredAnswer(
                    question=Question.model_validate(data["question"]),
                    expected=ExpectedAnswer.model_validate(data["expected"]),
                    answer=Answer.model_validate(data["answer"]),
                    outcome=data["outcome"],
                    visible_turns=frozenset(data["visible_turns"]),
                    category=data.get("category", ""),
                )
            )
    return manifest, rows


def _label(manifest: dict) -> str:
    tag = " (uses gold labels)" if manifest.get("uses_gold_labels") else ""
    return f"{manifest['system']}{tag}"


def _subset(rows, subset):
    keep = SUBSETS[subset]
    return [r for r in rows if keep(r)]


def _metric(name: str, weighting: str):
    fn = METRICS[name]
    if weighting == "episode":
        return lambda rows: fn(rows, episode_weights(rows))
    return fn


def comparison_table(folders: list[str | Path], stratify: bool = True, n: int = 2000,
                     weighting: str = "question", allow_mixed: bool = False) -> str:
    runs = [load_run(folder) for folder in folders]
    keys = ("split", "condition", "item_vocabulary_given_to_systems", "scenarios")
    if not allow_mixed:
        for manifest, _ in runs[1:]:
            differing = [k for k in keys if manifest.get(k) != runs[0][0].get(k)]
            if differing:
                raise ValueError(f"runs differ in {differing}; compare like with like, or pass --allow-mixed")
    lines = ["| metric | subset | " + " | ".join(_label(m) for m, _ in runs) + " |",
             "|---|---|" + "---|" * len(runs)]
    for metric_name, subset in HEADLINE:
        cells = []
        for _, rows in runs:
            chosen = _subset(rows, subset)
            interval = bootstrap(_metric(metric_name, weighting), chosen, n=n, stratify=stratify)
            cells.append(f"{interval.fmt()} (scen. {interval.n_scenarios}, q. {METRICS[metric_name](chosen).n})")
        lines.append(f"| {metric_name} | {subset} | " + " | ".join(cells) + " |")
    if len(runs) > 1:
        base_manifest, base_rows = runs[0]
        lines += ["", f"Paired differences against {_label(base_manifest)} (other minus base), 95% scenario-bootstrap intervals:", "",
                  "| metric | subset | " + " | ".join(_label(m) for m, _ in runs[1:]) + " |",
                  "|---|---|" + "---|" * (len(runs) - 1)]
        for metric_name, subset in HEADLINE:
            cells = []
            for _, rows in runs[1:]:
                diff = paired_bootstrap(_metric(metric_name, weighting), _subset(rows, subset), _subset(base_rows, subset),
                                        n=n, stratify=stratify)
                cells.append(diff.fmt())
            lines.append(f"| {metric_name} | {subset} | " + " | ".join(cells) + " |")
    applied = stratify and bool(_strata(runs[0][1]))
    lines += ["", f"Weighting: {weighting}. Stratified by category: {'yes' if applied else 'no'}"
              + ("" if applied or not stratify else " (a category has fewer than two scenarios, so plain resampling was used)") + ".",
              "Intervals are shown only when at least 5 scenarios contribute; otherwise only the estimate is given."]
    return "\n".join(lines)
