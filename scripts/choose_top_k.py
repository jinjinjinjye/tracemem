"""Choose k, the number of records each answer shows (decision record 0011, question 4).

The rule, fixed before any system is scored: k is the smallest number of records
that puts every turn a question's correct answer rests on (its required support,
computed by the replay) on the page for at least 90% of the development questions.
It is measured on the similarity system's store, one record per statement exactly as
given, ranked by closeness to the question with the shared retriever and the
embedding model the systems use. No system's answers are read, so the rule cannot
favour one system. Questions whose correct answer rests on no turn (for example
"none" for a value never replaced) are left out of the count.

Usage: python scripts/choose_top_k.py [--threshold 0.9] [scenario files or folders]
Needs the local embedding server (docs/local-model.md); embeddings are cached.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tracemem.bench.load import load_scenario
from tracemem.bench.replay import replay
from tracemem.eval.harness import turn_time
from tracemem.ops import flat_records
from tracemem.retrieval import DEFAULT_HALF_LIFE_DAYS, OllamaEmbeddings, SharedRetriever
from tracemem.systems.comparison import DEFAULT_BUDGET_BYTES, _quoted_line


def scenario_files(paths: list[str]) -> list[Path]:
    found = []
    for path in map(Path, paths or ["benchmark/scenarios/dev"]):
        found += sorted(path.rglob("*.yaml")) if path.is_dir() else [path]
    return found


def smallest_k_per_question(path: Path, retriever: SharedRetriever) -> list[tuple[str, int, int | None]]:
    """(question id, records in the store, smallest covering k or None) for each question with support."""
    scenario = load_scenario(path)
    timeline = replay(scenario)
    by_session: dict[str, list] = {}
    for question in timeline.questions:
        by_session.setdefault(question.after, []).append(question)
    candidates, times, turns, rows = [], {}, {}, []
    for number, session in enumerate(scenario.sessions, start=1):
        for index, turn in enumerate(session.turns):
            times[turn.id] = turn_time(session.date, index, number)
            turns[turn.id] = turn
            candidates += timeline.candidates_by_turn.get(turn.id, [])
        for question in by_session.get(session.id, []):
            support = set(timeline.expected[question.question_id].required_support)
            if not support:
                continue
            records = flat_records(scenario.project_id, candidates, times)
            line = lambda record: _quoted_line(record, turns)  # noqa: E731 - the similarity system's line
            smallest = None
            for k in range(1, len(records) + 1):
                chosen = retriever.select(question.text, records, None, DEFAULT_BUDGET_BYTES, line, top_k=k)
                if support <= {source for record in chosen for source in record.source_turn_ids}:
                    smallest = k
                    break
            rows.append((f"{scenario.scenario_id}:{question.question_id}", len(records), smallest))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--threshold", type=float, default=0.9)
    args = parser.parse_args(argv)
    retriever = SharedRetriever(0.0, DEFAULT_HALF_LIFE_DAYS, OllamaEmbeddings.from_env())
    rows = [row for path in scenario_files(args.paths) for row in smallest_k_per_question(path, retriever)]
    if not rows:
        print("no questions with required support")
        return 1
    largest = max(size for _, size, _ in rows)
    print(f"{len(rows)} questions with required support; stores hold up to {largest} records")
    print("| k | questions with all support on the page | share |")
    print("|---|---|---|")
    chosen = None
    for k in range(1, largest + 1):
        covered = sum(1 for _, _, smallest in rows if smallest is not None and smallest <= k)
        share = covered / len(rows)
        print(f"| {k} | {covered} of {len(rows)} | {share:.3f} |")
        if chosen is None and share >= args.threshold:
            chosen = k
    uncovered = [qid for qid, _, smallest in rows if smallest is None]
    if uncovered:
        print("never fully covered:", ", ".join(uncovered))
    print(f"k = {chosen} (smallest k with a share of at least {args.threshold})")
    return 0 if chosen is not None else 1


if __name__ == "__main__":
    sys.exit(main())
