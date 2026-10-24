"""Offline checks of the local and OpenRouter clients and the reply cache.

As in test_resolver_client.py, a fake module exposes only the SDK surface the
adapter consumes, so no key, network, model server or SDK is required. The cache
tests use a scripted inner client and a temporary cache folder; the wiring tests
also run the minimal scenario offline through the harness and the report.
"""

from __future__ import annotations

import json
import sys
import traceback
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from support import minimal_dict
from tracemem import model_client
from tracemem.eval import harness
from tracemem.eval.report import comparison_table
from tracemem.model_client import (
    CachedClient,
    OpenAICompatibleClient,
    SpendingCapError,
    from_env,
    local_client,
    openrouter_client,
    read_dotenv,
)
from tracemem.resolver import (
    FatalModelError,
    ModelReply,
    OpenAICompletionClient,
    ResolverConfig,
    ResolverConfigError,
    RetryableModelError,
)
from tracemem.schema import Scenario, SystemQuestion
from tracemem.systems import comparison
from tracemem.systems.base import SystemSpec

MESSAGES = [{"role": "user", "content": "synthetic evidence"}]
FORMAT = {"type": "json_schema", "json_schema": {"name": "test"}}
CONFIG = ResolverConfig(model="test-model", timeout_seconds=4.5, max_completion_tokens=73)
SETTINGS = ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "TRACEMEM_PROVIDER", "TRACEMEM_LOCAL_BASE_URL",
            "TRACEMEM_LOCAL_THINKING", "TRACEMEM_LOCAL_API_KEY", "TRACEMEM_CACHE", "TRACEMEM_CACHE_DIR",
            "TRACEMEM_BUDGET_USD")


def completion(*, content='{"op": "ADD"}', finish_reason="stop", cost=None, refusal=None, usage=True):
    usage = SimpleNamespace(prompt_tokens=17, completion_tokens=9) if usage else None
    if cost is not None:
        usage.cost = cost
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content, refusal=refusal),
                                 finish_reason=finish_reason)],
        usage=usage,
    )


@pytest.fixture
def sdk(monkeypatch, tmp_path):
    """Replace the entire SDK, and run where no .env or cache folder exists."""
    module = ModuleType("openai")

    class APIConnectionError(Exception):
        pass

    class APITimeoutError(APIConnectionError):
        pass

    class APIStatusError(Exception):
        def __init__(self, status_code, message):
            self.status_code = status_code
            super().__init__(message)

    module.APIConnectionError = APIConnectionError
    module.APITimeoutError = APITimeoutError
    module.APIStatusError = APIStatusError
    module.create = Mock(return_value=completion())
    module.OpenAI = Mock(return_value=SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=module.create)),
    ))
    monkeypatch.setitem(sys.modules, "openai", module)
    for name in SETTINGS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    return module


def request(client, config=CONFIG, messages=MESSAGES, response_format=FORMAT):
    return client.complete(config=config, messages=messages, response_format=response_format)


class ScriptedClient:
    """An inner client that returns scripted replies and reports a scripted cost."""

    def __init__(self, *actions, cost=None, label="scripted"):
        self.actions = list(actions)
        self.cost = cost
        self.label = label
        self.calls = []
        self.last_cost = None

    def describe(self):
        return {"label": self.label}

    def complete(self, *, config, messages, response_format):
        self.calls.append(messages)
        self.last_cost = None
        action = self.actions.pop(0) if self.actions else ModelReply(
            '{"op": "ADD"}', input_tokens=1000, output_tokens=200)
        if isinstance(action, Exception):
            raise action
        self.last_cost = self.cost
        return action


def log_entries(folder):
    path = folder / "calls.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def saved_replies(folder):
    return sorted(folder.rglob("*/*.json"))


# Provider settings


def test_local_client_targets_ollama_with_thinking_off_and_max_tokens(sdk):
    client = local_client({})
    sdk.OpenAI.assert_called_once_with(api_key="local", base_url="http://127.0.0.1:11434/v1",
                                       max_retries=0, default_headers=None)
    reply = request(client)
    sdk.create.assert_called_once_with(
        model="test-model", messages=MESSAGES, response_format=FORMAT, timeout=4.5,
        max_tokens=73, extra_body={"reasoning_effort": "none"},
    )
    assert reply == ModelReply(content='{"op": "ADD"}', input_tokens=17, output_tokens=9)
    assert client.last_cost is None


