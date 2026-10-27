"""Offline checks of the local and OpenRouter clients and the reply cache.

As in test_resolver_client.py, a fake module exposes only the SDK surface the
adapter consumes, so no key, network, model server or SDK is required. The cache
tests use a scripted inner client and a temporary cache folder; the wiring tests
also run the minimal scenario offline through the harness and the report.
"""

from __future__ import annotations

import io
import json
import os
import sys
import threading
import time
import traceback
import urllib.request
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
    model_digest,
    openrouter_client,
    read_dotenv,
    server_context_length,
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
            "TRACEMEM_LOCAL_THINKING", "TRACEMEM_LOCAL_API_KEY", "TRACEMEM_LOCAL_CONTEXT_TOKENS", "TRACEMEM_CACHE",
            "TRACEMEM_CACHE_DIR", "TRACEMEM_COST_LOG", "TRACEMEM_BUDGET_USD", "TRACEMEM_RESOLVER_MODEL")
# from_env needs the model for the local and OpenRouter providers; OpenRouter only a priced one.
LOCAL = {"TRACEMEM_PROVIDER": "local", "TRACEMEM_RESOLVER_MODEL": "test-model"}
ROUTER = {"TRACEMEM_PROVIDER": "openrouter", "OPENROUTER_API_KEY": "synthetic-router-key",
          "TRACEMEM_RESOLVER_MODEL": "anthropic/claude-haiku-5.5"}


def completion(*, content='{"op": "ADD"}', finish_reason="stop", cost=None, refusal=None, usage=True,
               prompt_tokens=17):
    usage = SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=9) if usage else None
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
    # The local server's context, as its /api/ps reports it after each reply.
    module.served_context = 16384
    module.context_checks = []

    def served(base_url, model, timeout_seconds=10.0):
        module.context_checks.append((base_url, model))
        return module.served_context

    monkeypatch.setattr(model_client, "server_context_length", served)
    # The digest each installed model has, as the local server's /api/tags lists it.
    module.digests = {"test-model": "synthetic-digest-1", "other-model": "synthetic-digest-2"}
    module.digest_lookups = []

    def digest(base_url, model, timeout_seconds=10.0):
        module.digest_lookups.append((base_url, model))
        if model not in module.digests:
            raise ResolverConfigError(f"the local server has no model {model}")
        return module.digests[model]

    monkeypatch.setattr(model_client, "model_digest", digest)
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


def cached(inner, folder, **settings):
    """A reply cache in folder whose cost log is folder/calls.jsonl, where log_entries reads it.

    The explicit log keeps every test away from the default cost log of the folder it runs in.
    """
    return CachedClient(inner, folder, log_path=folder / "calls.jsonl", **settings)


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
    assert request(cached(local_client({}), tmp_path)) == expected
    assert saved_replies(tmp_path) == []
    # A later run asks the provider again instead of replaying the incomplete reply.
    assert request(cached(local_client({}), tmp_path)) == expected
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
    client = from_env({**LOCAL, "TRACEMEM_LOCAL_BASE_URL": "  ", "TRACEMEM_CACHE_DIR": " ", "TRACEMEM_COST_LOG": " "})
    assert client.inner.base_url == "http://127.0.0.1:11434/v1"
    assert sdk.OpenAI.call_args.kwargs["base_url"] == "http://127.0.0.1:11434/v1"
    assert sdk.digest_lookups == [("http://127.0.0.1:11434/v1", "test-model")]
    assert str(client.cache_dir) == "cache/llm"
    assert client.log_path.as_posix() == "cache/costs.jsonl"


# Error mapping


@pytest.mark.parametrize("exception_name", ["APIConnectionError", "APITimeoutError"])
def test_connection_and_timeout_errors_are_retryable_and_sanitized(sdk, exception_name):
    # A remote provider's connection failure is retried; a local server's is not (below).
    sdk.create.side_effect = getattr(sdk, exception_name)("synthetic-private-provider-body")
    with pytest.raises(RetryableModelError, match="connection or timeout") as caught:
        request(openrouter_client({"OPENROUTER_API_KEY": "synthetic-router-key"}))
    assert "synthetic-private-provider-body" not in "".join(traceback.format_exception(caught.value))


def test_a_local_server_that_refuses_the_connection_stops_the_run_but_a_timeout_is_retried(sdk):
    client = local_client({"TRACEMEM_LOCAL_BASE_URL": "http://192.0.2.10:11434/v1"})
    sdk.create.side_effect = sdk.APIConnectionError("synthetic-private-provider-body")
    with pytest.raises(FatalModelError, match="refused or dropped the connection") as caught:
        request(client)
    assert not isinstance(caught.value, RetryableModelError)
    assert "http://192.0.2.10:11434/v1" in str(caught.value)
    assert "synthetic-private-provider-body" not in "".join(traceback.format_exception(caught.value))
    # A slow model on a busy server is still retried within the attempt limit.
    sdk.create.side_effect = sdk.APITimeoutError("synthetic-private-provider-body")
    with pytest.raises(RetryableModelError, match="connection or timeout"):
        request(client)


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


