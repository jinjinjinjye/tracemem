"""Offline checks of the optional OpenAI adapter, without importing the SDK.

The fake module exposes only the SDK surface consumed by the adapter. These
tests also run with the dev extra alone; no key, network, or SDK is required.
"""

from __future__ import annotations

import sys
import traceback
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from tracemem.resolver import (
    FatalModelError,
    LLMResolver,
    ModelReply,
    OpenAICompletionClient,
    ResolverConfig,
    ResolverConfigError,
    RetryableModelError,
)


def completion(*, content='{"op": "ADD"}', refusal=None, finish_reason="stop", usage=True):
    return SimpleNamespace(
        choices=[SimpleNamespace(
            message=SimpleNamespace(content=content, refusal=refusal),
            finish_reason=finish_reason,
        )],
        usage=SimpleNamespace(prompt_tokens=17, completion_tokens=9) if usage else None,
    )


@pytest.fixture
def sdk(monkeypatch):
    """Replace the entire SDK so an installed OpenAI package is never needed."""
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
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return module


def request(client, **config_overrides):
    return client.complete(
        config=ResolverConfig(model="test-model", **config_overrides),
        messages=[{"role": "user", "content": "synthetic evidence"}],
        response_format={"type": "json_schema", "json_schema": {"name": "test"}},
    )


@pytest.mark.parametrize("api_key", [None, "", " \t"])
def test_adapter_rejects_missing_or_blank_key_before_creating_client(sdk, api_key):
    with pytest.raises(ResolverConfigError, match="OPENAI_API_KEY"):
        OpenAICompletionClient(api_key=api_key)
    sdk.OpenAI.assert_not_called()
    sdk.create.assert_not_called()


def test_adapter_missing_sdk_has_actionable_optional_dependency_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "openai", None)
    with pytest.raises(ResolverConfigError, match=r"\[llm\]"):
        OpenAICompletionClient(api_key="synthetic-test-key")


@pytest.mark.parametrize("explicit_key", [None, "explicit-synthetic-key"])
def test_adapter_uses_explicit_or_environment_key_and_disables_sdk_retries(sdk, monkeypatch, explicit_key):
    monkeypatch.setenv("OPENAI_API_KEY", "environment-synthetic-key")
    # A machine-wide SDK base URL must not redirect this adapter's requests.
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid/unrelated-endpoint")
    OpenAICompletionClient(api_key=explicit_key)
    sdk.OpenAI.assert_called_once_with(
        api_key=explicit_key or "environment-synthetic-key",
        base_url="https://api.openai.com/v1",
        max_retries=0,
    )
    sdk.create.assert_not_called()


def test_adapter_forwards_request_settings_without_default_temperature(sdk):
    client = OpenAICompletionClient(api_key="synthetic-test-key")
    messages = [{"role": "user", "content": "synthetic evidence"}]
    response_format = {"type": "json_schema", "json_schema": {"name": "test"}}
    config = ResolverConfig(model="test-model", timeout_seconds=4.5, max_completion_tokens=73)
    result = client.complete(config=config, messages=messages, response_format=response_format)
    sdk.create.assert_called_once_with(
        model="test-model", messages=messages, response_format=response_format,
        timeout=4.5, max_completion_tokens=73,
    )
    assert result == ModelReply(content='{"op": "ADD"}', input_tokens=17, output_tokens=9)


@pytest.mark.parametrize("temperature", [0.0, 0.4])
def test_adapter_forwards_temperature_only_when_configured(sdk, temperature):
    request(OpenAICompletionClient(api_key="synthetic-test-key"), temperature=temperature)
    assert sdk.create.call_args.kwargs["temperature"] == temperature


@pytest.mark.parametrize(
    ("body", "refusal", "finish_reason", "expected_body", "expected_refused"),
    [
        ('{"op": "ADD"}', None, "stop", '{"op": "ADD"}', False),
        (None, "Unable to comply", "stop", "", True),
        (None, None, "stop", "", False),
        ('{"op":', None, "length", '{"op":', False),
        (None, None, "content_filter", "", False),
    ],
)
def test_adapter_preserves_body_refusal_and_completion_status(
    sdk, body, refusal, finish_reason, expected_body, expected_refused,
):
    sdk.create.return_value = completion(content=body, refusal=refusal, finish_reason=finish_reason)
    reply = request(OpenAICompletionClient(api_key="synthetic-test-key"))
    assert reply == ModelReply(
        content=expected_body, input_tokens=17, output_tokens=9,
        finish_reason=finish_reason, refused=expected_refused,
    )