def test_local_client_reads_base_url_and_thinking_switch(sdk):
    client = local_client({"TRACEMEM_LOCAL_BASE_URL": "http://192.0.2.10:8080/v1",
                           "TRACEMEM_LOCAL_THINKING": "ON"})
    assert sdk.OpenAI.call_args.kwargs["base_url"] == "http://192.0.2.10:8080/v1"
    request(client)
    assert "extra_body" not in sdk.create.call_args.kwargs
    assert "max_completion_tokens" not in sdk.create.call_args.kwargs


@pytest.mark.parametrize("value", ["yes", "true", ""])
def test_local_client_rejects_a_thinking_switch_other_than_on_or_off(sdk, value):
    with pytest.raises(ResolverConfigError, match="TRACEMEM_LOCAL_THINKING"):
        local_client({"TRACEMEM_LOCAL_THINKING": value})
    sdk.OpenAI.assert_not_called()


def test_openrouter_client_requires_every_parameter_and_uses_max_completion_tokens(sdk):
    client = openrouter_client({"OPENROUTER_API_KEY": "synthetic-router-key"})
    sdk.OpenAI.assert_called_once_with(api_key="synthetic-router-key", base_url="https://openrouter.ai/api/v1",
                                       max_retries=0, default_headers={"X-Title": "TraceMem"})
    request(client, config=ResolverConfig(model="test-model", timeout_seconds=4.5,
                                          max_completion_tokens=73, temperature=0.0))
    sdk.create.assert_called_once_with(
        model="test-model", messages=MESSAGES, response_format=FORMAT, timeout=4.5,
        max_completion_tokens=73, temperature=0.0, extra_body={"provider": {"require_parameters": True}},
    )
    assert "synthetic-router-key" not in json.dumps(client.describe())


def test_openrouter_key_comes_from_dotenv_only_when_absent_from_the_environment(sdk, tmp_path):
    dotenv = tmp_path / "private.env"
    dotenv.write_text('OPENROUTER_API_KEY="synthetic-file-key"\n', encoding="utf-8")
    openrouter_client({}, dotenv_path=dotenv)
    assert sdk.OpenAI.call_args.kwargs["api_key"] == "synthetic-file-key"
    openrouter_client({"OPENROUTER_API_KEY": "synthetic-environment-key"}, dotenv_path=dotenv)
    assert sdk.OpenAI.call_args.kwargs["api_key"] == "synthetic-environment-key"
    openrouter_client({"OPENROUTER_API_KEY": "  "}, dotenv_path=dotenv)
    assert sdk.OpenAI.call_args.kwargs["api_key"] == "synthetic-file-key"


def test_openrouter_without_a_key_fails_before_creating_the_sdk_client(sdk, tmp_path):
    with pytest.raises(ResolverConfigError, match="OPENROUTER_API_KEY"):
        openrouter_client({}, dotenv_path=tmp_path / "absent.env")
    sdk.OpenAI.assert_not_called()


def test_compatible_client_missing_sdk_has_actionable_optional_dependency_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "openai", None)
    with pytest.raises(ResolverConfigError, match=r"\[llm\]"):
        local_client({})


def test_compatible_client_keeps_a_cost_the_provider_reports(sdk):
    sdk.create.return_value = completion(cost=0.0021)
    client = openrouter_client({"OPENROUTER_API_KEY": "synthetic-router-key"})
    request(client)
    assert client.last_cost == pytest.approx(0.0021)
    sdk.create.return_value = completion()
    request(client)
    assert client.last_cost is None


