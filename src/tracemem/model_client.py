"""Model clients for a local OpenAI-compatible server and OpenRouter, with a reply cache.

Both targets speak the OpenAI Chat Completions API, so one adapter serves both; only
the endpoint, the key and a few provider-specific request fields differ. CachedClient
wraps any CompletionClient: a repeated request returns the saved reply at no cost,
and every completed call, saved or not, is appended to a usage and cost log.

Select the provider with TRACEMEM_PROVIDER (openai, the default, keeps the built-in
OpenAICompletionClient; openrouter; local, meaning an Ollama server). Only the
OpenRouter key is read from a local .env file, and only when it is absent from the
process environment. Once the cost log reaches TRACEMEM_BUDGET_USD (default 12), no
further provider call is made. The cost log is TRACEMEM_COST_LOG (default
cache/costs.jsonl), never inside a reply cache folder, and its total is read again
before every paid call, so fresh cache folders and runs going on at the same time
share one cap. Only priced calls count towards it: OpenRouter's reported cost, else
the price table below. OpenRouter therefore accepts only a model in the price table.
Any other call, including every call through the default openai provider, is logged
as unpriced at zero, so the cap does not limit its spending. The log covers this
machine only, and local calls are never capped.

A local server that gives the model a shorter context than a request needs does not
refuse it: Ollama cuts the request from the front and answers anyway. The local
client therefore records the context the server must give the model
(TRACEMEM_LOCAL_CONTEXT_TOKENS, default 16,384), and after every reply checks it
against the length the server reports in /api/ps, and the tokens the server read
against the size of the request. Either mismatch stops the run before the reply can
be saved. A tag such as qwen3.5:4b can be pulled again with new weights, so the local
client also records the digest the server lists for the model in /api/tags. A local
server that refuses or drops the connection is down, so the run stops instead of
scoring the remaining questions as failed answers; a timeout is still retried.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import os
import re
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Mapping

from tracemem.resolver import (
    CompletionClient, FatalModelError, ModelReply, OpenAICompletionClient, ResolverConfig,
    ResolverConfigError, RetryableModelError,
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LOCAL_BASE_URL = "http://127.0.0.1:11434/v1"  # Ollama's default port
DEFAULT_CACHE_DIR = "cache/llm"
# Outside every reply cache folder, so a fresh folder never resets the spending.
DEFAULT_COST_LOG = "cache/costs.jsonl"
DEFAULT_BUDGET_USD = 12.0
PROVIDERS = ("openai", "openrouter", "local")
DEFAULT_LOCAL_CONTEXT_TOKENS = 16384
# Text and JSON take about four UTF-8 bytes per token: 4.0 to 4.6 in the pilot-01
# requests of 25 Oct 2026. A server that read fewer tokens than one per six bytes
# sent has cut the request.
MAX_BYTES_PER_TOKEN = 6
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


def _server_models(base_url: str, endpoint: str, what: str, timeout_seconds: float) -> list:
    """The model entries an Ollama server lists at endpoint; FatalModelError if unreadable."""
    root = base_url.rstrip("/").removesuffix("/v1")
    if not root.startswith(("http://", "https://")):
        raise FatalModelError("the local server address must start with http:// or https://")
    try:
        with urllib.request.urlopen(root + endpoint, timeout=timeout_seconds) as response:
            listing = json.load(response)
    except (OSError, ValueError):
        raise FatalModelError(f"could not read the {what} models from the local server's {endpoint}; "
                              "the local provider needs an Ollama server") from None
    entries = listing.get("models") if isinstance(listing, dict) else None
    return [entry for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []


def _entry(entries: list, model: str) -> dict | None:
    names = {model} if ":" in model else {model, model + ":latest"}
    return next((entry for entry in entries if entry.get("name") in names or entry.get("model") in names), None)


def server_context_length(base_url: str, model: str, timeout_seconds: float = 10.0) -> int | None:
    """The context length an Ollama server reports in /api/ps for a loaded model.

    None when the model is not loaded or no length is reported. An unreachable
    server, or one without Ollama's /api/ps, stops the run with FatalModelError.
    """
    entry = _entry(_server_models(base_url, "/api/ps", "loaded", timeout_seconds), model)
    length = entry.get("context_length") if entry is not None else None
    return length if isinstance(length, int) and not isinstance(length, bool) else None


def model_digest(base_url: str, model: str, timeout_seconds: float = 10.0) -> str:
    """The digest an Ollama server lists in /api/tags for an installed model.

    /api/tags lists installed models without loading them. A model that is not
    installed is a ResolverConfigError; an unreachable server, one without Ollama's
    /api/tags, or a listing without a digest stops the run with FatalModelError.
    """
    entry = _entry(_server_models(base_url, "/api/tags", "installed", timeout_seconds), model)
    if entry is None:
        raise ResolverConfigError(f"the local server has no model {model}; pull it with ollama pull {model}")
    digest = entry.get("digest")
    if not isinstance(digest, str) or not digest.strip():
        raise FatalModelError(f"the local server lists no digest for {model} in /api/tags, "
                              "so its weights cannot be identified")
    return digest.strip()


def _switch(env: Mapping[str, str], name: str, default: str) -> bool:
    value = env.get(name, default).strip().lower()
    if value not in ("on", "off"):
        raise ResolverConfigError(f"{name} must be on or off")
    return value == "on"


class OpenAICompatibleClient:
    """Chat Completions against any compatible endpoint. SDK retries are disabled."""

    def __init__(self, *, base_url: str, api_key: str, extra_body: dict | None = None,
                 headers: dict[str, str] | None = None, label: str = "openai-compatible",
                 token_field: str = "max_completion_tokens", context_tokens: int | None = None,
                 model: str | None = None, model_digest: str | None = None, connection_fatal: bool = False):
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
        # When set, the context the server must give the model, checked after every reply.
        self.context_tokens = context_tokens
        # When set, the only model this client calls, and the digest of its weights.
        self.model = model
        self.model_digest = model_digest
        # A local server that refuses or drops the connection is down, not busy.
        self.connection_fatal = connection_fatal
        self.last_cost: float | None = None

    def describe(self) -> dict:
        """Settings that change replies; part of the cache key, never the key itself."""
        settings = {"label": self.label, "base_url": self.base_url, "extra_body": self.extra_body,
                    "token_field": self.token_field}
        if self.context_tokens is not None:
            # A shorter context cuts long requests, so it changes replies.
            settings["context_tokens"] = self.context_tokens
        if self.model_digest is not None:
            # The same tag pulled again can name other weights, which change replies.
            settings["model_digest"] = self.model_digest
        return settings

    def _check_context(self, model: str, messages: list[dict[str, str]], usage) -> None:
        """Stop the run unless the server gave the model the recorded context and read the whole request."""
        served = server_context_length(self.base_url, model)
        if served is None:
            raise FatalModelError(f"the local server reports no context length for {model} in /api/ps, "
                                  "so a cut request could not be detected")
        if served != self.context_tokens:
            raise FatalModelError(f"the local server gives {model} a {served}-token context, but "
                                  f"TRACEMEM_LOCAL_CONTEXT_TOKENS is {self.context_tokens}; start the server "
                                  "with OLLAMA_CONTEXT_LENGTH set to the same number (docs/local-model.md)")
        sent = sum(len(str(message.get("content") or "").encode("utf-8")) for message in messages)
        read = getattr(usage, "prompt_tokens", None)
        if isinstance(read, int) and read * MAX_BYTES_PER_TOKEN < sent:
            raise FatalModelError(f"the local server read {read} tokens of a {sent}-byte request, so it cut "
                                  "the request; give the model a longer context (docs/local-model.md)")

    def complete(self, *, config: ResolverConfig, messages: list[dict[str, str]],
                 response_format: dict) -> ModelReply:
        if self.model is not None and config.model != self.model:
            # The recorded digest belongs to self.model; another model's replies would carry it.
            raise FatalModelError(f"this client identified the model {self.model}, not {config.model}; "
                                  "build one client for each model")
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
        except self._sdk.APITimeoutError:
            # A slow reply is retried; APITimeoutError is a kind of APIConnectionError.
            raise RetryableModelError("provider connection or timeout failure") from None
        except self._sdk.APIConnectionError:
            if self.connection_fatal:
                raise FatalModelError(f"the {self.label} model server at {self.base_url} refused or dropped "
                                      "the connection; check that it is running (docs/local-model.md)") from None
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
        if self.context_tokens is not None:
            self._check_context(config.model, messages, usage)
        cost = getattr(usage, "cost", None) if usage else None
        self.last_cost = float(cost) if isinstance(cost, (int, float)) and not isinstance(cost, bool) else None
        return ModelReply(
            content=choice.message.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            finish_reason=choice.finish_reason,
            refused=bool(getattr(choice.message, "refusal", None)),
        )


def local_client(environ: Mapping[str, str] | None = None, model: str | None = None) -> OpenAICompatibleClient:
    """An Ollama server; thinking is off unless TRACEMEM_LOCAL_THINKING=on.

    The server must give the model the context of TRACEMEM_LOCAL_CONTEXT_TOKENS.
    Given a model, as from_env always gives one, the client calls only that model
    and records the digest the server lists for it, so a reply saved from other
    weights under the same tag is never replayed, and runs on different weights
    are never reported together. A refused or dropped connection stops the run.
    """
    env = os.environ if environ is None else environ
    thinking = _switch(env, "TRACEMEM_LOCAL_THINKING", "off")
    raw = env.get("TRACEMEM_LOCAL_CONTEXT_TOKENS", "").strip()
    try:
        context = int(raw) if raw else DEFAULT_LOCAL_CONTEXT_TOKENS
        if context < 1:
            raise ValueError
    except ValueError:
        raise ResolverConfigError("TRACEMEM_LOCAL_CONTEXT_TOKENS must be a positive whole number of tokens") from None
    base_url = env.get("TRACEMEM_LOCAL_BASE_URL", "").strip() or LOCAL_BASE_URL
    digest = model_digest(base_url, model) if model is not None else None
    # reasoning_effort "none" is how Ollama's OpenAI endpoint turns thinking off.
    extra = {} if thinking else {"reasoning_effort": "none"}
    return OpenAICompatibleClient(
        base_url=base_url,
        # Ollama ignores the key; a server that checks one can be given it here.
        api_key=env.get("TRACEMEM_LOCAL_API_KEY", "").strip() or "local",
        extra_body=extra, label="local", token_field="max_tokens", context_tokens=context,
        model=model, model_digest=digest, connection_fatal=True)


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
    spending cap still applies. The cost log is log_path, by default DEFAULT_COST_LOG,
    and never depends on the cache folder. Before each provider call under a cap, the
    log's total is read again, so other clients and other processes writing to the
    same log are counted and a run stops within one call of the cap. A paid call is
    logged before its reply is saved, so a reply that cannot be saved is still counted.
    A cost is the provider's own figure, else the price table's; a model in neither is
    logged at zero as "unpriced" and does not count towards the cap.
    """

    def __init__(self, inner: CompletionClient, cache_dir: str | os.PathLike = DEFAULT_CACHE_DIR,
                 log_path: str | os.PathLike | None = None, budget_usd: float | None = DEFAULT_BUDGET_USD,
                 use_cache: bool = True):
        self.inner = inner
        self.cache_dir = Path(cache_dir)
        self.log_path = Path(log_path if log_path is not None else DEFAULT_COST_LOG)
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
        if self.budget_usd is not None:
            # Read the whole log again: another run, or another client of this one, may have spent since.
            self.spent_usd = self._logged_spend()
            if self.spent_usd >= self.budget_usd:
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
        self.stats["misses"] += 1
        self.stats["cost_usd"] += cost
        self.spent_usd += cost
        # Log before saving: the call is paid for even if its reply cannot be saved.
        self._log(key, config.model, False, record, cost, source, time.monotonic() - started)
        if self.use_cache and reply.finish_reason == "stop" and not reply.refused:
            self._write(path, record)
            self._slots[request] = slot + 1
        return reply

    def _write(self, path: Path, record: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write then rename, so an interrupted run never leaves a half-written reply.
        handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                json.dump(record, stream, ensure_ascii=False)
            os.replace(temporary, path)
        except BaseException:
            # A failed save leaves no temporary file behind.
            with contextlib.suppress(OSError):
                os.unlink(temporary)
            raise

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
    limit spending through the default openai provider. OpenRouter accepts only a
    model of TRACEMEM_RESOLVER_MODEL in the price table, so a call whose cost the
    provider omits is still counted. The local client identifies that model by the
    digest its server lists. A local server charges nothing, so spending logged for
    a paid provider never stops it. The cost log is TRACEMEM_COST_LOG, whatever
    TRACEMEM_CACHE_DIR is.
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
    cost_log = env.get("TRACEMEM_COST_LOG", "").strip() or DEFAULT_COST_LOG
    if provider == "openai":
        client: CompletionClient = OpenAICompletionClient(api_key=env.get("OPENAI_API_KEY"))
    elif provider == "openrouter":
        if ResolverConfig.from_env(env).model not in PRICES_PER_MILLION:
            raise ResolverConfigError("with TRACEMEM_PROVIDER=openrouter, TRACEMEM_RESOLVER_MODEL must be one of "
                                      f"{', '.join(PRICES_PER_MILLION)}, the models the spending cap can price "
                                      "(PRICES_PER_MILLION in src/tracemem/model_client.py)")
        client = openrouter_client(env)
    else:
        client = local_client(env, model=ResolverConfig.from_env(env).model)
    return CachedClient(client, cache_dir, log_path=cost_log, budget_usd=None if provider == "local" else budget,
                        use_cache=use_cache)
