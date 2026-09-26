"""Run a system over scenarios under the same rules for every system.

The rules, each enforced here and tested in tests/test_harness.py:

1. Every scenario starts with a new system instance, so nothing leaks between scenarios.
2. Turns arrive strictly in order; questions are asked after the last turn of their session.
3. A question is a probe, not a turn: it is never passed to ``observe``, and a
   system whose memory changes while answering raises AnswerMutatedState.
4. Gold candidates are passed only in the gold-candidate condition; gold labels
   reach only systems registered with ``uses_gold`` (probes and mocks).
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from tracemem import __version__
from tracemem.bench.replay import GoldTimeline, replay
from tracemem.eval.classify import classify
from tracemem.eval.metrics import ScoredAnswer, compute_all, outcome_counts
from tracemem.schema import Candidate, Operation, Scenario, turn_time
from tracemem.systems.base import (
    SystemSpec,
    optional_candidates,
    optional_fingerprint,
    optional_operations,
    optional_rejected,
)

CONDITIONS = ("end_to_end", "gold_candidates")


class AnswerMutatedState(RuntimeError):
    """A system changed its memory while answering a question."""


@dataclass
class RunResult:
    system: str
    uses_gold: bool
    split: str
    condition: str
    rows: list[ScoredAnswer]
    vocabulary: str = "keys"
    system_config: dict = field(default_factory=dict)
    operations: dict[str, list[Operation]] = field(default_factory=dict)
    rejected: dict[str, list] = field(default_factory=dict)
    candidates: dict[str, list[Candidate]] = field(default_factory=dict)
    scenario_files: dict[str, str] = field(default_factory=dict)


def run_scenario(spec: SystemSpec, scenario: Scenario, timeline: GoldTimeline | None = None,
                 condition: str = "end_to_end", vocabulary: str = "keys") -> tuple[list[ScoredAnswer], object]:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}; use one of {CONDITIONS}")
    timeline = timeline or replay(scenario)
    system = spec.factory(scenario.meta(vocabulary), timeline if spec.uses_gold else None)
    if condition == "gold_candidates" and not getattr(system, "accepts_gold_candidates", False):
        raise ValueError(f"{spec.name} cannot run in the gold-candidate condition")

    by_session: dict[str, list] = {}
    for question in timeline.questions:
        by_session.setdefault(question.after, []).append(question)

    rows: list[ScoredAnswer] = []
    visible: set[str] = set()
    for number, session in enumerate(scenario.sessions, start=1):
        for index, turn in enumerate(session.turns):
            when = turn_time(session.date, index, number)
            if condition == "gold_candidates":
                system.observe(turn, when, gold_candidates=timeline.candidates_by_turn.get(turn.id, []))
            else:
                system.observe(turn, when)
            visible.add(turn.id)
        for question in by_session.get(session.id, []):
            before = optional_fingerprint(system)
            answer = system.answer(question.for_system(timeline.salt))
            if before is not None and optional_fingerprint(system) != before:
                raise AnswerMutatedState(f"{spec.name} changed its memory while answering {question.question_id}")
            expected = timeline.expected[question.question_id]
            rows.append(ScoredAnswer(question, expected, answer, classify(answer, expected), frozenset(visible),
                                     scenario.category))
    return rows, system


def run(spec: SystemSpec, scenarios: list[Scenario], split: str, condition: str = "end_to_end",
        files: dict[str, Path] | None = None, vocabulary: str = "keys") -> RunResult:
    ids = [s.scenario_id for s in scenarios]
    if len(set(ids)) != len(ids):
        raise ValueError(f"duplicate scenario_id among {sorted(i for i in set(ids) if ids.count(i) > 1)}")
    result = RunResult(system=spec.name, uses_gold=spec.uses_gold, split=split, condition=condition, rows=[],
                       vocabulary=vocabulary)
    for scenario in scenarios:
        rows, system = run_scenario(spec, scenario, condition=condition, vocabulary=vocabulary)
        describe = getattr(system, "describe", None)
        if callable(describe) and not result.system_config:
            result.system_config = describe()
        result.rows.extend(rows)
        ops = optional_operations(system)
        if ops is not None:
            result.operations[scenario.scenario_id] = ops
        rejected = optional_rejected(system)
        if rejected:
            result.rejected[scenario.scenario_id] = rejected
        cands = optional_candidates(system)
        if cands is not None:
            result.candidates[scenario.scenario_id] = cands
        if files and scenario.scenario_id in files:
            data = Path(files[scenario.scenario_id]).read_bytes()
            result.scenario_files[scenario.scenario_id] = hashlib.sha256(data).hexdigest()[:16]
    return result


# ---------------------------------------------------------------------------
# Writing a run to disk
# ---------------------------------------------------------------------------


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, check=True, timeout=10)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def manifest(result: RunResult, stamp: str) -> dict:
    status = _git("status", "--porcelain")
    return {
        "created_at": stamp,
        "system": result.system,
        "uses_gold_labels": result.uses_gold,
        "split": result.split,
        "condition": result.condition,
        "item_vocabulary_given_to_systems": result.vocabulary,
        "system_config": result.system_config,
        "git_commit": _git("rev-parse", "HEAD") or "unknown",
        "git_dirty": bool(status) if status is not None else None,
        "freeze_tag": _git("describe", "--tags", "--match", "freeze-*", "--abbrev=0"),
        "scenarios": result.scenario_files,
        "tracemem_version": __version__,
        "python": platform.python_version(),
        "command": ["tracemem", *sys.argv[1:]],  # never the absolute script path
    }


def write_run(result: RunResult, out_root: str | Path, extra_manifest: dict | None = None,
              weighting: str = "question") -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = Path(out_root) / f"{stamp}-{result.system}-{result.split}-{result.condition}"
    folder, attempt = base, 1
    while True:
        try:
            folder.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            attempt += 1
            folder = base.with_name(f"{base.name}-{attempt}")
    info = manifest(result, stamp)
    info.update(extra_manifest or {})
    (folder / "manifest.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    with open(folder / "answers.jsonl", "w", encoding="utf-8") as handle:
        for row in result.rows:
            handle.write(json.dumps({
                "scenario_id": row.scenario_id,
                "category": row.category,
                "question": row.question.model_dump(),
                "expected": row.expected.model_dump(),
                "answer": row.answer.model_dump(),
                "outcome": row.outcome,
                "visible_turns": sorted(row.visible_turns),
            }) + "\n")
    if result.operations:
        with open(folder / "ops.jsonl", "w", encoding="utf-8") as handle:
            for sid, ops in result.operations.items():
                for op in ops:
                    handle.write(json.dumps({"scenario_id": sid, **op.model_dump()}) + "\n")
    if result.rejected:
        with open(folder / "rejected_ops.jsonl", "w", encoding="utf-8") as handle:
            for sid, pairs in result.rejected.items():
                for op, reason in pairs:
                    handle.write(json.dumps({"scenario_id": sid, **op.model_dump(), "rejection": reason}) + "\n")
    if result.candidates:
        with open(folder / "candidates.jsonl", "w", encoding="utf-8") as handle:
            for sid, cands in result.candidates.items():
                for cand in cands:
                    handle.write(json.dumps({"scenario_id": sid, **cand.model_dump()}) + "\n")
    metrics = {
        name: {subset: {"value": v.value, "n": v.n} for subset, v in by_subset.items()}
        for name, by_subset in compute_all(result.rows, weighting=weighting).items()
    }
    metrics["weighting"] = weighting
    metrics["outcome_counts"] = outcome_counts(result.rows)
    (folder / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return folder