@pytest.mark.parametrize(("choice", "expected"), [
    ({"finish_reason": "length"}, ModelReply('{"op": "ADD"}', 17, 9, finish_reason="length")),
    ({"refusal": "synthetic refusal"}, ModelReply('{"op": "ADD"}', 17, 9, refused=True)),
])
def test_compatible_client_reports_cut_off_and_refused_replies_and_the_cache_saves_neither(sdk, tmp_path,
                                                                                          choice, expected):
    sdk.create.return_value = completion(**choice)
    assert request(CachedClient(local_client({}), tmp_path)) == expected
    assert saved_replies(tmp_path) == []
    # A later run asks the provider again instead of replaying the incomplete reply.
    assert request(CachedClient(local_client({}), tmp_path)) == expected
    assert sdk.create.call_count == 2
    assert [entry["cache_hit"] for entry in log_entries(tmp_path)] == [False, False]


def test_compatible_client_without_usage_reports_zero_tokens_and_no_cost(sdk):
    sdk.create.return_value = completion(usage=False)
    client = openrouter_client({"OPENROUTER_API_KEY": "synthetic-router-key"})
    assert request(client) == ModelReply('{"op": "ADD"}', input_tokens=0, output_tokens=0)
    assert client.last_cost is None


def test_local_client_sends_a_local_key_when_one_is_set(sdk):
    local_client({"TRACEMEM_LOCAL_API_KEY": " synthetic-local-key "})
    assert sdk.OpenAI.call_args.kwargs["api_key"] == "synthetic-local-key"


def test_blank_local_address_and_cache_folder_fall_back_to_the_defaults(sdk):
    client = from_env({"TRACEMEM_PROVIDER": "local", "TRACEMEM_LOCAL_BASE_URL": "  ", "TRACEMEM_CACHE_DIR": " "})
    assert client.inner.base_url == "http://127.0.0.1:11434/v1"
    assert sdk.OpenAI.call_args.kwargs["base_url"] == "http://127.0.0.1:11434/v1"
    assert str(client.cache_dir) == "cache/llm"


# Error mapping


@pytest.mark.parametrize("exception_name", ["APIConnectionError", "APITimeoutError"])
def test_connection_and_timeout_errors_are_retryable_and_sanitized(sdk, exception_name):
    sdk.create.side_effect = getattr(sdk, exception_name)("synthetic-private-provider-body")
    with pytest.raises(RetryableModelError, match="connection or timeout") as caught:
        request(local_client({}))
    assert "synthetic-private-provider-body" not in "".join(traceback.format_exception(caught.value))


@pytest.mark.parametrize("status_code", [408, 409, 429, 500, 502, 503])
def test_rate_limits_and_server_errors_are_retryable_and_sanitized(sdk, status_code):
    sdk.create.side_effect = sdk.APIStatusError(status_code, "synthetic-private-provider-body")
    with pytest.raises(RetryableModelError, match=str(status_code)) as caught:
        request(openrouter_client({"OPENROUTER_API_KEY": "synthetic-router-key"}))
    assert "synthetic-private-provider-body" not in "".join(traceback.format_exception(caught.value))


@pytest.mark.parametrize("status_code", [400, 401, 402, 403, 404, 422])
def test_other_client_errors_are_fatal_and_sanitized(sdk, status_code):
    sdk.create.side_effect = sdk.APIStatusError(status_code, "synthetic-private-provider-body")
    with pytest.raises(FatalModelError, match=str(status_code)) as caught:
        request(openrouter_client({"OPENROUTER_API_KEY": "synthetic-router-key"}))
    assert not isinstance(caught.value, RetryableModelError)
    assert "synthetic-private-provider-body" not in "".join(traceback.format_exception(caught.value))


def test_empty_choices_are_retryable(sdk):
    sdk.create.return_value = SimpleNamespace(choices=[], usage=None)
    with pytest.raises(RetryableModelError, match="no completion"):
        request(local_client({}))


# .env parsing


