"""Load scenario files and expand their checkpoint questions."""

from __future__ import annotations

from pathlib import Path

import yaml

from tracemem.schema import Question, Scenario, ScriptEvent


def load_scenario(path: str | Path) -> Scenario:
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return Scenario.model_validate(data)


def scenario_paths(*roots: str | Path) -> list[Path]:
    """Every *.yaml file under the given files or folders, sorted for a stable order."""
    paths: list[Path] = []
    for root in roots:
        root = Path(root)
        if not root.exists():
            raise FileNotFoundError(f"no such file or folder: {root}")
        if root.is_file():
            paths.append(root)
        else:
            paths.extend(sorted([*root.rglob("*.yaml"), *root.rglob("*.yml")]))
    return paths


def load_split(root: str | Path, split: str) -> list[Scenario]:
    """Load every scenario under ``root/split``; each file's ``split`` field must agree with its folder."""
    scenarios = [load_scenario(path) for path in scenario_paths(Path(root) / split)]
    for scenario in scenarios:
        if scenario.split != split:
            raise ValueError(f"{scenario.scenario_id} says split={scenario.split!r} but lives in {split}/")
    return scenarios


def candidate_bearing(event: ScriptEvent) -> bool:
    """True for every act that produces a memory candidate; a mention produces none."""
    return event.act != "mention"


def expand_questions(scenario: Scenario) -> list[Question]:
    """Explicit questions plus, when enabled, one automatic `current` question per item and session.

    An automatic question is asked after every session from the first session in
    which its item has a candidate-bearing event through the last session.
    Explicit questions with the same id replace automatic ones.
    """
    session_ids = [session.id for session in scenario.sessions]
    turn_session = {turn.id: session.id for session in scenario.sessions for turn in session.turns}
    questions: dict[str, Question] = {}

    if scenario.auto_questions:
        for spec in scenario.items:
            if not spec.ask:
                continue
            first = [
                session_ids.index(turn_session[event.turn])
                for event in scenario.script
                if event.item == spec.key and candidate_bearing(event) and event.turn in turn_session
            ]
            if not first:
                continue
            for session_id in session_ids[min(first):]:
                qid = f"{spec.key}@{session_id}"
                questions[qid] = Question(
                    question_id=qid,
                    scenario_id=scenario.scenario_id,
                    after=session_id,
                    kind="current",
                    item=spec.key,
                    text=spec.ask,
                )

    for spec in scenario.questions:
        questions[spec.id] = Question(
            question_id=spec.id,
            scenario_id=scenario.scenario_id,
            after=spec.after,
            kind=spec.kind,
            item=spec.item,
            text=spec.text,
            session=spec.session,
        )

    order = {session_id: index for index, session_id in enumerate(session_ids)}
    return sorted(questions.values(), key=lambda q: (order.get(q.after, len(order)), q.question_id))
