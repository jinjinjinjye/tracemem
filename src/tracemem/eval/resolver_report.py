"""Readable operation-level diagnostics from saved scorer rows; no model or scenario access."""

from __future__ import annotations

import json
from pathlib import Path

from tracemem.eval.resolver_metrics import LABELS, summarize


def _value(metric: dict) -> str:
    value = metric["value"]
    return ("n/a" if value is None else f"{value:.3f}") + f" (n={metric['n']})"


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def resolver_report(folder: str | Path, max_errors: int = 10) -> str:
    """Recompute scores from the saved rows; legacy or incomplete runs require a new evaluation."""
    if max_errors < 0:
        raise ValueError("max_errors must be nonnegative")
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status", "completed") != "completed":
        raise ValueError("cannot score a failed or incomplete run; inspect its resolver events")
    if manifest.get("condition") != "gold_candidates":
        raise ValueError("resolver evaluation requires the gold_candidates condition")
    scores_path = folder / "resolver_scores.jsonl"
    metrics_path = folder / "resolver_metrics.json"
    if not scores_path.is_file() or not metrics_path.is_file():
        raise ValueError("run has no saved resolver evaluation; rerun in gold_candidates with an operations hook")
    saved = json.loads(metrics_path.read_text(encoding="utf-8"))
    if saved.get("schema_version") != 1 or saved.get("condition") != "gold_candidates":
        raise ValueError("unsupported resolver evaluation format")
    rows = [json.loads(line) for line in scores_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = summarize(rows)
    if saved != {"schema_version": 1, "condition": "gold_candidates", **summary}:
        raise ValueError("resolver metrics do not match the saved scorer rows")
    mock = " (uses gold labels; component diagnostic)" if manifest.get("uses_gold_labels") else ""
    lines = [f"Resolver evaluation: {_cell(manifest['system'])}{mock}",
             f"Split: {_cell(manifest['split'])}. Condition: gold_candidates. Weighting: candidate.",
             "", "| metric | value |", "|---|---|"]
    for name, metric in summary["metrics"].items():
        lines.append(f"| {name} | {_value(metric)} |")
    lines += [f"| micro_f1 | {_value(summary['micro_f1'])} |",
              f"| macro_f1 | {_value(summary['macro_f1'])} |",
              "", "| operation | precision | recall | F1 | gold support | predicted |",
              "|---|---|---|---|---|---|"]
    for label in LABELS:
        score = summary["labels"][label]
        lines.append(f"| {label} | {_value(score['precision'])} | {_value(score['recall'])} | "
                     f"{_value(score['f1'])} | {score['support']} | {score['predicted']} |")
    columns = (*LABELS, "MISSING", "INVALID")
    for title, key in (("Gold operation / emitted operation", "confusion"),
                       ("Script act / emitted operation", "confusion_by_act")):
        lines += ["", title, "", "| gold | " + " | ".join(columns) + " |",
                  "|---|" + "---|" * len(columns)]
        for label, counts in summary[key].items():
            lines.append(f"| {_cell(label)} | " + " | ".join(str(counts.get(c, 0)) for c in columns) + " |")
    lines += ["", "Counts: " + json.dumps(summary["counts"], sort_keys=True),
              "Error flags (may overlap): " + json.dumps(summary["error_counts"], sort_keys=True),
              "", "Label scores include emitted operations rejected by storage. Exact-operation accuracy requires application.",
              "State accuracy follows the system's cumulative history; earlier errors can affect later candidates.",
              "Missing outputs remain in the gold denominator. Undefined metrics are n/a; macro F1 averages defined labels."]
    errors = [row for row in rows if row["errors"]]
    if errors and max_errors:
        lines += ["", f"First {min(len(errors), max_errors)} of {len(errors)} error rows (see resolver_analysis.jsonl):",
                  "", "| scenario | candidate | source text | act | status | errors |", "|---|---|---|---|---|---|"]
        for row in errors[:max_errors]:
            cells = [row["scenario_id"], row["candidate_id"], row["text"], row["act"],
                     row["status"], ", ".join(row["errors"])]
            lines.append("| " + " | ".join(_cell(cell) for cell in cells) + " |")
    return "\n".join(lines)
