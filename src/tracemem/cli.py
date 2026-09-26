"""The `tracemem` command: validate scenarios, show their gold, run systems, compare runs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from tracemem.bench.load import load_scenario, scenario_paths
from tracemem.bench.replay import replay
from tracemem.bench.validate import check_file
from tracemem.eval.harness import CONDITIONS, run, write_run
from tracemem.eval.metrics import SUBSETS, compute_all, outcome_counts
from tracemem.eval.report import comparison_table
from tracemem.systems import REGISTRY

TEST_LOG = Path("results/test-runs.jsonl")


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def cmd_validate(args) -> int:
    paths = scenario_paths(*(args.paths or ["benchmark/scenarios/dev"]))
    errors = 0
    totals = {"current": 0, "candidate": 0, "mention": 0, "confusable": 0}
    for path in paths:
        redact = args.redact or "test" in Path(path).parts
        issues, stats = check_file(path)
        for issue in issues:
            print(issue.render(redact=redact))
            errors += issue.level == "error"
        if stats is not None:
            totals["current"] += stats.current_questions
            totals["candidate"] += stats.trap_candidate
            totals["mention"] += stats.trap_mention
            totals["confusable"] += stats.trap_confusable
            if not redact:
                print(f"{stats.scenario}: {stats.current_questions} current questions; traps: "
                      f"candidate {stats.trap_candidate}, mention {stats.trap_mention}, confusable {stats.trap_confusable}")
    n = totals["current"] or 1
    print(f"\n{len(paths)} scenario files, {errors} errors. Current questions: {totals['current']}; "
          f"share with a candidate trap {totals['candidate'] / n:.0%}, mention trap {totals['mention'] / n:.0%}, "
          f"confusable trap {totals['confusable'] / n:.0%}.")
    return 1 if errors else 0


def cmd_replay(args) -> int:
    scenario = load_scenario(args.scenario)
    timeline = replay(scenario)
    print(f"# {scenario.scenario_id}: {scenario.title} ({scenario.category})\n")
    for turn_id in timeline.turn_order:
        for op in timeline.ops_by_turn.get(turn_id, []):
            kind = f"{op.op} as {op.add_as}" if op.add_as else op.op
            targets = f" (targets {', '.join(op.targets)})" if op.targets else ""
            print(f"{turn_id:7} {kind:18} {op.item} = {op.value}{targets}")
    print("\n| question | kind | expected | stale | unconfirmed | traps | support |")
    print("|---|---|---|---|---|---|---|")
    for q in timeline.questions:
        e = timeline.expected[q.question_id]
        traps = ", ".join(n for n, f in (("candidate", e.trap_candidate), ("mention", e.trap_mention),
                                          ("confusable", e.trap_confusable)) if f)
        expected = e.expected_value if e.expected_status == "answer" else e.expected_status
        print(f"| {q.question_id} | {q.kind} | {expected} | {', '.join(e.stale_values)} | "
              f"{', '.join(e.unconfirmed_values)} | {traps} | {', '.join(e.required_support)} |")
    return 0


def _test_split_allowed(args) -> tuple[bool, str]:
    if (_git("status", "--porcelain") or "").strip():
        return False, "the working tree has uncommitted changes; commit before a test run"
    tag = _git("describe", "--tags", "--match", "freeze-*", "--abbrev=0")
    if tag:
        return True, tag
    if args.i_know_this_is_the_test_split:
        return True, "override: no freeze tag"
    return False, "no freeze-* tag is reachable from HEAD (see docs/working-agreement.md, section 4)"


def cmd_run(args) -> int:
    if args.system not in REGISTRY:
        print(f"unknown system {args.system!r}; known: {', '.join(REGISTRY)}")
        return 2
    freeze = None
    if args.split == "test":
        allowed, freeze = _test_split_allowed(args)
        if not allowed:
            print(f"refusing to run on the test split: {freeze}")
            return 2
    root = Path(args.root) / args.split
    paths = scenario_paths(root)
    if not paths:
        print(f"no scenarios under {root}")
        return 2
    for path in paths:
        issues, _ = check_file(path)
        errors = [i for i in issues if i.level == "error"]
        if errors:
            for issue in errors:
                print(issue.render(redact=args.split == "test"))
            print("refusing to run: fix the scenario errors above (tracemem validate)")
            return 2
    scenarios = [load_scenario(p) for p in paths]
    files = {s.scenario_id: p for s, p in zip(scenarios, paths)}
    spec = REGISTRY[args.system]
    try:
        result = run(spec, scenarios, args.split, condition=args.condition, files=files, vocabulary=args.vocabulary)
    except ValueError as error:
        print(f"cannot run: {error}")
        return 2
    folder = write_run(result, args.out, extra_manifest={"freeze": freeze}, weighting=args.weighting)
    metrics = compute_all(result.rows, weighting=args.weighting)
    label = spec.name + (" (uses gold labels: a probe or mock, not a baseline)" if spec.uses_gold else "")
    print(f"{label} on {args.split}, {args.condition}, {len(scenarios)} scenarios, {len(result.rows)} questions\n")
    subsets = ["all", "trap_candidate", "no_trap"]
    print("| metric | " + " | ".join(subsets) + " |")
    print("|---|" + "---|" * len(subsets))
    for name, by_subset in metrics.items():
        print(f"| {name} | " + " | ".join(f"{by_subset[s].fmt()} (n={by_subset[s].n})" for s in subsets) + " |")
    print(f"\noutcomes: {json.dumps(outcome_counts(result.rows))}\nsaved to {folder}")
    if args.split == "test":
        TEST_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(TEST_LOG, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "run": folder.name, "commit": _git("rev-parse", "HEAD"), "freeze": freeze,
                "system": spec.name, "condition": args.condition,
                "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "current_accuracy": metrics["current_accuracy"]["all"].value,
            }) + "\n")
        print(f"logged in {TEST_LOG}; commit this file together with the run's summary")
    return 0


def cmd_report(args) -> int:
    try:
        print(comparison_table(args.runs, stratify=not args.no_stratify, n=args.resamples,
                               weighting=args.weighting, allow_mixed=args.allow_mixed))
    except ValueError as error:
        print(f"cannot compare: {error}")
        return 2
    return 0


def cmd_blind(args) -> int:
    """Print a scenario's dialogue and questions without its script, for blind review."""
    scenario = load_scenario(args.scenario)
    print(f"# {scenario.scenario_id}\n")
    for session in scenario.sessions:
        print(f"## {session.id} ({session.date})")
        for turn in session.turns:
            print(f"{turn.id} {turn.speaker}: {turn.text}")
        print()
    print("## Questions (answer each from the dialogue alone: a value, 'nothing settled', or 'disputed')")
    for q in replay(scenario).questions:
        where = f" (as of {q.session})" if q.session else ""
        print(f"- after {q.after}{where}: {q.text}")
    return 0


