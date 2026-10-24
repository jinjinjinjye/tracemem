"""Model clients for a local OpenAI-compatible server and OpenRouter, with a reply cache.

Both targets speak the OpenAI Chat Completions API, so one adapter serves both; only
the endpoint, the key and a few provider-specific request fields differ. CachedClient
wraps any CompletionClient: a repeated request returns the saved reply at no cost,
and every completed call, saved or not, is appended to a usage and cost log.

Select the provider with TRACEMEM_PROVIDER (openai, the default, keeps the built-in
OpenAICompletionClient; openrouter; local, meaning an Ollama server). Only the
OpenRouter key is read from a local .env file, and only when it is absent from the
process environment. Once the cost log reaches TRACEMEM_BUDGET_USD (default 12), no
further provider call is made. Only priced calls count towards it: OpenRouter's
reported cost, else the price table below. Any other call, including every call
through the default openai provider, is logged as unpriced at zero, so the cap does
not limit its spending. The log covers this machine only, and local calls are never
capped.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Mapping

from tracemem.resolver import (
    CompletionClient, FatalModelError, ModelReply, OpenAICompletionClient, ResolverConfig,
    ResolverConfigError, RetryableModelError,
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LOCAL_BASE_URL = "http://127.0.0.1:11434/v1"  # Ollama's default port
DEFAULT_CACHE_DIR = "cache/llm"
DEFAULT_BUDGET_USD = 12.0
PROVIDERS = ("openai", "openrouter", "local")
# US dollars per million input / output tokens, used only when the provider reports
# no cost. Checked on OpenRouter's model list on 23 and 24 Oct 2026.
PRICES_PER_MILLION = {
    "anthropic/claude-haiku-5.5": (0.10, 0.50),
    "anthropic/claude-haiku-5.5:batch": (0.05, 0.25),
}


def read_dotenv(path: str | os.PathLike) -> dict[str, str]:
    """Parse KEY=VALUE lines without expanding anything.

    Blank lines, comment lines and lines without "=" are skipped, and a leading
    "export " is allowed. A quoted value is taken literally; an unquoted value ends
    at a "#" that follows whitespace. A byte-order mark is ignored.
    """
    values: dict[str, str] = {}
    try:
        lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return values
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw = line.split("=", 1)
        key = key.strip().removeprefix("export ").strip()
        value = raw.strip()
        if not key:
            continue
        end = value.find(value[0], 1) if value[:1] in ("'", '"') else -1
        # Cut the comment before stripping: in "KEY= # note" the "#" follows a space.
        values[key] = value[1:end] if end > 0 else re.split(r"\s#", raw, maxsplit=1)[0].strip()
    return values


def _switch(env: Mapping[str, str], name: str, default: str) -> bool:
    value = env.get(name, default).strip().lower()
    if value not in ("on", "off"):
        raise ResolverConfigError(f"{name} must be on or off")
    return value == "on"


class OpenAICompatibleClient:
    """Chat Completions against any compatible endpoint. SDK retries are disabled."""

    def __init__(self, *, base_url: str, api_key: str, extra_body: dict | None = None,
                 headers: dict[str, str] | None = None, label: str = "openai-compatible",
                 token_field: str = "max_completion_tokens"):
        try:
            import openai
        except ImportError:
            raise ResolverConfigError('Install the optional SDK with pip install -e ".[llm]"') from None
        if not api_key.strip():
            raise ResolverConfigError(f"No API key for the {label} client")
        self._sdk = openai
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url, max_retries=0,
                                     default_headers=headers or None)
        self.base_url = base_url
        self.extra_body = dict(extra_body or {})
        self.label = label
        # Ollama reads max_tokens and ignores max_completion_tokens.
        self.token_field = token_field
        self.last_cost: float | None = None

    def describe(self) -> dict:
        """Settings that change replies; part of the cache key, never the key itself."""
        return {"label": self.label, "base_url": self.base_url, "extra_body": self.extra_body,
                "token_field": self.token_field}

    def complete(self, *, config: ResolverConfig, messages: list[dict[str, str]],
                 response_format: dict) -> ModelReply:
        kwargs = dict(model=config.model, messages=messages, response_format=response_format,
                      timeout=config.timeout_seconds)
        kwargs[self.token_field] = config.max_completion_tokens
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        if self.extra_body:
            kwargs["extra_body"] = self.extra_body
        self.last_cost = None
        try:
            result = self._client.chat.completions.create(**kwargs)
        except self._sdk.APIConnectionError:
            raise RetryableModelError("provider connection or timeout failure") from None
        except self._sdk.APIStatusError as error:
            code = error.status_code
            if code in (408, 409, 429) or code >= 500:
                raise RetryableModelError(f"transient provider status {code}") from None
            raise FatalModelError(f"provider rejected the request (status {code}); check credentials and model settings") from None
        if not result.choices:
            raise RetryableModelError("provider returned no completion")
        choice = result.choices[0]
        usage = result.usage
        cost = getattr(usage, "cost", None) if usage else None
        self.last_cost = float(cost) if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None
        return ModelReply(
            content=choice.message.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            finish_reason=choice.finish_reason,
            refused=bool(getattr(choice.message, "refusal", None)),
        )


def local_client(environ: Mapping[str, str] | None = None) -> OpenAICompatibleClient:
    """An Ollama server; thinking is off unless TRACEMEM_LOCAL_THINKING=on."""
    env = os.environ if environ is None else environ
    thinking = _switch(env, "TRACEMEM_LOCAL_THINKING", "off")
    # reasoning_effort "none" is how Ollama's OpenAI endpoint turns thinking off.
    extra = {} if thinking else {"reasoning_effort": "none"}
    return OpenAICompatibleClient(
        base_url=env.get("TRACEMEM_LOCAL_BASE_URL", "").strip() or LOCAL_BASE_URL,
        # Ollama ignores the key; a server that checks one can be given it here.
        api_key=env.get("TRACEMEM_LOCAL_API_KEY", "").strip() or "local",
        extra_body=extra, label="local", token_field="max_tokens")


def openrouter_client(environ: Mapping[str, str] | None = None,
                      dotenv_path: str | os.PathLike = ".env") -> OpenAICompatibleClient:
    """OpenRouter, routed only to endpoints that honour every request parameter."""
    env = os.environ if environ is None else environ
    key = (env.get("OPENROUTER_API_KEY") or "").strip() \
        or read_dotenv(dotenv_path).get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise ResolverConfigError("Set OPENROUTER_API_KEY in the environment or in .env")
    return OpenAICompatibleClient(
        base_url=OPENROUTER_BASE_URL, api_key=key,
        # Structured outputs vary by endpoint; without this a request could reach
        # one that ignores response_format.
        extra_body={"provider": {"require_parameters": True}},
        headers={"X-Title": "TraceMem"}, label="openrouter")


def _price(model: str, reply: ModelReply) -> float | None:
    if model not in PRICES_PER_MILLION:
        return None
    rate_in, rate_out = PRICES_PER_MILLION[model]
    return (reply.input_tokens * rate_in + reply.output_tokens * rate_out) / 1e6


class SpendingCapError(FatalModelError):
    """The cost log has reached the spending cap; no paid call is made."""


class CachedClient:
    """Return a saved reply for a repeated request; log every completed call with its cost.

    The key covers the provider settings, the model settings and the full request.
    Saved replies are returned with zero tokens, because the provider is not called
    and nothing is charged; their original counts stay in the cache file and the log.
    Only complete replies are saved: a provider error, a refusal or a cut-off reply
    is not, so retrying the same request asks the provider again. A request that
    repeats one this client has already served or saved, such as a retry that
    resends the same feedback after a complete but invalid reply, gets its own
    numbered slot in the cache. It therefore reaches the provider, as it would
    without the cache, and a later run replays the slots in the same order. With
    use_cache=False nothing is read or saved, but calls are still logged and the
    spending cap still applies. The cap is checked before each provider call against
    every cost in the log, so a run stops within one call of the cap. A cost is the
    provider's own figure, else the price table's; a model in neither is logged at
    zero as "unpriced" and does not count towards the cap.
    """

    def __init__(self, inner: CompletionClient, cache_dir: str | os.PathLike = DEFAULT_CACHE_DIR,
                 log_path: str | os.PathLike | None = None, budget_usd: float | None = DEFAULT_BUDGET_USD,
                 use_cache: bool = True):
        self.inner = inner
        self.cache_dir = Path(cache_dir)
        self.log_path = Path(log_path) if log_path is not None else self.cache_dir / "calls.jsonl"
        self.budget_usd = budget_usd
        self.use_cache = use_cache
        self.spent_usd = self._logged_spend()
        self.stats = {"calls": 0, "hits": 0, "misses": 0, "cost_usd": 0.0}
        # Request key -> slots this client has served or saved; the next repeat uses the next slot.
        self._slots: dict[str, int] = {}

    def _logged_spend(self) -> float:
        total = 0.0
        try:
            lines = self.log_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return total
        for line in lines:
            try:
                total += float(json.loads(line).get("cost_usd") or 0.0)
            except (ValueError, TypeError, AttributeError):
                continue
        return total

    def describe(self) -> dict:
        inner = getattr(self.inner, "describe", None)
        return {"cache": str(self.cache_dir), "use_cache": self.use_cache,
                "inner": inner() if callable(inner) else type(self.inner).__name__}

    def key(self, *, config: ResolverConfig, messages: list[dict[str, str]], response_format: dict,
            slot: int = 0) -> str:
        inner = getattr(self.inner, "describe", None)
        material = {"client": inner() if callable(inner) else type(self.inner).__name__,
                    # Timeouts and retry counts never change a reply.
                    "config": {k: v for k, v in config.model_dump().items()
                               if k not in ("timeout_seconds", "max_attempts")},
                    "messages": messages, "response_format": response_format}
        if slot:
            # Slot 0 keeps the plain key, so replies saved before slots existed still match.
            material["repeat"] = slot
        return hashlib.sha256(json.dumps(material, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    def _path(self, key: str) -> Path:
        return self.cache_dir / key[:2] / f"{key}.json"

    def _read(self, path: Path) -> dict | None:
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        # A malformed file is a miss; the next complete reply replaces it.
        if not isinstance(saved, dict) or not {"content", "finish_reason", "refused"} <= saved.keys():
            return None
        return saved

    def complete(self, *, config: ResolverConfig, messages: list[dict[str, str]],
                 response_format: dict) -> ModelReply:
        request = self.key(config=config, messages=messages, response_format=response_format)
        slot = self._slots.get(request, 0)
        key = self.key(config=config, messages=messages, response_format=response_format, slot=slot) \
            if slot else request
        path = self._path(key)
        self.stats["calls"] += 1
        started = time.monotonic()
        saved = self._read(path) if self.use_cache else None
        if saved is not None:
            self._slots[request] = slot + 1
            self.stats["hits"] += 1
            reply = ModelReply(content=saved["content"], finish_reason=saved["finish_reason"],
                               refused=saved["refused"])
            self._log(key, config.model, True, saved, 0.0, "cache", time.monotonic() - started)
            return reply
        if self.budget_usd is not None and self.spent_usd >= self.budget_usd:
            raise SpendingCapError(f"spending cap of US${self.budget_usd:.2f} reached "
                                   f"(US${self.spent_usd:.4f} logged in {self.log_path})")
        reply = self.inner.complete(config=config, messages=messages, response_format=response_format)
        reported = getattr(self.inner, "last_cost", None)
        priced = _price(config.model, reply)
        if isinstance(reported, float):
            cost, source = reported, "provider"
        elif priced is not None:
            cost, source = priced, "price_table"
        else:
            cost, source = 0.0, "unpriced"
        record = {"content": reply.content, "finish_reason": reply.finish_reason, "refused": reply.refused,
                  "input_tokens": reply.input_tokens, "output_tokens": reply.output_tokens,
                  "cost_usd": cost, "cost_source": source, "model": config.model}
        if self.use_cache and reply.finish_reason == "stop" and not reply.refused:
            self._write(path, record)
            self._slots[request] = slot + 1
        self.stats["misses"] += 1
        self.stats["cost_usd"] += cost
        self.spent_usd += cost
        self._log(key, config.model, False, record, cost, source, time.monotonic() - started)
        return reply

    def _write(self, path: Path, record: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write then rename, so an interrupted run never leaves a half-written reply.
        handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False)
        os.replace(temporary, path)

    def _log(self, key: str, model: str, hit: bool, record: dict, cost: float, source: str,
             seconds: float) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "key": key, "model": model, "cache_hit": hit,
                 "input_tokens": record.get("input_tokens", 0), "output_tokens": record.get("output_tokens", 0),
                 "finish_reason": record.get("finish_reason"), "cost_usd": cost, "cost_source": source,
                 "seconds": round(seconds, 3)}
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry) + "\n")


def from_env(environ: Mapping[str, str] | None = None) -> CompletionClient:
    """The client named by TRACEMEM_PROVIDER, cached unless TRACEMEM_CACHE=off.

    Every setting is checked before any client is constructed. The cap at
    TRACEMEM_BUDGET_USD counts only priced calls (see CachedClient), so it does not
    limit spending through the default openai provider. A local server charges
    nothing, so spending logged for a paid provider never stops it.
    """
    env = os.environ if environ is None else environ
    provider = env.get("TRACEMEM_PROVIDER", "openai").strip().lower()
    if provider not in PROVIDERS:
        raise ResolverConfigError("TRACEMEM_PROVIDER must be openai, openrouter or local")
    try:
        budget = float(env.get("TRACEMEM_BUDGET_USD", DEFAULT_BUDGET_USD))
        if not math.isfinite(budget) or budget < 0:
            raise ValueError
    except ValueError:
        raise ResolverConfigError("TRACEMEM_BUDGET_USD must be a non-negative number of US dollars") from None
    use_cache = _switch(env, "TRACEMEM_CACHE", "on")
    cache_dir = env.get("TRACEMEM_CACHE_DIR", "").strip() or DEFAULT_CACHE_DIR
    if provider == "openai":
        client: CompletionClient = OpenAICompletionClient(api_key=env.get("OPENAI_API_KEY"))
    elif provider == "openrouter":
        client = openrouter_client(env)
    else:
        client = local_client(env)
    return CachedClient(client, cache_dir, budget_usd=None if provider == "local" else budget,
                        use_cache=use_cache)