# The local server's context


def test_local_client_records_the_context_the_server_must_give_the_model(sdk):
    assert local_client({}).describe()["context_tokens"] == 16384
    assert local_client({"TRACEMEM_LOCAL_CONTEXT_TOKENS": " 8192 "}).describe()["context_tokens"] == 8192
    assert local_client({"TRACEMEM_LOCAL_CONTEXT_TOKENS": " "}).describe()["context_tokens"] == 16384
    # Only the local server is checked; OpenRouter refuses a request that does not fit.
    router = openrouter_client({"OPENROUTER_API_KEY": "synthetic-router-key"})
    assert "context_tokens" not in router.describe()
    request(router)
    assert sdk.context_checks == []


@pytest.mark.parametrize("value", ["0", "-4096", "lots", "16384.5"])
def test_local_client_rejects_a_context_that_is_not_a_positive_whole_number(sdk, value):
    with pytest.raises(ResolverConfigError, match="TRACEMEM_LOCAL_CONTEXT_TOKENS"):
        from_env({**LOCAL, "TRACEMEM_LOCAL_CONTEXT_TOKENS": value})
    sdk.OpenAI.assert_not_called()
    assert sdk.digest_lookups == []


def test_every_local_reply_checks_the_context_the_server_reports(sdk):
    client = local_client({"TRACEMEM_LOCAL_BASE_URL": "http://192.0.2.10:11434/v1"})
    request(client)
    request(client, config=ResolverConfig(model="other-model"))
    assert sdk.context_checks == [("http://192.0.2.10:11434/v1", "test-model"),
                                  ("http://192.0.2.10:11434/v1", "other-model")]


@pytest.mark.parametrize("served", [4096, 32768, None])
def test_a_server_with_another_context_stops_the_run_and_nothing_is_saved(sdk, tmp_path, served):
    sdk.served_context = served
    client = cached(local_client({}), tmp_path)
    with pytest.raises(FatalModelError, match="context") as caught:
        request(client)
    assert not isinstance(caught.value, RetryableModelError)
    assert saved_replies(tmp_path) == [] and log_entries(tmp_path) == []
    sdk.served_context = 16384
    assert request(client) == ModelReply('{"op": "ADD"}', input_tokens=17, output_tokens=9)
    assert len(saved_replies(tmp_path)) == 1


def test_a_reply_that_read_fewer_tokens_than_the_request_holds_stops_the_run_unsaved(sdk, tmp_path):
    # A 4,414-token request cut to 2,050 tokens by a 4,096-token context, at four bytes a token.
    cut = [{"role": "system", "content": "x" * 17000}, {"role": "user", "content": "y" * 656}]
    sdk.create.return_value = completion(prompt_tokens=2050)
    client = cached(local_client({}), tmp_path)
    with pytest.raises(FatalModelError, match="read 2050 tokens of a 17656-byte request") as caught:
        request(client, messages=cut)
    assert not isinstance(caught.value, RetryableModelError)
    assert saved_replies(tmp_path) == [] and log_entries(tmp_path) == []
    # Six bytes a token is the most a whole request takes; the pilot's took 4.0 to 4.6.
    whole = [{"role": "user", "content": "z" * (2050 * 6)}]
    assert request(client, messages=whole).input_tokens == 2050
    sdk.create.return_value = completion(usage=False)
    assert request(client, messages=cut).input_tokens == 0  # nothing reported, nothing to compare


class ServerListing:
    def __init__(self, body):
        self.body = body
        self.opened = []

    def __call__(self, url, timeout):
        self.opened.append((url, timeout))
        if isinstance(self.body, Exception):
            raise self.body
        return io.BytesIO(self.body.encode("utf-8"))


def test_server_context_length_reads_the_loaded_model_from_ollama_ps(monkeypatch):
    listing = ServerListing(json.dumps({"models": [
        {"name": "nomic-embed-text:latest", "model": "nomic-embed-text:latest", "context_length": 2048},
        {"name": "qwen3.5:4b", "model": "qwen3.5:4b", "context_length": 16384},
        {"name": "unreported:1b", "model": "unreported:1b"},
    ]}))
    monkeypatch.setattr(urllib.request, "urlopen", listing)
    assert server_context_length("http://127.0.0.1:11434/v1", "qwen3.5:4b") == 16384
    assert server_context_length("http://192.0.2.10:11434/", "nomic-embed-text") == 2048
    assert server_context_length("http://127.0.0.1:11434/v1/", "qwen3.5:9b") is None
    assert server_context_length("http://127.0.0.1:11434/v1", "unreported:1b") is None
    assert [url for url, _ in listing.opened] == ["http://127.0.0.1:11434/api/ps", "http://192.0.2.10:11434/api/ps",
                                                 "http://127.0.0.1:11434/api/ps", "http://127.0.0.1:11434/api/ps"]
    assert all(timeout == 10.0 for _, timeout in listing.opened)