def test_read_dotenv_skips_comments_and_bare_lines_and_strips_quotes_and_export(tmp_path):
    path = tmp_path / "private.env"
    path.write_text("\n".join([
        "FIRST=after the byte-order mark",
        "# a comment line",
        "",
        "export OPENROUTER_API_KEY=\"synthetic-double-quoted\"",
        "SINGLE='single quoted # kept'",
        "PLAIN=plain value # trailing comment",
        "A_BARE_LINE_WITHOUT_AN_EQUALS_SIGN",
        "  SPACED =  spaced value  ",
        "EMPTY=",
        "URL=http://example.invalid/page#fragment",
        "QUOTED_THEN_COMMENT=\"quoted\" # comment",
        "COMMENT_ONLY= # paste your key here",
        "TAB_COMMENT=\t# note",
        "HASH_FIRST=#kept",
        "=value without a key",
    ]) + "\n", encoding="utf-8-sig")
    assert read_dotenv(path) == {
        "FIRST": "after the byte-order mark",
        "OPENROUTER_API_KEY": "synthetic-double-quoted",
        "SINGLE": "single quoted # kept",
        "PLAIN": "plain value",
        "SPACED": "spaced value",
        "EMPTY": "",
        "URL": "http://example.invalid/page#fragment",
        "QUOTED_THEN_COMMENT": "quoted",
        "COMMENT_ONLY": "",
        "TAB_COMMENT": "",
        "HASH_FIRST": "#kept",
    }


def test_read_dotenv_of_a_missing_file_is_empty(tmp_path):
    assert read_dotenv(tmp_path / "absent.env") == {}


def test_read_dotenv_of_an_undecodable_file_is_empty(tmp_path):
    path = tmp_path / "private.env"
    path.write_bytes(b"OPENROUTER_API_KEY=synthetic-\xff-key\n")
    assert read_dotenv(path) == {}


def test_a_key_line_holding_only_a_comment_gives_the_missing_key_error(sdk, tmp_path):
    dotenv = tmp_path / "private.env"
    dotenv.write_text("OPENROUTER_API_KEY= # paste your key here\n", encoding="utf-8")
    with pytest.raises(ResolverConfigError, match="OPENROUTER_API_KEY"):
        openrouter_client({}, dotenv_path=dotenv)
    sdk.OpenAI.assert_not_called()


# Reply cache


def test_cache_hit_returns_the_saved_reply_with_zero_tokens_and_makes_no_call(tmp_path):
    inner = ScriptedClient(ModelReply('{"op": "KEEP"}', input_tokens=1000, output_tokens=200))
    first = request(CachedClient(inner, tmp_path))
    assert first == ModelReply('{"op": "KEEP"}', input_tokens=1000, output_tokens=200)
    # A new instance on the same folder stands for a later run.
    later = CachedClient(inner, tmp_path)
    assert request(later) == ModelReply('{"op": "KEEP"}', input_tokens=0, output_tokens=0)
    assert len(inner.calls) == 1
    assert later.stats == {"calls": 1, "hits": 1, "misses": 0, "cost_usd": 0.0}


def test_cache_key_ignores_timeout_and_attempts_but_not_model_messages_schema_or_client(tmp_path):
    cache = CachedClient(ScriptedClient(), tmp_path)

    def key(config=CONFIG, messages=MESSAGES, response_format=FORMAT, client=cache):
        return client.key(config=config, messages=messages, response_format=response_format)

    base = key()
    assert key(config=CONFIG.model_copy(update={"timeout_seconds": 120.0, "max_attempts": 5})) == base
    assert key(config=CONFIG.model_copy(update={"model": "other-model"})) != base
    assert key(config=CONFIG.model_copy(update={"max_completion_tokens": 74})) != base
    assert key(config=CONFIG.model_copy(update={"temperature": 0.0})) != base
    assert key(messages=[{"role": "user", "content": "other evidence"}]) != base
    assert key(response_format={"type": "json_schema", "json_schema": {"name": "other"}}) != base
    assert key(client=CachedClient(ScriptedClient(label="other-provider"), tmp_path)) != base


def test_a_request_differing_only_in_timeout_or_attempts_is_served_from_the_cache(tmp_path):
    inner = ScriptedClient()
    request(CachedClient(inner, tmp_path))
    later = CachedClient(inner, tmp_path)
    request(later, config=CONFIG.model_copy(update={"timeout_seconds": 180.0, "max_attempts": 3}))
    request(later, config=CONFIG.model_copy(update={"model": "other-model"}))
    assert len(inner.calls) == 2
    assert later.stats["hits"] == 1


