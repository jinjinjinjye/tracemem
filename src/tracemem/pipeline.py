"""TraceMem's write and read paths, assembled from the five components.

Write path, per turn: extract -> match -> resolve -> apply to the operation log.
Read path, per question: retrieve -> answer, where the answer step sees only the
retrieved records and the turns those records cite.
"""

from __future__ import annotations

from datetime import datetime

from tracemem.components import Answerer, Extractor, Matcher, Resolver, Retriever
from tracemem.ops import InvalidOperation, OpLog
from tracemem.schema import Answer, Candidate, Operation, ScenarioMeta, SystemQuestion, Turn


class TraceMemPipeline:
    accepts_gold_candidates = True

    def __init__(self, meta: ScenarioMeta, extractor: Extractor, matcher: Matcher, resolver: Resolver,
                 retriever: Retriever, answerer: Answerer, budget_tokens: int = 2000, name: str = "tracemem"):
        self.name = name
        self.meta = meta
        self.extractor, self.matcher, self.resolver = extractor, matcher, resolver
        self.retriever, self.answerer = retriever, answerer
        self.budget_tokens = budget_tokens
        self.log = OpLog(meta.project_id)
        self.turns: dict[str, Turn] = {}
        self._candidates: list[Candidate] = []
        self._rejected: list[tuple[Operation, str]] = []

    # -- write path ----------------------------------------------------------------

    def observe(self, turn: Turn, when: datetime, gold_candidates: list[Candidate] | None = None) -> None:
        self.turns[turn.id] = turn
        self.log.observe_turn(turn.id, when, turn.speaker)
        candidates = gold_candidates if gold_candidates is not None else self.extractor.extract(turn, when, self.meta)
        for candidate in candidates:
            self._candidates.append(candidate)
            related = self.matcher.match(candidate, self.log)
            op = self.resolver.resolve(candidate, related)
            try:
                self.log.apply(op)
            except InvalidOperation as error:
                # A rejected operation changes nothing; it is kept for the resolver metrics.
                self._rejected.append((op, str(error)))

    # -- read path -------------------------------------------------------------------

    def answer(self, question: SystemQuestion) -> Answer:
        records = self.retriever.retrieve(question, self.log, self.budget_tokens)
        cited = {t for record in records for t in record.source_turn_ids}
        turns = {t: self.turns[t] for t in cited if t in self.turns}
        return self.answerer.answer(question, records, turns)

    # -- optional hooks used by the harness -----------------------------------------------

    def fingerprint(self) -> str:
        return self.log.fingerprint()

    def operations(self) -> list[Operation]:
        return list(self.log.ops)

    def rejected_operations(self) -> list[tuple[Operation, str]]:
        return list(self._rejected)

    def candidates(self) -> list[Candidate]:
        return list(self._candidates)

    def describe(self) -> dict:
        return {
            "extractor": type(self.extractor).__name__,
            "matcher": type(self.matcher).__name__,
            "resolver": type(self.resolver).__name__,
            "retriever": type(self.retriever).__name__,
            "answerer": type(self.answerer).__name__,
            "budget_tokens": self.budget_tokens,
        }
