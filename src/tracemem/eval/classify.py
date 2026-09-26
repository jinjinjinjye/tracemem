"""Put each answer into exactly one outcome class (docs/metrics.md, "Outcome classes").

The classes, not the raw values, feed every rate. Each error class names a
different failure, so that a reader can tell a system that forgets (missed)
from one that is over-cautious (false_conflict) or one that trusts an old or
unconfirmed statement (stale, unconfirmed_as_current).
"""

from __future__ import annotations

from typing import Literal

from tracemem.schema import Answer, ExpectedAnswer, normalise

Outcome = Literal[
    "correct",
    "stale",  # gave a value that was replaced
    "unconfirmed_as_current",  # gave a suggestion, a disputed claim, or a declined claim as settled
    "confusable_as_current",  # gave another item's value
    "current_as_historical",  # asked about the past, gave today's value
    "false_certainty",  # the team disagrees, the system picked a side
    "false_conflict",  # the matter is settled (or undecided), the system reported a conflict
    "missed",  # something is settled or disputed, the system said nothing is
    "abstained",  # the system declined to answer
    "wrong_other",  # any other value
]
OUTCOMES: tuple[str, ...] = (
    "correct",
    "stale",
    "unconfirmed_as_current",
    "confusable_as_current",
    "current_as_historical",
    "false_certainty",
    "false_conflict",
    "missed",
    "abstained",
    "wrong_other",
)


def _value_class(value: str, expected: ExpectedAnswer) -> Outcome:
    """Classify a given value. The order of the checks is the precedence rule."""
    if value in expected.accepted_values:
        return "correct"
    if value in expected.stale_values:
        return "stale"
    if value in expected.unconfirmed_values:
        return "unconfirmed_as_current"
    if value in expected.confusable_values:
        return "confusable_as_current"
    if value in expected.current_values:
        return "current_as_historical"
    return "wrong_other"


def classify(answer: Answer, expected: ExpectedAnswer) -> Outcome:
    if answer.status == "abstain":
        return "abstained"
    gold = expected.expected_status

    if gold == "conflict":
        if answer.status == "conflict":
            return "correct"
        return "false_certainty" if answer.status == "answer" else "missed"

    if answer.status == "conflict":
        return "false_conflict"

    if gold == "none":
        if answer.status == "none":
            return "correct"
        outcome = _value_class(normalise(answer.value), expected)
        return "wrong_other" if outcome == "correct" else outcome

    # The gold is a settled value.
    if answer.status == "none":
        return "missed"
    return _value_class(normalise(answer.value), expected)