@pytest.mark.parametrize("body", [OSError("synthetic refusal"), "not json", '["models"]', '{"models": 7}'])
def test_a_server_without_a_readable_listing_stops_the_run_or_lists_nothing(monkeypatch, body):
    monkeypatch.setattr(urllib.request, "urlopen", ServerListing(body))
    if isinstance(body, Exception) or body == "not json":
        with pytest.raises(FatalModelError, match="api/ps"):
            server_context_length("http://127.0.0.1:11434/v1", "qwen3.5:4b")
    else:
        assert server_context_length("http://127.0.0.1:11434/v1", "qwen3.5:4b") is None


def test_server_context_length_reads_only_http_addresses(monkeypatch):
    listing = ServerListing("{}")
    monkeypatch.setattr(urllib.request, "urlopen", listing)
    with pytest.raises(FatalModelError, match="http"):
        server_context_length("file:///synthetic/v1", "qwen3.5:4b")
    assert listing.opened == []


def test_model_digest_reads_the_installed_model_from_ollama_tags(monkeypatch):
    listing = ServerListing(json.dumps({"models": [
        {"name": "nomic-embed-text:latest", "model": "nomic-embed-text:latest", "digest": "0a109f422b47"},
        {"name": "qwen3.5:4b", "model": "qwen3.5:4b", "digest": " 2a6f4c1b9d3e "},
        {"name": "undigested:1b", "model": "undigested:1b"},
    ]}))
    monkeypatch.setattr(urllib.request, "urlopen", listing)
    assert model_digest("http://127.0.0.1:11434/v1", "qwen3.5:4b") == "2a6f4c1b9d3e"
    assert model_digest("http://192.0.2.10:11434/", "nomic-embed-text") == "0a109f422b47"
    with pytest.raises(ResolverConfigError, match="ollama pull qwen3.5:9b"):
        model_digest("http://127.0.0.1:11434/v1", "qwen3.5:9b")
    with pytest.raises(FatalModelError, match="no digest"):
        model_digest("http://127.0.0.1:11434/v1", "undigested:1b")
    assert [url for url, _ in listing.opened] == ["http://127.0.0.1:11434/api/tags", "http://192.0.2.10:11434/api/tags",
                                                 "http://127.0.0.1:11434/api/tags", "http://127.0.0.1:11434/api/tags"]
    assert all(timeout == 10.0 for _, timeout in listing.opened)


@pytest.mark.parametrize("body", [OSError("synthetic refusal"), "not json", '["models"]', '{"models": 7}'])
def test_a_server_without_a_readable_model_list_stops_the_run_or_has_no_such_model(monkeypatch, body):
    monkeypatch.setattr(urllib.request, "urlopen", ServerListing(body))
    if isinstance(body, Exception) or body == "not json":
        with pytest.raises(FatalModelError, match="api/tags"):
            model_digest("http://127.0.0.1:11434/v1", "qwen3.5:4b")
    else:
        with pytest.raises(ResolverConfigError, match="no model qwen3.5:4b"):
            model_digest("http://127.0.0.1:11434/v1", "qwen3.5:4b")


def test_model_digest_reads_only_http_addresses(monkeypatch):
    listing = ServerListing("{}")
    monkeypatch.setattr(urllib.request, "urlopen", listing)
    with pytest.raises(FatalModelError, match="http"):
        model_digest("file:///synthetic/v1", "qwen3.5:4b")
    assert listing.opened == []


def test_a_repulled_local_model_gets_new_cache_keys_so_old_replies_are_not_replayed(sdk):
    client = from_env(LOCAL)
    assert client.inner.describe()["model_digest"] == "synthetic-digest-1"
    request(client)
    assert request(from_env(LOCAL)).input_tokens == 0  # saved, and replayed for the same weights
    # The same tag pulled again with other weights.
    sdk.digests["test-model"] = "synthetic-digest-3"
    repulled = from_env(LOCAL)
    assert repulled.key(config=CONFIG, messages=MESSAGES, response_format=FORMAT) != \
        client.key(config=CONFIG, messages=MESSAGES, response_format=FORMAT)
    assert request(repulled).input_tokens == 17
    assert sdk.create.call_count == 2
    assert sdk.digest_lookups == [("http://127.0.0.1:11434/v1", "test-model")] * 3


def test_a_local_client_built_for_one_model_calls_no_other(sdk):
    client = local_client({}, model="test-model")
    with pytest.raises(FatalModelError, match="other-model") as caught:
        request(client, config=ResolverConfig(model="other-model"))
    assert not isinstance(caught.value, RetryableModelError)
    sdk.create.assert_not_called()
    assert request(client).input_tokens == 17


