"""Offline accounting and compatibility regressions for controlled comparisons."""

from __future__ import annotations

import json

import pytest

from support import minimal_dict, scored
from tracemem.eval import harness
from tracemem.eval.report import comparison_table
from tracemem.resolver import (
    FatalModelError, LLMResolver, ModelReply, ResolverConfig, RetryableModelError,
)
from tracemem.schema import Answer, Scenario, SystemQuestion, Usage
from tracemem.systems import comparison
from tracemem.systems.base import SystemSpec


CONFIG = ResolverConfig(model="offline-comparison", max_attempts=2)


def answer_reply(*, input_tokens=4, output_tokens=2):
    return ModelReply(json.dumps({"status": "abstain", "value": None, "cited_turn_ids": [], "text": ""}),
                      input_tokens=input_tokens, output_tokens=output_tokens)


class ScriptedClient:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = 0

    def complete(self, **kwargs):
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class ComparisonClient:
    """Resolve only visible state; optionally fail while answering the second question."""

    def __init__(self, fail_answers=False):
        self.fail_answers = fail_answers
        self.answer_calls = 0
        self.write_calls = 0

    def complete(self, *, config, messages, response_format):
        if response_format["json_schema"]["name"] == "memory_answer":
            self.answer_calls += 1
            if self.fail_answers and self.answer_calls == 2:
                return ModelReply("broken JSON", input_tokens=7, output_tokens=3)
            if self.fail_answers and self.answer_calls == 3:
                raise FatalModelError("offline fatal provider error")
            return answer_reply()
        self.write_calls += 1
        evidence = json.loads(messages[1]["content"])
        candidate = evidence["candidate"]
        active = next((record for record in evidence["related"] if record["status"] == "active"), None)
        op = "ADD" if active is None else "KEEP" if active["value"] == candidate["value"] else "SUPERSEDE"
        return ModelReply(json.dumps({
            "op": op, "add_as": "active" if op == "ADD" else None,
            "targets": [] if active is None else [active["record_id"]],
            "source_turn_ids": candidate["source_turn_ids"], "reason": None,
            "rationale": "Synthetic visible-state operation.",
        }), input_tokens=5, output_tokens=2)


def question():
    return SystemQuestion(question_id="opaque", scenario_id="synthetic", kind="current", text="What is settled?")


def system_spec(name, client):
    return SystemSpec(name, lambda meta, gold: comparison.make_system(name, meta, config=CONFIG, client=client),
                      False, "offline controlled test")


@pytest.fixture(autouse=True)
def no_git_metadata(monkeypatch):
    monkeypatch.setattr(harness, "_git", lambda *args: None)


def test_answer_usage_counts_successful_retries_once_per_question_and_cumulatively():
    client = ScriptedClient(ModelReply("broken", input_tokens=7, output_tokens=3),
                            answer_reply(), answer_reply(input_tokens=6, output_tokens=1))
    answerer = comparison.SharedAnswerer(CONFIG, client)
    first = answerer.answer(question(), [], {})
    first_total = answerer.usage()
    second = answerer.answer(question(), [], {})
    assert first.usage == Usage(calls=2, input_tokens=11, output_tokens=5)
    assert second.usage == Usage(calls=1, input_tokens=6, output_tokens=1)
    assert first_total == first.usage
    assert answerer.usage() == Usage(calls=3, input_tokens=17, output_tokens=6)
    assert client.calls == 3


def test_answer_usage_survives_fatal_error_after_a_billable_invalid_completion():
    client = ScriptedClient(ModelReply("broken", input_tokens=7, output_tokens=3),
                            FatalModelError("offline provider rejection"))
    answerer = comparison.SharedAnswerer(CONFIG, client)
    with pytest.raises(FatalModelError):
        answerer.answer(question(), [], {})
    assert answerer.usage() == Usage(calls=2, input_tokens=7, output_tokens=3)
    assert client.calls == 2


def test_exhausted_transient_answer_calls_are_retained_without_inventing_tokens():
    client = ScriptedClient(TimeoutError(), RetryableModelError("offline retryable error"))
    answerer = comparison.SharedAnswerer(CONFIG, client)
    answer = answerer.answer(question(), [], {})
    assert answer.status == "abstain"
    assert answer.usage == answerer.usage() == Usage(calls=2)