def test_adapter_missing_usage_defaults_to_zero(sdk):
    sdk.create.return_value = completion(usage=False)
    reply = request(OpenAICompletionClient(api_key="synthetic-test-key"))
    assert (reply.input_tokens, reply.output_tokens) == (0, 0)


def test_adapter_empty_choices_is_retryable(sdk):
    sdk.create.return_value = SimpleNamespace(choices=[], usage=None)
    with pytest.raises(RetryableModelError, match="no completion"):
        request(OpenAICompletionClient(api_key="synthetic-test-key"))
    assert sdk.create.call_count == 1


@pytest.mark.parametrize("exception_name", ["APIConnectionError", "APITimeoutError"])
def test_adapter_connection_and_timeout_errors_are_retryable_and_sanitized(sdk, exception_name):
    raw_provider_detail = "synthetic-private-provider-body"
    sdk.create.side_effect = getattr(sdk, exception_name)(raw_provider_detail)
    with pytest.raises(RetryableModelError, match="connection or timeout") as exc:
        request(OpenAICompletionClient(api_key="synthetic-test-key"))
    assert raw_provider_detail not in str(exc.value)
    assert raw_provider_detail not in "".join(traceback.format_exception(exc.value))
    assert sdk.create.call_count == 1


@pytest.mark.parametrize("status_code", [408, 409, 429, 500, 502, 503, 599])
def test_adapter_transient_statuses_are_retryable_and_sanitized(sdk, status_code):
    raw_provider_detail = "synthetic-private-provider-body"
    sdk.create.side_effect = sdk.APIStatusError(status_code, raw_provider_detail)
    with pytest.raises(RetryableModelError, match=str(status_code)) as exc:
        request(OpenAICompletionClient(api_key="synthetic-test-key"))
    assert raw_provider_detail not in str(exc.value)
    assert raw_provider_detail not in "".join(traceback.format_exception(exc.value))
    assert sdk.create.call_count == 1


@pytest.mark.parametrize("status_code", [400, 401, 403, 404, 422])
def test_adapter_nontransient_statuses_are_fatal_and_sanitized(sdk, status_code):
    raw_provider_detail = "synthetic-private-provider-body"
    sdk.create.side_effect = sdk.APIStatusError(status_code, raw_provider_detail)
    with pytest.raises(FatalModelError, match=str(status_code)) as exc:
        request(OpenAICompletionClient(api_key="synthetic-test-key"))
    assert raw_provider_detail not in str(exc.value)
    assert raw_provider_detail not in "".join(traceback.format_exception(exc.value))
    assert sdk.create.call_count == 1


def test_from_env_builds_resolver_without_calling_model_or_retaining_key_in_description(sdk, monkeypatch):
    for key in (
        "TRACEMEM_RESOLVER_MODEL", "TRACEMEM_RESOLVER_TIMEOUT_SECONDS",
        "TRACEMEM_RESOLVER_MAX_ATTEMPTS", "TRACEMEM_RESOLVER_MAX_COMPLETION_TOKENS",
        "TRACEMEM_RESOLVER_TEMPERATURE",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("TRACEMEM_RESOLVER_MODEL", "test-model")
    monkeypatch.setenv("TRACEMEM_RESOLVER_TIMEOUT_SECONDS", "7.5")
    monkeypatch.setenv("TRACEMEM_RESOLVER_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("TRACEMEM_RESOLVER_MAX_COMPLETION_TOKENS", "256")
    resolver = LLMResolver.from_env()
    assert resolver.config == ResolverConfig(
        model="test-model", timeout_seconds=7.5, max_attempts=3, max_completion_tokens=256,
    )
    assert isinstance(resolver.client, OpenAICompletionClient)
    assert resolver.usage().calls == 0
    sdk.create.assert_not_called()
    assert "synthetic-test-key" not in str(resolver.describe())


def test_from_env_invalid_model_settings_fail_before_constructing_client(sdk, monkeypatch):
    monkeypatch.delenv("TRACEMEM_RESOLVER_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    with pytest.raises(ResolverConfigError, match="TRACEMEM_RESOLVER_MODEL"):
        LLMResolver.from_env()
    sdk.OpenAI.assert_not_called()
    sdk.create.assert_not_called()
