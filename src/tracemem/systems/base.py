"""The interface every compared system implements (docs/interfaces.md, "Systems")."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Protocol, runtime_checkable

from tracemem.schema import Answer, Candidate, Operation, ScenarioMeta, SystemQuestion, Turn

if TYPE_CHECKING:
    from tracemem.bench.replay import GoldTimeline


@runtime_checkable
class MemorySystem(Protocol):
    """A system sees turns one at a time, in order, and answers questions between sessions.

    ``observe`` receives ``gold_candidates`` only in the gold-candidate condition,
    and only if the system sets ``accepts_gold_candidates``. ``answer`` must not
    change what the system remembers; the harness checks this with
    ``fingerprint`` when a system provides one.
    """

    name: str

    def observe(self, turn: Turn, when: datetime, gold_candidates: list[Candidate] | None = None) -> None: ...

    def answer(self, question: SystemQuestion) -> Answer: ...


# Optional methods a system may also provide:
#   fingerprint() -> str             changes whenever memory changes
#   operations() -> list[Operation]  applied operations, for resolver metrics
#   rejected_operations() -> list    (operation, reason) pairs the store refused
#   candidates() -> list[Candidate]  for extraction metrics
#   describe() -> dict               configuration, model ids, prompt hashes; written to the manifest
#   accepts_gold_candidates: bool    the system can run in the gold-candidate condition


SystemFactory = Callable[[ScenarioMeta, "GoldTimeline | None"], MemorySystem]


@dataclass(frozen=True)
class SystemSpec:
    """A registered system.

    ``uses_gold`` marks systems built with the scenario's gold labels: the
    probes and the gold-mock pipeline. They exist to test the benchmark and the
    scorer, and every report labels them as such; they are never baselines.
    """

    name: str
    factory: SystemFactory
    uses_gold: bool
    description: str


def optional_operations(system: MemorySystem) -> list[Operation] | None:
    method = getattr(system, "operations", None)
    return method() if callable(method) else None


def optional_candidates(system: MemorySystem) -> list[Candidate] | None:
    method = getattr(system, "candidates", None)
    return method() if callable(method) else None


def optional_rejected(system: MemorySystem) -> list | None:
    method = getattr(system, "rejected_operations", None)
    return method() if callable(method) else None


def optional_fingerprint(system: MemorySystem) -> str | None:
    method = getattr(system, "fingerprint", None)
    return method() if callable(method) else None