@pytest.mark.parametrize("name", ["tracemem-controlled", "tracemem-no-versions"])
def test_failed_run_saves_all_answer_attempts_without_double_counting_completed_rows(name, tmp_path):
    client = ComparisonClient(fail_answers=True)
    scenario = Scenario.model_validate(minimal_dict())
    with pytest.raises(harness.RunAborted) as caught:
        harness.run(system_spec(name, client), [scenario], "dev", condition="gold_candidates")
    result = caught.value.result
    assert result.status == "failed"
    assert result.failure["error_type"] == "FatalModelError"
    assert len(result.rows) == 1
    assert result.rows[0].answer.usage == Usage(calls=1, input_tokens=4, output_tokens=2)
    expected = Usage(calls=3, input_tokens=11, output_tokens=5)
    assert result.answer_usage == {scenario.scenario_id: expected}
    folder = harness.write_run(result, tmp_path)
    saved = json.loads((folder / "usage.json").read_text(encoding="utf-8"))
    assert saved["answer"]["total"] == expected.model_dump()
    assert saved["answer"]["by_scenario"] == {scenario.scenario_id: expected.model_dump()}
    assert saved["resolver"]["total"]["calls"] + saved["answer"]["total"]["calls"] == (
        client.write_calls + client.answer_calls)


def test_usage_file_prefers_hook_per_scenario_and_falls_back_to_completed_rows_elsewhere(tmp_path):
    rows = [
        scored(scenario="hooked", answer=Answer(status="abstain", usage=Usage(calls=1, input_tokens=4, output_tokens=2))),
        scored(scenario="legacy", answer=Answer(status="abstain", usage=Usage(calls=2, input_tokens=10, output_tokens=3))),
        scored(scenario="legacy", question_id="second",
               answer=Answer(status="abstain", usage=Usage(calls=1, input_tokens=5, output_tokens=2))),
    ]
    result = harness.RunResult(system="answer-usage-test", uses_gold=False, split="dev", condition="gold_candidates",
                               rows=rows, answer_usage={"hooked": Usage(calls=3, input_tokens=20, output_tokens=8)})
    folder = harness.write_run(result, tmp_path)
    saved = json.loads((folder / "usage.json").read_text(encoding="utf-8"))
    assert "resolver" not in saved
    assert saved["answer"]["by_scenario"] == {
        "hooked": {"calls": 3, "input_tokens": 20, "output_tokens": 8},
        "legacy": {"calls": 3, "input_tokens": 15, "output_tokens": 5},
    }
    assert saved["answer"]["total"] == {"calls": 6, "input_tokens": 35, "output_tokens": 13}


def test_reference_prompt_and_schema_metadata_do_not_call_the_client():
    client = ScriptedClient()
    reference = LLMResolver(CONFIG, client).describe()
    settings = comparison.comparison_settings(CONFIG, 12000, client)
    assert settings["resolver_reference_prompt_hash"] == reference["prompt_hash"]
    assert settings["resolver_reference_schema_hash"] == reference["output_schema_hash"]
    assert client.calls == 0


@pytest.mark.parametrize("changed_field", ["prompt_hash", "output_schema_hash"])
@pytest.mark.parametrize("allow_mixed", [False, True])
def test_comparison_rejects_ablation_runs_with_different_resolver_reference(changed_field, allow_mixed,
                                                                          monkeypatch, tmp_path):
    scenario = Scenario.model_validate(minimal_dict())
    first = harness.run(system_spec("tracemem-controlled", ComparisonClient()), [scenario],
                        "dev", condition="gold_candidates")
    original = LLMResolver.describe

    def changed_description(self):
        return {**original(self), changed_field: "different-reference-version"}

    monkeypatch.setattr(LLMResolver, "describe", changed_description)
    second = harness.run(system_spec("tracemem-no-versions", ComparisonClient()), [scenario],
                         "dev", condition="gold_candidates")
    folders = [harness.write_run(result, tmp_path) for result in (first, second)]
    with pytest.raises(ValueError, match="comparison|differ"):
        comparison_table(folders, n=10, allow_mixed=allow_mixed)


def test_resolver_reference_changes_within_a_run_are_rejected(monkeypatch):
    original = LLMResolver.describe
    clients = []

    def factory(meta, gold):
        if clients:
            monkeypatch.setattr(LLMResolver, "describe", lambda self: {
                **original(self), "prompt_hash": "changed-between-scenarios",
            })
        client = ComparisonClient()
        clients.append(client)
        return comparison.make_system("tracemem-controlled", meta, config=CONFIG, client=client)

    first = Scenario.model_validate(minimal_dict())
    second = first.model_copy(update={"scenario_id": "another-synthetic-scenario"})
    spec = SystemSpec("tracemem-controlled", factory, False, "offline controlled test")
    with pytest.raises(ValueError, match="configuration changed"):
        harness.run(spec, [first, second], "dev", condition="gold_candidates")