def test_from_env_refuses_a_local_model_the_server_has_not_installed(sdk):
    with pytest.raises(ResolverConfigError, match="no model absent-model"):
        from_env({**LOCAL, "TRACEMEM_RESOLVER_MODEL": "absent-model"})
    with pytest.raises(ResolverConfigError, match="TRACEMEM_RESOLVER_MODEL"):
        from_env({"TRACEMEM_PROVIDER": "local"})
    sdk.OpenAI.assert_not_called()


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
    first = request(cached(inner, tmp_path))
    assert first == ModelReply('{"op": "KEEP"}', input_tokens=1000, output_tokens=200)
    # A new instance on the same folder stands for a later run.
    later = cached(inner, tmp_path)
    assert request(later) == ModelReply('{"op": "KEEP"}', input_tokens=0, output_tokens=0)
    assert len(inner.calls) == 1
    assert later.stats == {"calls": 1, "hits": 1, "misses": 0, "cost_usd": 0.0}


def test_cache_key_ignores_timeout_and_attempts_but_not_model_messages_schema_or_client(tmp_path):
    cache = cached(ScriptedClient(), tmp_path)

    def key(config=CONFIG, messages=MESSAGES, response_format=FORMAT, client=cache):
        return client.key(config=config, messages=messages, response_format=response_format)

    base = key()
    assert key(config=CONFIG.model_copy(update={"timeout_seconds": 120.0, "max_attempts": 5})) == base
    assert key(config=CONFIG.model_copy(update={"model": "other-model"})) != base
    assert key(config=CONFIG.model_copy(update={"max_completion_tokens": 74})) != base
    assert key(config=CONFIG.model_copy(update={"temperature": 0.0})) != base
    assert key(messages=[{"role": "user", "content": "other evidence"}]) != base
    assert key(response_format={"type": "json_schema", "json_schema": {"name": "other"}}) != base
    assert key(client=cached(ScriptedClient(label="other-provider"), tmp_path)) != base


def test_a_request_differing_only_in_timeout_or_attempts_is_served_from_the_cache(tmp_path):
    inner = ScriptedClient()
    request(cached(inner, tmp_path))
    later = cached(inner, tmp_path)
    request(later, config=CONFIG.model_copy(update={"timeout_seconds": 180.0, "max_attempts": 3}))
    request(later, config=CONFIG.model_copy(update={"model": "other-model"}))
    assert len(inner.calls) == 2
    assert later.stats["hits"] == 1


@pytest.mark.parametrize("error", [RetryableModelError("transient"), FatalModelError("fatal")])
def test_provider_errors_are_not_cached(tmp_path, error):
    inner = ScriptedClient(error, ModelReply('{"op": "ADD"}'))
    cache = cached(inner, tmp_path)
    with pytest.raises(type(error)):
        request(cache)
    assert saved_replies(tmp_path) == [] and log_entries(tmp_path) == []
    assert request(cache).content == '{"op": "ADD"}'
    assert len(inner.calls) == 2 and len(saved_replies(tmp_path)) == 1


@pytest.mark.parametrize("reply", [ModelReply('{"op":', finish_reason="length"), ModelReply("", refused=True)])
def test_refused_or_cut_off_replies_are_logged_but_not_saved(tmp_path, reply):
    inner = ScriptedClient(reply, reply)
    cache = cached(inner, tmp_path)
    # An identical retry must reach the provider again, as it would without the cache.
    assert request(cache) == reply and request(cache) == reply
    assert len(inner.calls) == 2 and saved_replies(tmp_path) == []
    assert [entry["cache_hit"] for entry in log_entries(tmp_path)] == [False, False]


def test_a_repeat_within_one_client_reaches_the_provider_and_a_later_run_replays_both_in_order(tmp_path):
    inner = ScriptedClient(ModelReply("first reply", 10, 1), ModelReply("second reply", 20, 2))
    run = cached(inner, tmp_path)
    assert [request(run).content for _ in range(2)] == ["first reply", "second reply"]
    assert len(inner.calls) == 2 and len(saved_replies(tmp_path)) == 2
    later = cached(inner, tmp_path)
    assert [request(later) for _ in range(2)] == [ModelReply("first reply"), ModelReply("second reply")]
    assert len(inner.calls) == 2 and later.stats["hits"] == 2


def test_a_retry_that_resends_the_same_feedback_is_not_answered_from_the_cache(tmp_path):
    question = SystemQuestion(question_id="opaque", scenario_id="synthetic", kind="current", text="What is settled?")
    config = ResolverConfig(model="test-model", max_attempts=3)
    valid = json.dumps({"status": "none", "value": None, "cited_turn_ids": [], "text": ""})
    inner = ScriptedClient(ModelReply("not json"), ModelReply("not json"), ModelReply(valid))
    answer = comparison.SharedAnswerer(config, cached(inner, tmp_path)).answer(question, [], {})
    # Attempts 2 and 3 send the same feedback; the third must not replay the second's invalid reply.
    assert inner.calls[1] == inner.calls[2] and len(inner.calls) == 3
    assert answer.status == "none"
    rerun = comparison.SharedAnswerer(config, cached(inner, tmp_path)).answer(question, [], {})
    assert rerun.status == "none" and len(inner.calls) == 3


