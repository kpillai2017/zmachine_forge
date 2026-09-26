"""One swappable LLM interface for every agent (proforma Section 3).

    provider = get_provider()             # ZB_PROVIDER or the fallback order
    text = provider.complete(system, user)

Fallback order: rovodev -> anthropic -> openai(-compatible) -> gemini ->
ollama -> brief. "brief" is the OFFLINE mode: it never calls a model;
agents detect it and write task briefs for a human (or Rovo Dev in your
editor) to implement instead.

Standard library only (urllib), so zbuilder installs nothing extra.
Keys come from the environment and are never logged.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request


class ProviderError(Exception):
    pass


def _post_json(url: str, payload: dict, headers: dict, timeout: float = 180.0) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as exc:
        raise ProviderError(f"HTTP {exc.code} from {url.split('?')[0]}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderError(f"cannot reach {url.split('?')[0]}: {exc}") from exc


class Provider:
    name = "base"
    offline = False

    def available(self) -> bool:
        raise NotImplementedError

    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class RovoDevProvider(Provider):
    """`acli rovodev serve PORT --disable-session-token`: POST /v2/chat
    streams Server-Sent Events. No system role, so the system prompt is
    prepended. HTTP 409 = busy -> retry with backoff."""
    name = "rovodev"

    def __init__(self):
        self.url = os.environ.get("ROVODEV_SERVE_URL", "").rstrip("/")

    def available(self) -> bool:
        if not self.url:
            return False
        try:
            with urllib.request.urlopen(f"{self.url}/healthcheck", timeout=3) as r:
                return json.loads(r.read().decode()).get("status") == "healthy"
        except Exception:
            return False

    def complete(self, system: str, user: str) -> str:
        message = f"{system}\n\n---\n\n{user}"
        for attempt in range(1, 6):
            try:
                return self._once(message)
            except urllib.error.HTTPError as exc:
                if exc.code == 409 and attempt < 5:
                    time.sleep(0.75 * attempt)
                    continue
                raise ProviderError(f"Rovo Dev serve returned HTTP {exc.code}") from exc
        raise ProviderError("Rovo Dev serve stayed busy")

    def _once(self, message: str) -> str:
        req = urllib.request.Request(f"{self.url}/v2/chat",
                                     data=json.dumps({"message": message}).encode(),
                                     headers={"Content-Type": "application/json"})
        parts: list[str] = []
        with urllib.request.urlopen(req, timeout=600) as r:
            event = None
            for raw in r:
                line = raw.decode("utf-8", "replace").rstrip("\n")
                if not line:
                    event = None
                elif line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("data:"):
                    try:
                        data = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
                    if event == "part_start" and data.get("part", {}).get("part_kind") == "text":
                        parts.append(data["part"].get("content", "") or "")
                    elif event == "part_delta" and \
                            data.get("delta", {}).get("part_delta_kind") == "text":
                        parts.append(data["delta"].get("content_delta", "") or "")
        return "".join(parts)


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self):
        self.key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = os.environ.get("ZB_MODEL", "claude-sonnet-4-5")

    def available(self) -> bool:
        return bool(self.key)

    def complete(self, system: str, user: str) -> str:
        data = _post_json("https://api.anthropic.com/v1/messages",
                          {"model": self.model, "max_tokens": 8000, "system": system,
                           "messages": [{"role": "user", "content": user}]},
                          {"x-api-key": self.key, "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in data.get("content", []))


class OpenAICompatibleProvider(Provider):
    name = "openai"

    def __init__(self, key_env="OPENAI_API_KEY", base_env="OPENAI_BASE_URL",
                 default_base="https://api.openai.com/v1", default_model="gpt-4o"):
        self.key = os.environ.get(key_env, "")
        self.base = os.environ.get(base_env, "") or default_base
        self.model = os.environ.get("ZB_MODEL", default_model)

    def available(self) -> bool:
        return bool(self.key)

    def complete(self, system: str, user: str) -> str:
        data = _post_json(self.base.rstrip("/") + "/chat/completions",
                          {"model": self.model, "messages": [
                              {"role": "system", "content": system},
                              {"role": "user", "content": user}]},
                          {"Authorization": f"Bearer {self.key}"})
        return data["choices"][0]["message"]["content"]


class GeminiProvider(OpenAICompatibleProvider):
    name = "gemini"

    def __init__(self):
        super().__init__("GEMINI_API_KEY", "GEMINI_BASE_URL",
                         "https://generativelanguage.googleapis.com/v1beta/openai",
                         "gemini-2.5-pro")


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(self):
        self.url = os.environ.get("OLLAMA_HOST", "").rstrip("/")
        self.model = os.environ.get("ZB_MODEL", "qwen2.5-coder")

    def available(self) -> bool:
        if not self.url:
            return False
        try:
            urllib.request.urlopen(f"{self.url}/api/tags", timeout=2)
            return True
        except Exception:
            return False

    def complete(self, system: str, user: str) -> str:
        data = _post_json(f"{self.url}/api/generate",
                          {"model": self.model, "system": system, "prompt": user,
                           "stream": False}, {})
        return data.get("response", "")


class BriefProvider(Provider):
    """Offline: never calls a model. Agents see `offline` and write briefs."""
    name = "brief"
    offline = True

    def available(self) -> bool:
        return True

    def complete(self, system: str, user: str) -> str:
        raise ProviderError("brief mode has no model; the agent should write a brief")


PROVIDERS = {"rovodev": RovoDevProvider, "anthropic": AnthropicProvider,
             "openai": OpenAICompatibleProvider, "gemini": GeminiProvider,
             "ollama": OllamaProvider, "brief": BriefProvider}
FALLBACK_ORDER = ["rovodev", "anthropic", "openai", "gemini", "ollama", "brief"]


def get_provider(name: str | None = None) -> Provider:
    """An explicit name (or ZB_PROVIDER) wins; otherwise the first available."""
    name = name or os.environ.get("ZB_PROVIDER", "")
    if name:
        if name not in PROVIDERS:
            raise ProviderError(f"unknown provider {name!r}; choose from {', '.join(PROVIDERS)}")
        provider = PROVIDERS[name]()
        if not provider.available():
            raise ProviderError(f"provider {name!r} is not available (check its env vars)")
        return provider
    for candidate in FALLBACK_ORDER:
        provider = PROVIDERS[candidate]()
        if provider.available():
            return provider
    return BriefProvider()
