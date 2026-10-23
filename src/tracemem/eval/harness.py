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
from tracemem.eval.resolver_metrics import score_scenario, summarize
from tracemem.resolver import FatalModelError, ResolverConfigError, ResolverInputError
from tracemem.schema import Candidate, Operation, Scenario, Usage, turn_time
from tracemem.systems.base import (
    SystemSpec,
    optional_candidates,
    optional_fingerprint,
    optional_operations,
    optional_rejected,
)

CONDITIONS = ("end_to_end", "gold_candidates")
RESOLVER_ABORTS = (ResolverConfigError, ResolverInputError, FatalModelError)


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
    resolver_events: dict[str, list[dict]] = field(default_factory=dict)
    resolver_usage: dict[str, Usage] = field(default_factory=dict)
    answer_usage: dict[str, Usage] = field(default_factory=dict)
    resolver_scores: list[dict] | None = None
    memory_events: dict[str, list[dict]] = field(default_factory=dict)
    status: str = "completed"
    failure: dict | None = None


class ScenarioRunAborted(RuntimeError):
    """Known setup/input/provider failure, retaining observations completed before it."""

    def __init__(self, error: Exception, rows: list[ScoredAnswer], system: object | None):
        self.error, self.rows, self.system = error, rows, system
        super().__init__(str(error))


class RunAborted(RuntimeError):
    """A failed run that the caller can persist, but must not report as a completed evaluation."""

    def __init__(self, result: RunResult):
        self.result = result
        super().__init__(result.failure["message"] if result.failure else "run aborted")


def run_scenario(spec: SystemSpec, scenario: Scenario, timeline: GoldTimeline | None = None,
                 condition: str = "end_to_end", vocabulary: str = "keys") -> tuple[list[ScoredAnswer], object]:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}; use one of {CONDITIONS}")
    timeline = timeline or replay(scenario)
    try:
        system = spec.factory(scenario.meta(vocabulary), timeline if spec.uses_gold else None)
    except RESOLVER_ABORTS as error:
        raise ScenarioRunAborted(error, [], None) from None
    if condition == "gold_candidates" and not getattr(system, "accepts_gold_candidates", False):
        raise ValueError(f"{spec.name} cannot run in the gold-candidate condition")

    by_session: dict[str, list] = {}
    for question in timeline.questions:
        by_session.setdefault(question.after, []).append(question)

    rows: list[ScoredAnswer] = []
    visible: set[str] = set()
    try:
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
    except RESOLVER_ABORTS as error:
        raise ScenarioRunAborted(error, rows, system) from None
    return rows, system


def _collect_scenario(result: RunResult, scenario: Scenario, rows: list[ScoredAnswer],
                      system: object | None, files: dict[str, Path] | None,
                      timeline: GoldTimeline | None = None) -> bool:
    result.rows.extend(rows)
    if files and scenario.scenario_id in files:
        data = Path(files[scenario.scenario_id]).read_bytes()
        result.scenario_files[scenario.scenario_id] = hashlib.sha256(data).hexdigest()[:16]
    if system is None:
        return False
    describe = getattr(system, "describe", None)
    if callable(describe):
        config = describe()
        if result.system_config and config.get("comparison") != result.system_config.get("comparison"):
            raise ValueError("controlled comparison configuration changed within a run")
        if not result.system_config:
            result.system_config = config
    ops = optional_operations(system)
    if ops is not None:
        result.operations[scenario.scenario_id] = ops
    rejected = optional_rejected(system)
    if rejected:
        result.rejected[scenario.scenario_id] = rejected
    cands = optional_candidates(system)
    if cands is not None:
        result.candidates[scenario.scenario_id] = cands
    events = getattr(system, "resolver_events", None)
    if callable(events):
        event_rows = events()
        if event_rows:
            result.resolver_events[scenario.scenario_id] = event_rows
    usage = getattr(system, "resolver_usage", None)
    if callable(usage):
        value = usage()
        if value is not None:
            result.resolver_usage[scenario.scenario_id] = value
    answer_usage = getattr(system, "answer_usage", None)
    if callable(answer_usage):
        value = answer_usage()
        if value is not None:
            result.answer_usage[scenario.scenario_id] = value
    memory_events = getattr(system, "memory_events", None)
    if callable(memory_events):
        result.memory_events[scenario.scenario_id] = memory_events()
    # Evaluate only after observation has finished. Gold stays on the scorer side.
    if result.condition == "gold_candidates" and timeline is not None and ops is not None:
        scores = score_scenario(timeline, ops, rejected or [],
                                result.resolver_events.get(scenario.scenario_id))
        if result.resolver_scores is None:
            result.resolver_scores = []
        result.resolver_scores.extend(scores)
        return True
    return False


