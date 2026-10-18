"""Probes never look ahead: cutting a scenario after session k does not change any answer given by then.

A probe reads gold labels, so it could in principle peek at turns it has not
been shown yet. If it did, its answers at session k would change when the
sessions after k are removed. Every registered system (the probes and the
gold-stand-in pipeline) is checked on every pilot and every cut point.
"""

from __future__ import annotations

import json

import pytest

from support import PILOT_IDS, pilot
from tracemem.eval.harness import run_scenario
from tracemem.resolver import LLMResolver, ModelReply, ResolverConfig
from tracemem.schema import Scenario
from tracemem.systems import REGISTRY


class VisibleStateClient:
    """Deterministic completions based only on the candidate and matched records.

    This deliberately simple policy makes the first value active, confirms equal
    values, and supersedes different ones. It tests temporal isolation through the
    real Resolver without reading gold operations or claiming semantic accuracy.
    """

    def __init__(self):
        self.calls = 0

    def complete(self, *, config, messages, response_format):
        self.calls += 1
        evidence = json.loads(messages[1]["content"])
        candidate = evidence["candidate"]
        active = next((r for r in evidence["related"] if r["status"] == "active"), None)
        op = "ADD" if active is None else "KEEP" if active["value"] == candidate["value"] else "SUPERSEDE"
        return ModelReply(content=json.dumps({
            "op": op, "add_as": "active" if op == "ADD" else None,
            "targets": [] if active is None else [active["record_id"]],
            "source_turn_ids": candidate["source_turn_ids"], "reason": None,
            "rationale": "Offline temporal-isolation policy using only currently visible state.",
        }))


@pytest.fixture
def offline_resolver(monkeypatch):
    """Keep the registered real pipeline runnable with no credentials or network."""
    clients = []

    def from_env(cls):
        client = VisibleStateClient()
        clients.append(client)
        return cls(ResolverConfig(model="offline-model"), client)

    def forbid_provider(*args, **kwargs):
        pytest.fail("Temporal-isolation tests must not construct a live provider client")

    monkeypatch.setattr(LLMResolver, "from_env", classmethod(from_env))
    monkeypatch.setattr("tracemem.resolver.OpenAICompletionClient", forbid_provider)
    return clients


def truncate(scenario: Scenario, k: int) -> Scenario:
    """The scenario as it would look if it ended after its k-th session."""
    data = scenario.model_dump()
    data["sessions"] = data["sessions"][:k]
    sessions = {s["id"] for s in data["sessions"]}
    turns = {t["id"] for s in data["sessions"] for t in s["turns"]}
    data["script"] = [e for e in data["script"] if e["turn"] in turns]
    data["questions"] = [q for q in data["questions"]
                         if q["after"] in sessions and (q["session"] is None or q["session"] in sessions)]
    return Scenario.model_validate(data)


def answers(spec, scenario: Scenario) -> dict:
    rows, _ = run_scenario(spec, scenario)
    return {r.question.question_id: (r.question.after, r.answer) for r in rows}


def test_truncate_keeps_only_the_first_sessions():
    cut = truncate(pilot("pilot-01"), 2)
    assert [s.id for s in cut.sessions] == ["S1", "S2"]
    assert {e.turn.split("-")[0] for e in cut.script} == {"S1", "S2"}
    assert cut.questions == []  # both explicit questions are asked after S3 or S4


@pytest.mark.parametrize("name", list(REGISTRY))
@pytest.mark.parametrize("scenario_id", PILOT_IDS)
def test_answers_do_not_depend_on_later_sessions(scenario_id, name, offline_resolver):
    spec = REGISTRY[name]
    full_scenario = pilot(scenario_id)
    full = answers(spec, full_scenario)
    for k in range(1, len(full_scenario.sessions)):
        kept = {s.id for s in full_scenario.sessions[:k]}
        cut = answers(spec, truncate(full_scenario, k))
        expected_ids = {qid for qid, (after, _) in full.items() if after in kept}
        assert set(cut) == expected_ids, f"cut after S{k}"
        for qid in expected_ids:
            assert cut[qid][1] == full[qid][1], f"{name} changed its answer to {qid} when cut after S{k}"
    if name == "pipeline-resolver-dev":
        assert len(offline_resolver) == len(full_scenario.sessions)
        assert all(client.calls > 0 for client in offline_resolver)