def test_a_malformed_saved_reply_is_a_miss(tmp_path):
    inner = ScriptedClient()
    cache = cached(inner, tmp_path)
    path = cache._path(cache.key(config=CONFIG, messages=MESSAGES, response_format=FORMAT))
    path.parent.mkdir(parents=True)
    path.write_text('["not", "a", "reply"]', encoding="utf-8")
    assert request(cache).input_tokens == 1000
    assert len(inner.calls) == 1


def test_cost_log_records_misses_with_cost_and_hits_at_zero_cost(tmp_path):
    inner = ScriptedClient(cost=0.004)
    first = cached(inner, tmp_path)
    request(first)
    later = cached(inner, tmp_path)
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
    request(cached(ScriptedClient(cost=0.5), tmp_path / "reported"), config=priced)
    request(cached(ScriptedClient(), tmp_path / "table"), config=priced)
    request(cached(ScriptedClient(), tmp_path / "unpriced"))
    # 1000 input tokens at US$2 and 200 output tokens at US$10 per million.
    assert [(e["cost_usd"], e["cost_source"]) for e in log_entries(tmp_path / "reported")] == [(0.5, "provider")]
    assert [(e["cost_usd"], e["cost_source"]) for e in log_entries(tmp_path / "table")] == [(0.004, "price_table")]
    assert [(e["cost_usd"], e["cost_source"]) for e in log_entries(tmp_path / "unpriced")] == [(0.0, "unpriced")]


def test_cap_raises_before_any_call_once_the_log_reaches_it(tmp_path):
    inner = ScriptedClient(cost=0.006)
    cache = cached(inner, tmp_path, budget_usd=0.01)
    request(cache, messages=[{"role": "user", "content": "first"}])
    request(cache, messages=[{"role": "user", "content": "second"}])
    with pytest.raises(SpendingCapError, match="spending cap") as caught:
        request(cache, messages=[{"role": "user", "content": "third"}])
    # A fatal error, so the resolver and the answerer stop instead of retrying.
    assert isinstance(caught.value, FatalModelError) and not isinstance(caught.value, RetryableModelError)
    assert len(inner.calls) == 2
    # A saved reply costs nothing and is still returned to a later run.
    later = cached(inner, tmp_path, budget_usd=0.01)
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
    capped = cached(inner, tmp_path, budget_usd=0.01)
    assert capped.spent_usd == pytest.approx(0.011)
    with pytest.raises(SpendingCapError):
        request(capped)
    assert inner.calls == []
    request(cached(inner, tmp_path, budget_usd=0.012))
    assert len(inner.calls) == 1


def test_without_a_budget_nothing_is_capped(tmp_path):
    (tmp_path / "calls.jsonl").write_text(json.dumps({"cost_usd": 1000.0}) + "\n", encoding="utf-8")
    inner = ScriptedClient()
    request(cached(inner, tmp_path, budget_usd=None))
    assert len(inner.calls) == 1


def test_use_cache_false_neither_reads_nor_writes_saved_replies_but_still_logs_and_caps(tmp_path):
    request(cached(ScriptedClient(ModelReply('{"op": "KEEP"}')), tmp_path))
    (saved,) = saved_replies(tmp_path)
    before = saved.read_text(encoding="utf-8")
    inner = ScriptedClient(ModelReply('{"op": "FLAG"}'), cost=0.02)
    uncached = cached(inner, tmp_path, budget_usd=0.02, use_cache=False)
    assert request(uncached).content == '{"op": "FLAG"}'
    assert len(inner.calls) == 1
    assert saved_replies(tmp_path) == [saved] and saved.read_text(encoding="utf-8") == before
    assert [(e["cache_hit"], e["cost_usd"]) for e in log_entries(tmp_path)] == [(False, 0.0), (False, 0.02)]
    with pytest.raises(SpendingCapError):
        request(uncached)
    assert len(inner.calls) == 1