@pytest.mark.parametrize("error", [RetryableModelError("transient"), FatalModelError("fatal")])
def test_provider_errors_are_not_cached(tmp_path, error):
    inner = ScriptedClient(error, ModelReply('{"op": "ADD"}'))
    cache = CachedClient(inner, tmp_path)
    with pytest.raises(type(error)):
        request(cache)
    assert saved_replies(tmp_path) == [] and log_entries(tmp_path) == []
    assert request(cache).content == '{"op": "ADD"}'
    assert len(inner.calls) == 2 and len(saved_replies(tmp_path)) == 1


@pytest.mark.parametrize("reply", [ModelReply('{"op":', finish_reason="length"), ModelReply("", refused=True)])
def test_refused_or_cut_off_replies_are_logged_but_not_saved(tmp_path, reply):
    inner = ScriptedClient(reply, reply)
    cache = CachedClient(inner, tmp_path)
    # An identical retry must reach the provider again, as it would without the cache.
    assert request(cache) == reply and request(cache) == reply
    assert len(inner.calls) == 2 and saved_replies(tmp_path) == []
    assert [entry["cache_hit"] for entry in log_entries(tmp_path)] == [False, False]


def test_a_repeat_within_one_client_reaches_the_provider_and_a_later_run_replays_both_in_order(tmp_path):
    inner = ScriptedClient(ModelReply("first reply", 10, 1), ModelReply("second reply", 20, 2))
    run = CachedClient(inner, tmp_path)
    assert [request(run).content for _ in range(2)] == ["first reply", "second reply"]
    assert len(inner.calls) == 2 and len(saved_replies(tmp_path)) == 2
    later = CachedClient(inner, tmp_path)
    assert [request(later) for _ in range(2)] == [ModelReply("first reply"), ModelReply("second reply")]
    assert len(inner.calls) == 2 and later.stats["hits"] == 2


def test_a_retry_that_resends_the_same_feedback_is_not_answered_from_the_cache(tmp_path):
    question = SystemQuestion(question_id="opaque", scenario_id="synthetic", kind="current", text="What is settled?")
    config = ResolverConfig(model="test-model", max_attempts=3)
    valid = json.dumps({"status": "none", "value": None, "cited_turn_ids": [], "text": ""})
    inner = ScriptedClient(ModelReply("not json"), ModelReply("not json"), ModelReply(valid))
    answer = comparison.SharedAnswerer(config, CachedClient(inner, tmp_path)).answer(question, [], {})
    # Attempts 2 and 3 send the same feedback; the third must not replay the second's invalid reply.
    assert inner.calls[1] == inner.calls[2] and len(inner.calls) == 3
    assert answer.status == "none"
    rerun = comparison.SharedAnswerer(config, CachedClient(inner, tmp_path)).answer(question, [], {})
    assert rerun.status == "none" and len(inner.calls) == 3


def test_a_malformed_saved_reply_is_a_miss(tmp_path):
    inner = ScriptedClient()
    cache = CachedClient(inner, tmp_path)
    path = cache._path(cache.key(config=CONFIG, messages=MESSAGES, response_format=FORMAT))
    path.parent.mkdir(parents=True)
    path.write_text('["not", "a", "reply"]', encoding="utf-8")
    assert request(cache).input_tokens == 1000
    assert len(inner.calls) == 1


def test_cost_log_records_misses_with_cost_and_hits_at_zero_cost(tmp_path):
    inner = ScriptedClient(cost=0.004)
    first = CachedClient(inner, tmp_path)
    request(first)
    later = CachedClient(inner, tmp_path)
    request(later)
    miss, hit = log_entries(tmp_path)
    assert miss["key"] == hit["key"] and miss["model"] == hit["model"] == "test-model"
    assert (miss["cache_hit"], miss["cost_usd"], miss["cost_source"]) == (False, 0.004, "provider")
    assert (hit["cache_hit"], hit["cost_usd"], hit["cost_source"]) == (True, 0.0, "cache")
    assert (hit["input_tokens"], hit["output_tokens"]) == (1000, 200)
    assert first.stats == {"calls": 1, "hits": 0, "misses": 1, "cost_usd": 0.004}
    assert later.stats == {"calls": 1, "hits": 1, "misses": 0, "cost_usd": 0.0}


