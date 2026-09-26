"""Every type that crosses a component boundary.

Components exchange only these types. A change here is a contract change: it
needs approval from every owner who consumes the changed type, with fixtures
and tests updated in the same pull request (docs/working-agreement.md, section 2).

All models forbid unknown fields, so a misspelt field is an error instead of a
silently ignored value, and all models are immutable once built.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, time, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Vocabularies
# ---------------------------------------------------------------------------

Act = Literal[
    "decide",  # first confirmed choice for an item with no active value
    "revise",  # settled replacement of the active value
    "restate",  # reaffirms the active value
    "suggest",  # proposes a value without confirming it
    "accept",  # confirms an earlier suggestion (names it in `accepts`)
    "contest",  # asserts a different current value without settling it
    "mention",  # names a value without proposing it: a recollection, counterfactual or report
    "task_open",  # creates a task
    "task_progress",  # changes a task's progress
]
# Which acts each kind of item allows. On a task item, `value` (or `progress`
# for task_progress) must be one of PROGRESS_VALUES.
ACTS_BY_KIND: dict[str, frozenset[str]] = {
    "decision": frozenset({"decide", "revise", "restate", "suggest", "accept", "contest", "mention"}),
    "task": frozenset({"task_open", "task_progress", "restate", "suggest", "accept", "contest", "mention"}),
}

Progress = Literal["open", "blocked", "completed", "cancelled"]
PROGRESS_VALUES: tuple[str, ...] = ("open", "blocked", "completed", "cancelled")
# Everyday words that count as each progress value when scoring answers about tasks.
PROGRESS_ALIASES: dict[str, list[str]] = {
    "open": ["in progress", "ongoing", "started", "reopened", "not started", "to do", "todo"],
    "blocked": ["stuck", "on hold", "waiting"],
    "completed": ["done", "finished", "complete"],
    "cancelled": ["canceled", "dropped", "abandoned"],
}

QuestionKind = Literal["current", "previous", "as_of"]

Category = Literal[
    "suggestion_after_decision",  # newer-record trap: a suggestion follows the decision
    "unresolved_contradiction",  # newer-record trap: a second speaker disputes the decision
    "confusable_items",  # similar-item trap: a same-kind item is decided later
    "mention_after_decision",  # newer-mention trap: questions, recollections, counterfactuals
    "task_lifecycle",  # tasks change progress; may host any trap
    "explicit_revision",  # control: "X instead of Y"
    "implicit_revision",  # control: the change is stated without replacement words
    "accepted_suggestion",  # control: a suggestion accepted later, possibly sessions later
]
# Categories in which recency is expected to be right; they need no trap question.
CONTROL_CATEGORIES = frozenset({"explicit_revision", "implicit_revision", "accepted_suggestion"})

OpName = Literal["ADD", "KEEP", "SUPERSEDE", "FLAG"]
RecordStatus = Literal["active", "proposed", "contested", "superseded", "declined"]
AnswerStatus = Literal["answer", "none", "conflict", "abstain"]
ExpectedStatus = Literal["answer", "none", "conflict"]

ITEM_KEY = r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$"
SESSION_ID = r"^S[1-9][0-9]*$"
TURN_ID = r"^S[1-9][0-9]*-T[1-9][0-9]*$"


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ---------------------------------------------------------------------------
# Scenario side: written by benchmark authors (docs/benchmark.md)
# ---------------------------------------------------------------------------


class ItemSpec(Contract):
    key: str = Field(pattern=ITEM_KEY, description="stable item key, e.g. model.sentiment")
    kind: Literal["decision", "task"]
    description: str
    ask: str | None = Field(default=None, description="question text for automatic checkpoint questions")
    values: dict[str, list[str]] = Field(
        default_factory=dict, description="canonical value -> aliases; tasks use the progress vocabulary"
    )
    confusable_with: list[str] = Field(default_factory=list)


class Turn(Contract):
    id: str = Field(pattern=TURN_ID)
    speaker: str
    text: str


class Session(Contract):
    id: str = Field(pattern=SESSION_ID)
    date: date
    turns: list[Turn]


class ScriptEvent(Contract):
    turn: str = Field(pattern=TURN_ID)
    act: Act
    item: str
    value: str | None = None
    reason: str | None = None
    accepts: str | None = Field(default=None, pattern=TURN_ID)
    progress: Progress | None = None


class QuestionSpec(Contract):
    id: str
    after: str = Field(pattern=SESSION_ID)
    kind: QuestionKind
    item: str
    text: str
    session: str | None = Field(default=None, pattern=SESSION_ID)


class ReviewInfo(Contract):
    status: Literal["unreviewed", "reviewed", "blind_checked"] = "unreviewed"
    reviewer: str | None = None
    notes: str | None = None


class Scenario(Contract):
    scenario_id: str
    title: str
    category: Category
    split: Literal["dev", "test"]
    author: str
    review: ReviewInfo = Field(default_factory=ReviewInfo)
    project_id: str
    items: list[ItemSpec]
    sessions: list[Session]
    script: list[ScriptEvent]
    questions: list[QuestionSpec] = Field(default_factory=list)
    auto_questions: bool = True

    def item(self, key: str) -> ItemSpec:
        for spec in self.items:
            if spec.key == key:
                return spec
        raise KeyError(key)

    def turns(self) -> list[Turn]:
        return [turn for session in self.sessions for turn in session.turns]

    def meta(self, vocabulary: Vocabulary = "keys") -> ScenarioMeta:
        """What a system may know before the first turn. Never includes values, aliases or trap labels."""
        items = []
        if vocabulary == "keys":
            items = [ItemInfo(key=s.key, kind=s.kind, description=s.description) for s in self.items]
        return ScenarioMeta(scenario_id=self.scenario_id, project_id=self.project_id, items=items, vocabulary=vocabulary)


def session_of(turn_id: str) -> str:
    return turn_id.split("-")[0]


def turn_time(session_date: date, index: int, session_number: int = 1) -> datetime:
    """Synthetic time of the index-th turn (0-based) of session number ``session_number`` (1-based).

    Session n starts at 10:00 plus (n - 1) hours on its date, and each turn adds a
    minute, so turns stay in order even when two sessions share a date (up to 60
    turns per session).
    """
    return datetime.combine(session_date, time(10, 0)) + timedelta(hours=session_number - 1, minutes=index)


# ---------------------------------------------------------------------------
# Pipeline side: exchanged between components (docs/interfaces.md)
# ---------------------------------------------------------------------------


Vocabulary = Literal["keys", "none"]


class ItemInfo(Contract):
    """The part of an item a system may see: its key and a description, never its values."""

    key: str
    kind: Literal["decision", "task"]
    description: str


class ScenarioMeta(Contract):
    """What a system may know about a scenario before it sees any turn.

    ``vocabulary`` records whether the item keys were given ("keys") or withheld
    ("none"). Values, aliases, question templates and confusable-item labels are
    benchmark answers and never reach a system.
    """

    scenario_id: str
    project_id: str
    items: list[ItemInfo] = Field(default_factory=list)
    vocabulary: Vocabulary = "keys"


class Candidate(Contract):
    """A statement worth remembering, produced by extraction and consumed by resolution."""

    candidate_id: str
    project_id: str
    item: str
    value: str
    source_turn_ids: list[str] = Field(min_length=1)
    speaker: str = Field(description="who made the statement")
    text: str = Field(description="the source turn text, quoted")


class Operation(Contract):
    """One memory operation, produced by resolution and applied by storage."""

    op_id: str
    op: OpName
    turn_id: str = Field(pattern=TURN_ID, description="the turn being observed when the operation was issued")
    item: str
    value: str | None = None
    add_as: Literal["active", "proposed"] | None = Field(default=None, description="ADD only")
    targets: list[str] = Field(default_factory=list, description="record ids the operation acts on")
    source_turn_ids: list[str] = Field(min_length=1)
    reason: str | None = None
    rationale: str = ""
    candidate_id: str | None = None


class Record(Contract):
    """One stored memory.

    In TraceMem's store the status is derived from the operation log, never set
    directly. Systems without a resolver keep one record per candidate with
    ``status=None`` (ops.flat_records), so every record-based system reads the
    same records and differs only in status and filtering.
    """

    record_id: str
    project_id: str
    item: str
    value: str
    status: RecordStatus | None
    source_turn_ids: list[str]
    speakers: list[str] = Field(default_factory=list)
    created_turn: str
    created_at: datetime
    supersedes: list[str] = Field(default_factory=list)
    reason: str | None = None


class Question(Contract):
    """A checkpoint question as the benchmark knows it, including its gold item. Scorer-side only."""

    question_id: str
    scenario_id: str
    after: str
    kind: QuestionKind
    item: str
    text: str
    session: str | None = None

    def for_system(self, salt: str = "") -> SystemQuestion:
        return SystemQuestion(
            question_id=public_question_id(self.scenario_id, self.question_id, salt),
            scenario_id=self.scenario_id,
            kind=self.kind,
            text=self.text,
            session=self.session,
        )


class SystemQuestion(Contract):
    """The question a system receives: the text and kind, but not the item it is about.

    The id is opaque so that it cannot reveal the item either. ``kind`` and
    ``session`` are given identically to every system.
    """

    question_id: str
    scenario_id: str
    kind: QuestionKind
    text: str
    session: str | None = None


def public_question_id(scenario_id: str, question_id: str, salt: str = "") -> str:
    """An id a system cannot map back to the item: keyed by a secret the harness keeps from systems."""
    return "q-" + hashlib.sha256(f"{salt}/{scenario_id}/{question_id}".encode()).hexdigest()[:12]


class Usage(Contract):
    """Model usage behind one answer or one observed turn, for cost reporting."""

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


class Answer(Contract):
    """A system's structured answer. `value` is the value the system asserts for the question asked."""

    status: AnswerStatus
    value: str | None = None
    cited_turn_ids: list[str] = Field(default_factory=list)
    context_turn_ids: list[str] = Field(default_factory=list, description="turns behind everything the answer model saw")
    text: str = ""
    usage: Usage | None = None

    @model_validator(mode="after")
    def _value_iff_answer(self) -> Answer:
        if (self.status == "answer") != (self.value is not None):
            raise ValueError("an Answer carries a value exactly when its status is 'answer'")
        return self


class ExpectedAnswer(Contract):
    """The gold answer to one question, computed by replaying the scenario's script."""

    question_id: str
    scenario_id: str
    kind: QuestionKind
    item: str
    after: str
    expected_status: ExpectedStatus
    expected_value: str | None = None
    # Every value set below holds normalised forms: each canonical value plus its aliases.
    accepted_values: list[str] = Field(default_factory=list)
    stale_values: list[str] = Field(default_factory=list)
    unconfirmed_values: list[str] = Field(default_factory=list)
    confusable_values: list[str] = Field(default_factory=list)
    current_values: list[str] = Field(
        default_factory=list, description="historical questions only: forms of the value current at the checkpoint"
    )
    required_support: list[str] = Field(default_factory=list)
    additional_support: list[str] = Field(default_factory=list)
    trap_candidate: bool = False
    trap_mention: bool = False
    trap_confusable: bool = False
    episode: str = Field(default="", description="item plus the index of its gold state; repeated checkpoints share it")


def normalise(text: str | None) -> str:
    """Lowercase, trim, collapse whitespace, and strip surrounding punctuation."""
    if text is None:
        return ""
    collapsed = " ".join(text.lower().split())
    return collapsed.strip(" .,;:!?'\"()[]{}")
