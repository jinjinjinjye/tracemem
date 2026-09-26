"""Probe systems: simple rules applied to the gold labels of turns seen so far.

Probes need no language model and run in seconds. They are not baselines. They
answer two questions before any money is spent:

* Does the scorer work? The oracle must score perfectly, and always-oldest must
  be marked stale wherever an older value was replaced.
* Can the benchmark tell TraceMem from recency at all? The two "latest" probes
  show how often simply taking the newest statement is already right.

A probe reads only the labels of turns it has observed, never later ones
(tests/test_probes.py checks this by truncating scenarios).
"""

from __future__ import annotations

from datetime import datetime

from tracemem.bench.load import candidate_bearing
from tracemem.bench.replay import GoldTimeline, event_value, suggestion_map
from tracemem.schema import Answer, Candidate, Question, ScenarioMeta, ScriptEvent, SystemQuestion, Turn, session_of


class _Probe:
    name = "probe"

    def __init__(self, meta: ScenarioMeta, gold: GoldTimeline | None):
        if gold is None:
            raise ValueError(f"{self.name} needs the gold timeline")
        self.gold = gold
        self.events: list[ScriptEvent] = []
        self.turns: list[str] = []
        # Probes are allowed gold labels; they map the opaque question back to its item.
        self.by_public_id = {gold.public_id(q): q for q in gold.questions}

    def observe(self, turn: Turn, when: datetime, gold_candidates: list[Candidate] | None = None) -> None:
        self.turns.append(turn.id)
        self.events.extend(self.gold.events_by_turn.get(turn.id, []))

    def fingerprint(self) -> str:
        return str(len(self.turns))

    def _window(self, question: Question) -> list[ScriptEvent]:
        """Events up to the end of the session the question is about."""
        if question.kind != "as_of":
            return self.events
        order = [s.id for s in self.gold.scenario.sessions]
        allowed_sessions = set(order[: order.index(question.session) + 1])  # works for an empty session too
        return [e for e in self.events if session_of(e.turn) in allowed_sessions]

    def _values(self, events: list[ScriptEvent], item: str, include_mentions: bool) -> list[tuple[str, str]]:
        """(value, turn) pairs for the item, oldest first; within a turn, mentions before decisions."""
        position = {t: i for i, t in enumerate(self.gold.turn_order)}
        events = sorted(events, key=lambda e: (position[e.turn], candidate_bearing(e)))
        suggestions = suggestion_map(events)
        pairs = []
        for event in events:
            if event.item != item or (not include_mentions and not candidate_bearing(event)):
                continue
            value = event_value(event, suggestions)
            if value is not None:
                pairs.append((value, event.turn))
        return pairs

    @staticmethod
    def _answer(pair: tuple[str, str] | None) -> Answer:
        if pair is None:
            return Answer(status="none", text="No value found.")
        value, turn = pair
        return Answer(status="answer", value=value, cited_turn_ids=[turn], text=f"{value} ({turn})")

    def _pick(self, pairs: list[tuple[str, str]], kind: str) -> tuple[str, str] | None:
        raise NotImplementedError

    def _from_pairs(self, pairs: list[tuple[str, str]], question: Question) -> Answer:
        if question.kind == "previous":
            if not pairs:
                return self._answer(None)
            current = self._pick(pairs, "current")[0]
            earlier = [p for p in pairs if p[0] != current]
            return self._answer(self._pick(earlier, "current") if earlier else None)
        return self._answer(self._pick(pairs, "current") if pairs else None)


class OracleProbe(_Probe):
    """Returns the replayed expected answer and cites the turns that established it."""

    name = "oracle"

    def answer(self, question: SystemQuestion) -> Answer:
        expected = self.gold.expected[self.by_public_id[question.question_id].question_id]
        return Answer(
            status=expected.expected_status,
            value=expected.expected_value,
            cited_turn_ids=list(expected.required_support),
            context_turn_ids=list(expected.required_support),
            text="oracle",
        )


class AlwaysOldestProbe(_Probe):
    """Answers with the first value ever stated for the item."""

    name = "always-oldest"

    def _pick(self, pairs, kind):
        return pairs[0]

    def answer(self, public: SystemQuestion) -> Answer:
        question = self.by_public_id[public.question_id]
        return self._from_pairs(self._values(self._window(question), question.item, include_mentions=False), question)


class LatestCandidateProbe(_Probe):
    """Answers with the newest value from any statement that would become a memory record."""

    name = "latest-candidate"

    def _pick(self, pairs, kind):
        return pairs[-1]

    def answer(self, public: SystemQuestion) -> Answer:
        question = self.by_public_id[public.question_id]
        return self._from_pairs(self._values(self._window(question), question.item, include_mentions=False), question)


class LatestMentionProbe(_Probe):
    """Answers with the newest value mentioned in any way, including questions and recollections."""

    name = "latest-mention"

    def _pick(self, pairs, kind):
        return pairs[-1]

    def answer(self, public: SystemQuestion) -> Answer:
        question = self.by_public_id[public.question_id]
        return self._from_pairs(self._values(self._window(question), question.item, include_mentions=True), question)


class AlwaysConflictProbe(_Probe):
    """Always reports a conflict. Shows how far the error rates can be lowered by never committing."""

    name = "always-conflict"

    def answer(self, question: SystemQuestion) -> Answer:
        return Answer(status="conflict", text="always conflict")


class AlwaysNoneProbe(_Probe):
    """Always says nothing is settled. Shows how far the error rates can be lowered by never answering."""

    name = "always-none"

    def answer(self, question: SystemQuestion) -> Answer:
        return Answer(status="none", text="always none")