def test_provider_reported_cost_wins_over_the_price_table(tmp_path, monkeypatch):
    monkeypatch.setitem(model_client.PRICES_PER_MILLION, "priced-model", (2.0, 10.0))
    priced = CONFIG.model_copy(update={"model": "priced-model"})
    request(CachedClient(ScriptedClient(cost=0.5), tmp_path / "reported"), config=priced)
    request(CachedClient(ScriptedClient(), tmp_path / "table"), config=priced)
    request(CachedClient(ScriptedClient(), tmp_path / "unpriced"))
    # 1000 input tokens at US$2 and 200 output tokens at US$10 per million.
    assert [(e["cost_usd"], e["cost_source"]) for e in log_entries(tmp_path / "reported")] == [(0.5, "provider")]
    assert [(e["cost_usd"], e["cost_source"]) for e in log_entries(tmp_path / "table")] == [(0.004, "price_table")]
    assert [(e["cost_usd"], e["cost_source"]) for e in log_entries(tmp_path / "unpriced")] == [(0.0, "unpriced")]


def test_cap_raises_before_any_call_once_the_log_reaches_it(tmp_path):
    inner = ScriptedClient(cost=0.006)
    cache = CachedClient(inner, tmp_path, budget_usd=0.01)
    request(cache, messages=[{"role": "user", "content": "first"}])
    request(cache, messages=[{"role": "user", "content": "second"}])
    with pytest.raises(SpendingCapError, match="spending cap") as caught:
        request(cache, messages=[{"role": "user", "content": "third"}])
    # A fatal error, so the resolver and the answerer stop instead of retrying.
    assert isinstance(caught.value, FatalModelError) and not isinstance(caught.value, RetryableModelError)
    assert len(inner.calls) == 2
    # A saved reply costs nothing and is still returned to a later run.
    later = CachedClient(inner, tmp_path, budget_usd=0.01)
    assert request(later, messages=[{"role": "user", "content": "first"}]).content == '{"op": "ADD"}'
    assert len(inner.calls) == 2
    # Within one client a repeat is a fresh request, so the cap stops it.
    with pytest.raises(SpendingCapError):
        request(later, messages=[{"role": "user", "content": "first"}])
    assert len(inner.calls) == 2


def test_cap_counts_costs_already_in_the_log_at_start(tmp_path):
    (tmp_path / "calls.jsonl").write_text("\n".join([
        json.dumps({"cost_usd": 0.007}), "not json", json.dumps({"cost_usd": None}), json.dumps({"cost_usd": 0.004}),
    ]) + "\n", encoding="utf-8")
    inner = ScriptedClient()
    capped = CachedClient(inner, tmp_path, budget_usd=0.01)
    assert capped.spent_usd == pytest.approx(0.011)
    with pytest.raises(SpendingCapError):
        request(capped)
    assert inner.calls == []
    request(CachedClient(inner, tmp_path, budget_usd=0.012))
    assert len(inner.calls) == 1


def test_without_a_budget_nothing_is_capped(tmp_path):
    (tmp_path / "calls.jsonl").write_text(json.dumps({"cost_usd": 1000.0}) + "\n", encoding="utf-8")
    inner = ScriptedClient()
    request(CachedClient(inner, tmp_path, budget_usd=None))
    assert len(inner.calls) == 1


def test_use_cache_false_neither_reads_nor_writes_saved_replies_but_still_logs_and_caps(tmp_path):
    request(CachedClient(ScriptedClient(ModelReply('{"op": "KEEP"}')), tmp_path))
    (saved,) = saved_replies(tmp_path)
    before = saved.read_text(encoding="utf-8")
    inner = ScriptedClient(ModelReply('{"op": "FLAG"}'), cost=0.02)
    uncached = CachedClient(inner, tmp_path, budget_usd=0.02, use_cache=False)
    assert request(uncached).content == '{"op": "FLAG"}'
    assert len(inner.calls) == 1
    assert saved_replies(tmp_path) == [saved] and saved.read_text(encoding="utf-8") == before
    assert [(e["cache_hit"], e["cost_usd"]) for e in log_entries(tmp_path)] == [(False, 0.0), (False, 0.02)]
    with pytest.raises(SpendingCapError):
        request(uncached)
    assert len(inner.calls) == 1