def cmd_systems(args) -> int:
    for spec in REGISTRY.values():
        print(f"{spec.name:18} {spec.description}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tracemem", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="check scenario files and print trap statistics")
    p.add_argument("paths", nargs="*", help="files or folders (default: benchmark/scenarios/dev)")
    p.add_argument("--redact", action="store_true", help="print issue codes only (always on for test/)")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("replay", help="show a scenario's gold operations and expected answers")
    p.add_argument("scenario")
    p.set_defaults(func=cmd_replay)

    p = sub.add_parser("run", help="run one system over a split and score it")
    p.add_argument("--system", required=True)
    p.add_argument("--split", default="dev", choices=["dev", "test"])
    p.add_argument("--condition", default="end_to_end", choices=CONDITIONS)
    p.add_argument("--vocabulary", default="keys", choices=["keys", "none"],
                   help="whether systems receive the item keys (a team decision; recorded in the manifest)")
    p.add_argument("--weighting", default="question", choices=["question", "episode"])
    p.add_argument("--root", default="benchmark/scenarios")
    p.add_argument("--out", default="runs")
    p.add_argument("--i-know-this-is-the-test-split", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("report", help="compare saved runs with scenario-bootstrap intervals")
    p.add_argument("runs", nargs="+")
    p.add_argument("--no-stratify", action="store_true")
    p.add_argument("--resamples", type=int, default=2000)
    p.add_argument("--weighting", default="question", choices=["question", "episode"])
    p.add_argument("--allow-mixed", action="store_true", help="compare runs with different settings anyway")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("blind", help="print a scenario's dialogue without its script, for blind review")
    p.add_argument("scenario")
    p.set_defaults(func=cmd_blind)

    p = sub.add_parser("systems", help="list runnable systems")
    p.set_defaults(func=cmd_systems)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