def test_a_fresh_cache_folder_keeps_the_spending_because_the_cost_log_is_not_in_it(sdk, tmp_path):
    # Two repeats, each with its own reply cache, as a repeat script would run them.
    first = from_env({**ROUTER, "TRACEMEM_BUDGET_USD": "0.01", "TRACEMEM_CACHE_DIR": "cache/llm-r1"})
    first.inner = ScriptedClient(cost=0.006)
    request(first, messages=[{"role": "user", "content": "first"}])
    request(first, messages=[{"role": "user", "content": "second"}])
    fresh = from_env({**ROUTER, "TRACEMEM_BUDGET_USD": "0.01", "TRACEMEM_CACHE_DIR": "cache/llm-r2"})
    fresh.inner = ScriptedClient(cost=0.006)
    assert fresh.log_path == first.log_path and fresh.spent_usd == pytest.approx(0.012)
    with pytest.raises(SpendingCapError, match="spending cap"):
        request(fresh, messages=[{"role": "user", "content": "third"}])
    assert fresh.inner.calls == []
    # Both calls sit in the one log, and neither reply folder holds a log of its own.
    logged =[json.loads(line) for line in (tmp_path / "cache" / "costs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [entry["cost_usd"] for entry in logged] == [0.006, 0.006]
    assert not list((tmp_path / "cache" / "llm-r1").glob("*.jsonl"))
    # TRACEMEM_COST_LOG moves the log, and with it the spending counted.
    moved = from_env({**ROUTER, "TRACEMEM_BUDGET_USD": "0.01", "TRACEMEM_COST_LOG": "elsewhere/costs.jsonl"})
    assert moved.log_path.as_posix() == "elsewhere/costs.jsonl" and moved.spent_usd == 0.0


def test_a_cache_built_without_a_log_path_uses_the_shared_cost_log_whatever_its_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cache").mkdir()
    (tmp_path / "cache" / "costs.jsonl").write_text(json.dumps({"cost_usd": 0.02}) + "\n", encoding="utf-8")
    inner = ScriptedClient()
    for folder in ("cache/llm", "cache/llm-fresh", tmp_path / "elsewhere"):
        cache = CachedClient(inner, folder, budget_usd=0.01)
        assert cache.log_path.as_posix() == "cache/costs.jsonl" and cache.spent_usd == pytest.approx(0.02)
        with pytest.raises(SpendingCapError):
            request(cache)
    assert inner.calls == []


def test_the_cap_reads_the_log_again_before_every_paid_call(tmp_path):
    log = tmp_path / "costs.jsonl"
    inner = ScriptedClient(cost=0.004)
    one = CachedClient(inner, tmp_path / "one", log_path=log, budget_usd=0.01)
    other = CachedClient(inner, tmp_path / "two", log_path=log, budget_usd=0.01)
    request(one, messages=[{"role": "user", "content": "a"}])
    request(other, messages=[{"role": "user", "content": "b"}])
    # Another process appends to the same log after both clients were built.
    with log.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"cost_usd": 0.003}) + "\n")
    with pytest.raises(SpendingCapError, match=r"US\$0\.0110 logged"):
        request(one, messages=[{"role": "user", "content": "c"}])
    with pytest.raises(SpendingCapError):
        request(other, messages=[{"role": "user", "content": "d"}])
    assert len(inner.calls) == 2
    # A saved reply costs nothing, so a later run still gets it although the cap is reached.
    later = CachedClient(inner, tmp_path / "one", log_path=log, budget_usd=0.01)
    assert request(later, messages=[{"role": "user", "content": "a"}]).content == '{"op": "ADD"}'
    assert len(inner.calls) == 2 and later.stats["hits"] == 1


def test_a_paid_call_is_logged_before_its_reply_is_saved(tmp_path):
    inner = ScriptedClient(cost=0.5)
    cache = cached(inner, tmp_path, budget_usd=1.0)
    # A file where the reply's folder should be makes the save fail, as a full disk would.
    folder = cache._path(cache.key(config=CONFIG, messages=MESSAGES, response_format=FORMAT)).parent
    folder.write_text("not a folder", encoding="utf-8")
    with pytest.raises(OSError):
        request(cache)
    assert len(inner.calls) == 1 and saved_replies(tmp_path) == []
    assert [(e["cache_hit"], e["cost_usd"], e["cost_source"]) for e in log_entries(tmp_path)] == [
        (False, 0.5, "provider")]
    assert cached(inner, tmp_path, budget_usd=1.0).spent_usd == pytest.approx(0.5)


def test_a_failed_save_leaves_no_temporary_file(tmp_path, monkeypatch):
    inner = ScriptedClient(cost=0.5)
    cache = cached(inner, tmp_path)

    def full_disk(source, target):
        raise OSError("synthetic full disk")

    monkeypatch.setattr(model_client.os, "replace", full_disk)
    with pytest.raises(OSError, match="synthetic full disk"):
        request(cache)
    assert list(tmp_path.rglob("*.tmp")) == [] and saved_replies(tmp_path) == []
    assert [e["cost_usd"] for e in log_entries(tmp_path)] == [0.5]


def test_cache_and_log_never_contain_the_api_key(sdk, tmp_path):
    client = cached(openrouter_client({"OPENROUTER_API_KEY": "synthetic-router-key"}), tmp_path / "cache")
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
    # The cost log is not in the cache folder, so a fresh folder does not reset the cap.
    assert client.log_path.as_posix() == "cache/costs.jsonl"
    sdk.create.assert_not_called()


def test_from_env_selects_openrouter_and_local_and_never_caps_the_local_server(sdk):
    paid = from_env({**ROUTER, "TRACEMEM_PROVIDER": "OpenRouter", "TRACEMEM_BUDGET_USD": "3.5",
                     "TRACEMEM_CACHE": "off", "TRACEMEM_CACHE_DIR": "elsewhere"})
    assert paid.inner.label == "openrouter"
    assert (str(paid.cache_dir), paid.budget_usd, paid.use_cache) == ("elsewhere", 3.5, False)
    assert paid.log_path.as_posix() == "cache/costs.jsonl"
    assert paid.describe() == {"cache": "elsewhere", "use_cache": False, "inner": paid.inner.describe()}
    local = from_env({**LOCAL, "TRACEMEM_BUDGET_USD": "3.5"})
    assert local.inner.label == "local" and local.inner.token_field == "max_tokens"
    assert local.budget_usd is None and local.use_cache is True
    sdk.create.assert_not_called()


