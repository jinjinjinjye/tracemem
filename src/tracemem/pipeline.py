"""TraceMem's write and read paths, assembled from the five components.

Write path, per turn: extract -> match -> resolve -> apply to the operation log.
Read path, per question: retrieve -> answer, where the answer step sees only the
retrieved records and the turns those records cite.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime

from tracemem.components import Answerer, Extractor, Matcher, Resolver, Retriever
from tracemem.ops import InvalidOperation, OpLog
from tracemem.resolver import FatalModelError, ResolverConfigError, ResolverError, ResolverInputError
from tracemem.schema import Answer, Candidate, Operation, ScenarioMeta, SystemQuestion, Turn, Usage


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
        self._resolver_events: list[dict] = []

    # -- write path ----------------------------------------------------------------

    def observe(self, turn: Turn, when: datetime, gold_candidates: list[Candidate] | None = None) -> None:
        self.turns[turn.id] = turn
        self.log.observe_turn(turn.id, when, turn.speaker)
        candidates = gold_candidates if gold_candidates is not None else self.extractor.extract(turn, when, self.meta)
        for candidate in candidates:
            self._candidates.append(candidate)
            related = self.matcher.match(candidate, self.log)
            before = self.resolver_usage()
            try:
                op = self.resolver.resolve(candidate, related)
            except ResolverError as error:
                self._record_resolution(candidate, turn.id, before, "generation_failed", error=error)
                continue
            except (ResolverInputError, ResolverConfigError, FatalModelError) as error:
                self._record_resolution(candidate, turn.id, before, "aborted", error=error)
                raise
            try:
                self.log.apply(op)
            except InvalidOperation as error:
                # A rejected operation changes nothing; it is kept for the resolver metrics.
                self._rejected.append((op, str(error)))
                self._record_resolution(candidate, turn.id, before, "rejected", op, error)
            else:
                self._record_resolution(candidate, turn.id, before, "applied", op)

    def _record_resolution(self, candidate: Candidate, turn_id: str, before: Usage | None,
                           status: str, op: Operation | None = None, error: Exception | None = None) -> None:
        after = self.resolver_usage()
        usage = None
        if before is not None and after is not None:
            usage = {key: getattr(after, key) - getattr(before, key)
                     for key in ("calls", "input_tokens", "output_tokens")}
            if any(value < 0 for value in usage.values()):
                raise ValueError("resolver usage counters must not decrease within a scenario")
        attempts = usage["calls"] if usage is not None else getattr(error, "attempts", None)
        self._resolver_events.append({
            "candidate_id": candidate.candidate_id, "turn_id": turn_id, "item": candidate.item,
            "status": status, "operation_id": op.op_id if op else None,
            "attempts": attempts, "usage": usage,
            "error_type": type(error).__name__ if error else None,
            "error_detail": error.detail if isinstance(error, ResolverError) else str(error) if error else None,
        })

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

    def resolver_events(self) -> list[dict]:
        """Candidate outcomes, including failures without an Operation; safe to mutate a snapshot."""
        model_backed = callable(getattr(self.resolver, "usage", None)) or callable(getattr(self.resolver, "describe", None))
        if not model_backed and not any(event["error_type"] for event in self._resolver_events):
            return []  # retain the successful gold pipeline's existing artifact set
        return deepcopy(self._resolver_events)

    def resolver_usage(self) -> Usage | None:
        """Resolver write-path usage only. Missing instrumentation is unknown, not zero."""
        method = getattr(self.resolver, "usage", None)
        if not callable(method):
            return None
        usage = method()
        if not isinstance(usage, Usage):
            raise TypeError("resolver.usage() must return Usage")
        return usage

    def describe(self) -> dict:
        config = {
            "extractor": type(self.extractor).__name__,
            "matcher": type(self.matcher).__name__,
            "resolver": type(self.resolver).__name__,
            "retriever": type(self.retriever).__name__,
            "answerer": type(self.answerer).__name__,
            "budget_tokens": self.budget_tokens,
        }
        describe = getattr(self.resolver, "describe", None)
        if callable(describe):
            config["resolver_config"] = describe()
        return config