def run(spec: SystemSpec, scenarios: list[Scenario], split: str, condition: str = "end_to_end",
        files: dict[str, Path] | None = None, vocabulary: str = "keys") -> RunResult:
    ids = [s.scenario_id for s in scenarios]
    if len(set(ids)) != len(ids):
        raise ValueError(f"duplicate scenario_id among {sorted(i for i in set(ids) if ids.count(i) > 1)}")
    result = RunResult(system=spec.name, uses_gold=spec.uses_gold, split=split, condition=condition, rows=[],
                       vocabulary=vocabulary)
    scored_scenarios = 0
    for scenario in scenarios:
        timeline = replay(scenario)
        try:
            rows, system = run_scenario(spec, scenario, timeline, condition=condition, vocabulary=vocabulary)
        except ScenarioRunAborted as aborted:
            try:
                _collect_scenario(result, scenario, aborted.rows, aborted.system, files)
            finally:
                close = getattr(aborted.system, "close", None)
                if callable(close):
                    close()
            result.status = "failed"
            result.failure = {"scenario_id": scenario.scenario_id, "error_type": type(aborted.error).__name__,
                              "message": str(aborted.error)}
            raise RunAborted(result) from None
        try:
            scored_scenarios += _collect_scenario(result, scenario, rows, system, files, timeline)
        finally:
            close = getattr(system, "close", None)
            if callable(close):
                close()
    if scored_scenarios != len(scenarios):
        result.resolver_scores = None  # a partial set of instrumented scenarios is not a full evaluation
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
    info = {
        "created_at": stamp,
        "system": result.system,
        "uses_gold_labels": result.uses_gold,
        "split": result.split,
        "condition": result.condition,
        "item_vocabulary_given_to_systems": result.vocabulary,
        "system_config": result.system_config,
        "status": result.status,
        "failure": result.failure,
        "git_commit": _git("rev-parse", "HEAD") or "unknown",
        "git_dirty": bool(status) if status is not None else None,
        "freeze_tag": _git("describe", "--tags", "--match", "freeze-*", "--abbrev=0"),
        "scenarios": result.scenario_files,
        "tracemem_version": __version__,
        "python": platform.python_version(),
        "command": ["tracemem", *sys.argv[1:]],  # never the absolute script path
    }
    if "comparison" in result.system_config:
        info["comparison"] = {**result.system_config["comparison"], "candidate_hashes": {
            sid: hashlib.sha256(json.dumps([c.model_dump() for c in candidates], sort_keys=True,
                                          ensure_ascii=False).encode()).hexdigest()
            for sid, candidates in result.candidates.items()
        }}
    return info


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
    comparison = info.get("comparison")
    info.update(extra_manifest or {})
    # Extra metadata cannot make an aborted evaluation look completed.
    info.update(status=result.status, failure=result.failure)
    if comparison is not None:
        info["comparison"] = comparison
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
    if result.resolver_events:
        with open(folder / "resolver_events.jsonl", "w", encoding="utf-8") as events_handle, \
                open(folder / "resolver_errors.jsonl", "w", encoding="utf-8") as errors_handle:
            for sid, events in result.resolver_events.items():
                for event in events:
                    line = json.dumps({**event, "scenario_id": sid}) + "\n"
                    events_handle.write(line)
                    if event["status"] in ("generation_failed", "aborted"):
                        errors_handle.write(line)
    usage_info = {}
    if result.resolver_usage:
        by_scenario = {sid: value.model_dump() for sid, value in result.resolver_usage.items()}
        total = {key: sum(value[key] for value in by_scenario.values())
                 for key in ("calls", "input_tokens", "output_tokens")}
        usage_info["resolver"] = {
            "total": total, "by_scenario": by_scenario, "tokens_are_provider_reported": True,
        }
    if result.answer_usage or "comparison" in result.system_config:
        # Cumulative hooks include calls for an aborted answer. Completed answer
        # rows are a fallback only for scenarios without that hook, never added
        # again to an already cumulative scenario total.
        by_scenario = {sid: value.model_dump() for sid, value in result.answer_usage.items()}
        for row in result.rows:
            if row.scenario_id in result.answer_usage or row.answer.usage is None:
                continue
            total = by_scenario.setdefault(row.scenario_id, Usage().model_dump())
            for key in ("calls", "input_tokens", "output_tokens"):
                total[key] += getattr(row.answer.usage, key)
        usage_info["answer"] = {"total": {
            key: sum(value[key] for value in by_scenario.values())
            for key in ("calls", "input_tokens", "output_tokens")
        }, "by_scenario": by_scenario, "tokens_are_provider_reported": True}
    if usage_info:
        (folder / "usage.json").write_text(json.dumps(usage_info, indent=2), encoding="utf-8")
    if result.memory_events:
        with open(folder / "memory_events.jsonl", "w", encoding="utf-8") as handle:
            for sid, events in result.memory_events.items():
                for event in events:
                    handle.write(json.dumps({**event, "scenario_id": sid}) + "\n")
    metrics = {
        name: {subset: {"value": v.value, "n": v.n} for subset, v in by_subset.items()}
        for name, by_subset in compute_all(result.rows, weighting=weighting).items()
    }
    metrics["weighting"] = weighting
    metrics["outcome_counts"] = outcome_counts(result.rows)
    (folder / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    if result.status == "completed" and result.condition == "gold_candidates" and result.resolver_scores is not None:
        resolver_metrics = {"schema_version": 1, "condition": result.condition, **summarize(result.resolver_scores)}
        (folder / "resolver_metrics.json").write_text(json.dumps(resolver_metrics, indent=2), encoding="utf-8")
        with open(folder / "resolver_scores.jsonl", "w", encoding="utf-8") as scores_handle, \
                open(folder / "resolver_analysis.jsonl", "w", encoding="utf-8") as errors_handle:
            for row in result.resolver_scores:
                line = json.dumps(row) + "\n"
                scores_handle.write(line)
                if row["errors"]:
                    errors_handle.write(line)
    return folder