def test_from_env_reads_the_process_environment_when_no_mapping_is_given(sdk, monkeypatch):
    monkeypatch.setenv("TRACEMEM_PROVIDER", "local")
    monkeypatch.setenv("TRACEMEM_RESOLVER_MODEL", "test-model")
    monkeypatch.setenv("TRACEMEM_LOCAL_BASE_URL", "http://192.0.2.10:11434/v1")
    monkeypatch.setenv("TRACEMEM_COST_LOG", "elsewhere/costs.jsonl")
    client = from_env()
    assert client.inner.base_url == "http://192.0.2.10:11434/v1"
    assert client.log_path.as_posix() == "elsewhere/costs.jsonl"


@pytest.mark.parametrize("provider", ["anthropic", "ollama", ""])
def test_from_env_rejects_an_unknown_provider_before_constructing_a_client(sdk, provider):
    with pytest.raises(ResolverConfigError, match="TRACEMEM_PROVIDER"):
        from_env({"TRACEMEM_PROVIDER": provider, "OPENAI_API_KEY": "synthetic-openai-key"})
    sdk.OpenAI.assert_not_called()


@pytest.mark.parametrize("model", ["anthropic/claude-sonnet-5", "anthropic/claude-haiku-5.5:free", "test-model"])
def test_openrouter_refuses_a_model_the_cap_cannot_price_before_constructing_a_client(sdk, model):
    with pytest.raises(ResolverConfigError, match="anthropic/claude-haiku-5.5, anthropic/claude-haiku-5.5:batch"):
        from_env({**ROUTER, "TRACEMEM_RESOLVER_MODEL": model})
    sdk.OpenAI.assert_not_called()


def test_openrouter_accepts_every_priced_model_and_needs_a_model(sdk):
    for model in model_client.PRICES_PER_MILLION:
        assert from_env({**ROUTER, "TRACEMEM_RESOLVER_MODEL": model}).inner.label == "openrouter"
    with pytest.raises(ResolverConfigError, match="TRACEMEM_RESOLVER_MODEL"):
        from_env({key: value for key, value in ROUTER.items() if key != "TRACEMEM_RESOLVER_MODEL"})
    # The default provider is unchanged: its calls stay unpriced and need no table entry.
    assert isinstance(from_env({"OPENAI_API_KEY": "synthetic-openai-key"}).inner, OpenAICompletionClient)


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
    monkeypatch.setenv("TRACEMEM_RESOLVER_MODEL", "test-model")
    local = comparison.make_client()
    assert isinstance(local, CachedClient) and isinstance(local.inner, OpenAICompatibleClient)
    assert local.inner.label == "local"
    sdk.create.assert_not_called()


def test_comparison_settings_record_the_provider_settings_but_not_the_cache_or_the_key(sdk, tmp_path):
    def settings(**environ):
        return comparison.comparison_settings(CONFIG, 12000, from_env(environ))

    base = settings(**LOCAL)
    assert base["model_client"] == {"label": "local", "base_url": "http://127.0.0.1:11434/v1",
                                    "extra_body": {"reasoning_effort": "none"}, "token_field": "max_tokens",
                                    "context_tokens": 16384, "model_digest": "synthetic-digest-1"}
    # Runs made with different local contexts are never reported together.
    assert settings(**LOCAL, TRACEMEM_LOCAL_CONTEXT_TOKENS="8192") != base
    assert settings(**LOCAL, TRACEMEM_CACHE="off", TRACEMEM_CACHE_DIR=str(tmp_path),
                    TRACEMEM_COST_LOG=str(tmp_path / "costs.jsonl")) == base
    assert settings(**LOCAL, TRACEMEM_LOCAL_THINKING="on") != base
    assert settings(**LOCAL, TRACEMEM_LOCAL_BASE_URL="http://192.0.2.7:11434/v1") != base
    # Nor are runs on other weights pulled under the same tag.
    sdk.digests["test-model"] = "synthetic-digest-3"
    assert settings(**LOCAL) != base
    router = settings(**ROUTER)
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
    first = run(lambda: cached(inner, tmp_path / "cache"))
    calls = inner.calls
    again = run(lambda: cached(inner, tmp_path / "cache"))
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