def test_cache_and_log_never_contain_the_api_key(sdk, tmp_path):
    client = CachedClient(openrouter_client({"OPENROUTER_API_KEY": "synthetic-router-key"}), tmp_path / "cache")
    request(client)
    request(client)
    written = "".join(path.read_text(encoding="utf-8") for path in (tmp_path / "cache").rglob("*") if path.is_file())
    assert written and "synthetic-router-key" not in written
    assert "synthetic-router-key" not in json.dumps(client.describe())


# Selection from the environment


def test_from_env_defaults_to_the_built_in_openai_client_with_cache_and_cap(sdk):
    client = from_env({"OPENAI_API_KEY": "synthetic-openai-key"})
    assert isinstance(client, CachedClient) and isinstance(client.inner, OpenAICompletionClient)
    assert sdk.OpenAI.call_args.kwargs["base_url"] == "https://api.openai.com/v1"
    assert (str(client.cache_dir), client.budget_usd, client.use_cache) == ("cache/llm", 12.0, True)
    assert client.log_path.as_posix() == "cache/llm/calls.jsonl"
    sdk.create.assert_not_called()


def test_from_env_selects_openrouter_and_local_and_never_caps_the_local_server(sdk):
    paid = from_env({"TRACEMEM_PROVIDER": "OpenRouter", "OPENROUTER_API_KEY": "synthetic-router-key",
                     "TRACEMEM_BUDGET_USD": "3.5", "TRACEMEM_CACHE": "off", "TRACEMEM_CACHE_DIR": "elsewhere"})
    assert paid.inner.label == "openrouter"
    assert (str(paid.cache_dir), paid.budget_usd, paid.use_cache) == ("elsewhere", 3.5, False)
    assert paid.describe() == {"cache": "elsewhere", "use_cache": False, "inner": paid.inner.describe()}
    local = from_env({"TRACEMEM_PROVIDER": "local", "TRACEMEM_BUDGET_USD": "3.5"})
    assert local.inner.label == "local" and local.inner.token_field == "max_tokens"
    assert local.budget_usd is None and local.use_cache is True
    sdk.create.assert_not_called()


def test_from_env_reads_the_process_environment_when_no_mapping_is_given(sdk, monkeypatch):
    monkeypatch.setenv("TRACEMEM_PROVIDER", "local")
    monkeypatch.setenv("TRACEMEM_LOCAL_BASE_URL", "http://192.0.2.10:11434/v1")
    client = from_env()
    assert client.inner.base_url == "http://192.0.2.10:11434/v1"


@pytest.mark.parametrize("provider", ["anthropic", "ollama", ""])
def test_from_env_rejects_an_unknown_provider_before_constructing_a_client(sdk, provider):
    with pytest.raises(ResolverConfigError, match="TRACEMEM_PROVIDER"):
        from_env({"TRACEMEM_PROVIDER": provider, "OPENAI_API_KEY": "synthetic-openai-key"})
    sdk.OpenAI.assert_not_called()


@pytest.mark.parametrize("budget", ["twelve", "", "nan", "inf", "-1"])
def test_from_env_rejects_a_budget_that_is_not_a_non_negative_number(sdk, budget):
    with pytest.raises(ResolverConfigError, match="TRACEMEM_BUDGET_USD"):
        from_env({"TRACEMEM_PROVIDER": "local", "TRACEMEM_BUDGET_USD": budget})
    sdk.OpenAI.assert_not_called()


@pytest.mark.parametrize("value", ["false", "0", "disabled"])
def test_from_env_rejects_a_cache_switch_other_than_on_or_off(sdk, value):
    with pytest.raises(ResolverConfigError, match="TRACEMEM_CACHE"):
        from_env({"TRACEMEM_PROVIDER": "local", "TRACEMEM_CACHE": value})
    sdk.OpenAI.assert_not_called()


# Wiring