@pytest.mark.parametrize("system", ["tracemem-controlled", "similarity", "mem0-classic"])
def test_a_dead_local_server_aborts_the_run_instead_of_scoring_failed_answers(sdk, tmp_path, monkeypatch, system):
    if system == "mem0-classic":
        pytest.importorskip("mem0")
    monkeypatch.setattr(harness, "_git", lambda *args: None)
    scenario = Scenario.model_validate(minimal_dict())
    config = ResolverConfig(model="test-model", max_attempts=2)

    def run():
        spec = SystemSpec(system, lambda meta, gold: comparison.make_system(
            system, meta, config=config, client=cached(local_client({}, model="test-model"), tmp_path)),
            False, "offline outage test")
        return harness.run(spec, [scenario], "dev", condition="gold_candidates")

    sdk.create.side_effect = sdk.APIConnectionError("synthetic refusal")
    with pytest.raises(harness.RunAborted) as caught:
        run()
    assert caught.value.result.status == "failed"
    assert caught.value.result.failure["error_type"] == "FatalModelError"
    # The first refused call stops the run: nothing is retried, logged or saved.
    assert sdk.create.call_count == 1
    assert log_entries(tmp_path) == [] and saved_replies(tmp_path) == []
    # A server that only times out is retried, and the run completes with its failures recorded.
    sdk.create.side_effect = sdk.APITimeoutError("synthetic timeout")
    assert run().status == "completed"
    assert sdk.create.call_count > 2


# Several processes on one cost log (E's review of PR #6, finding 2)

HAIKU = CONFIG.model_copy(update={"model": "anthropic/claude-haiku-5.5", "max_completion_tokens": 1000})


class SlowClient(ScriptedClient):
    """A priced call that takes a while, so parallel callers overlap as A8's six runs do."""

    def __init__(self, delay):
        super().__init__()
        self.delay = delay

    def complete(self, *, config, messages, response_format):
        time.sleep(self.delay)
        return super().complete(config=config, messages=messages, response_format=response_format)


def test_parallel_clients_on_one_cost_log_stop_within_one_call_of_the_cap(tmp_path):
    # Six clients share one log and all start at once. Before the fix each read an empty log, saw room
    # under the cap and called, so six calls went out where the cap allowed one.
    log = tmp_path / "costs.jsonl"
    inner = SlowClient(delay=0.3)
    start = threading.Barrier(6)
    outcomes = []

    def one(n):
        client = CachedClient(inner, tmp_path / f"cache{n}", log_path=log, budget_usd=0.0003)
        start.wait()
        try:
            request(client, config=HAIKU)
            outcomes.append("called")
        except SpendingCapError:
            outcomes.append("capped")

    threads = [threading.Thread(target=one, args=(n,)) for n in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    # Each call costs US$0.0002 at the price table's rates and reserves its worst case, about US$0.0005,
    # before it goes out, so the first reservation already fills the US$0.0003 cap for the other five.
    assert sorted(outcomes) == ["called"] + ["capped"] * 5
    assert len(inner.calls) == 1
    spent, reserved = model_client.read_cost_log(log)
    assert spent == pytest.approx(0.0002) and reserved == 0.0


def test_an_unsettled_reservation_counts_until_it_expires(tmp_path):
    # A process that dies mid-call never settles its reservation; it keeps counting for a while, then expires.
    log = tmp_path / "costs.jsonl"
    log.write_text(json.dumps({"reservation": "crashed", "reserved_usd": 0.01, "reserved_at": time.time()}) + "\n",
                   encoding="utf-8")
    inner = ScriptedClient()
    with pytest.raises(SpendingCapError, match="reserved"):
        request(CachedClient(inner, tmp_path / "a", log_path=log, budget_usd=0.01), config=HAIKU)
    assert inner.calls == []
    stale = time.time() - model_client.RESERVATION_EXPIRY_SECONDS - 1
    log.write_text(json.dumps({"reservation": "crashed", "reserved_usd": 0.01, "reserved_at": stale}) + "\n",
                   encoding="utf-8")
    request(CachedClient(inner, tmp_path / "b", log_path=log, budget_usd=0.01), config=HAIKU)
    assert len(inner.calls) == 1


def test_a_finished_or_failed_call_leaves_no_reservation_open(tmp_path):
    log = tmp_path / "costs.jsonl"
    inner = ScriptedClient(RetryableModelError("synthetic outage"))
    cache = CachedClient(inner, tmp_path / "c", log_path=log, budget_usd=1.0)
    with pytest.raises(RetryableModelError):
        request(cache, config=HAIKU)
    assert model_client.read_cost_log(log) == (0.0, 0.0)
    request(cache, config=HAIKU)
    spent, reserved = model_client.read_cost_log(log)
    assert spent == pytest.approx(0.0002) and reserved == 0.0
    # Readers that only sum cost_usd, such as the spend checks in the run guide, see the same total.
    assert sum(entry.get("cost_usd") or 0.0 for entry in log_entries_at(log)) == pytest.approx(0.0002)


def test_a_lock_file_left_by_a_dead_process_does_not_block_paid_calls(tmp_path):
    log = tmp_path / "costs.jsonl"
    lock = tmp_path / "costs.jsonl.lock"
    lock.write_text("", encoding="utf-8")
    old = time.time() - model_client.STALE_LOCK_SECONDS - 60
    os.utime(lock, (old, old))
    inner = ScriptedClient()
    began = time.monotonic()
    request(CachedClient(inner, tmp_path / "d", log_path=log, budget_usd=1.0), config=HAIKU)
    assert len(inner.calls) == 1 and time.monotonic() - began < 2


def log_entries_at(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