def test_comparison_client_is_selected_by_the_provider_setting(sdk, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-openai-key")
    default = comparison.make_client()
    assert isinstance(default, CachedClient) and isinstance(default.inner, OpenAICompletionClient)
    monkeypatch.setenv("TRACEMEM_PROVIDER", "local")
    local = comparison.make_client()
    assert isinstance(local, CachedClient) and isinstance(local.inner, OpenAICompatibleClient)
    assert local.inner.label == "local"
    sdk.create.assert_not_called()


def test_comparison_settings_record_the_provider_settings_but_not_the_cache_or_the_key(sdk, tmp_path):
    def settings(**environ):
        return comparison.comparison_settings(CONFIG, 12000, from_env(environ))

    base = settings(TRACEMEM_PROVIDER="local")
    assert base["model_client"] == {"label": "local", "base_url": "http://127.0.0.1:11434/v1",
                                    "extra_body": {"reasoning_effort": "none"}, "token_field": "max_tokens"}
    assert settings(TRACEMEM_PROVIDER="local", TRACEMEM_CACHE="off", TRACEMEM_CACHE_DIR=str(tmp_path)) == base
    assert settings(TRACEMEM_PROVIDER="local", TRACEMEM_LOCAL_THINKING="on") != base
    assert settings(TRACEMEM_PROVIDER="local", TRACEMEM_LOCAL_BASE_URL="http://192.0.2.7:11434/v1") != base
    router = settings(TRACEMEM_PROVIDER="openrouter", OPENROUTER_API_KEY="synthetic-router-key")
    assert router["model_client"]["label"] == "openrouter" and router != base
    assert "synthetic-router-key" not in json.dumps(router)
    default = settings(OPENAI_API_KEY="synthetic-openai-key")
    assert default["model_client"] == "OpenAICompletionClient"
    assert "synthetic-openai-key" not in json.dumps(default)


class VisibleStateClient:
    """Resolve from visible state and abstain from every answer, offline."""

    def __init__(self, label="scripted"):
        self.label = label
        self.calls = 0

    def describe(self):
        return {"label": self.label}

    def complete(self, *, config, messages, response_format):
        self.calls += 1
        if response_format["json_schema"]["name"] == "memory_answer":
            return ModelReply(json.dumps({"status": "abstain", "value": None, "cited_turn_ids": [], "text": ""}),
                              input_tokens=4, output_tokens=2)
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


def test_usage_counts_cache_hits_and_the_report_refuses_runs_on_different_clients(tmp_path, monkeypatch):
    monkeypatch.setattr(harness, "_git", lambda *args: None)
    scenario = Scenario.model_validate(minimal_dict())
    config = ResolverConfig(model="offline-comparison", max_attempts=2)

    def run(client_factory):
        spec = SystemSpec("tracemem-controlled", lambda meta, gold: comparison.make_system(
            "tracemem-controlled", meta, config=config, client=client_factory()), False, "offline cache test")
        result = harness.run(spec, [scenario], "dev", condition="gold_candidates")
        return harness.write_run(result, tmp_path / "runs")

    inner = VisibleStateClient()
    first = run(lambda: CachedClient(inner, tmp_path / "cache"))
    calls = inner.calls
    again = run(lambda: CachedClient(inner, tmp_path / "cache"))
    assert calls and inner.calls == calls
    usage = [json.loads((folder / "usage.json").read_text(encoding="utf-8")) for folder in (first, again)]
    assert usage[0]["model_cache"]["total"] == {"calls": calls, "hits": 0, "misses": calls}
    assert usage[1]["model_cache"]["total"] == {"calls": calls, "hits": calls, "misses": 0}
    assert set(usage[1]["model_cache"]["by_scenario"]) == {scenario.scenario_id}
    # The rerun's tokens are zero although it made the same calls; the hits show why.
    assert sum(usage[1][stage]["total"]["calls"] for stage in ("resolver", "answer")) == calls
    assert sum(usage[1][stage]["total"]["input_tokens"] for stage in ("resolver", "answer")) == 0
    uncached = run(VisibleStateClient)
    assert "model_cache" not in json.loads((uncached / "usage.json").read_text(encoding="utf-8"))
    assert comparison_table([first, again, uncached], n=20)
    other_server = run(lambda: VisibleStateClient(label="other-server"))
    with pytest.raises(ValueError, match="shared inputs and models are required"):
        comparison_table([first, other_server], n=20)
