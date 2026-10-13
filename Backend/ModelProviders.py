"""Local-first model adapters with an optional OpenAI-compatible cloud fallback.

Uses only the Python standard library so the assistant can start without optional
AI SDKs or API credentials. Model responses are untrusted input and must be
validated by AgentRuntime before any tool is executed.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ModelProviderError(RuntimeError):
    """Raised when a configured model provider cannot return a response."""


@dataclass(frozen=True)
class ModelReply:
    text: str
    provider: str


class LocalFirstModelRouter:
    """Call Ollama first; use an OpenAI-compatible endpoint only if configured."""

    def __init__(
        self,
        *,
        local_url: str | None = None,
        local_model: str | None = None,
        cloud_url: str | None = None,
        cloud_model: str | None = None,
        cloud_api_key: str | None = None,
        timeout_seconds: float = 45.0,
    ) -> None:
        self.local_url = (local_url or os.getenv("JARVIS_OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.local_model = local_model or os.getenv("JARVIS_LOCAL_MODEL", "qwen2.5:7b")
        self.cloud_url = (cloud_url or os.getenv("JARVIS_CLOUD_BASE_URL", "")).rstrip("/")
        self.cloud_model = cloud_model or os.getenv("JARVIS_CLOUD_MODEL", "")
        self.cloud_api_key = cloud_api_key or os.getenv("JARVIS_CLOUD_API_KEY", "")
        self.timeout_seconds = max(1.0, float(timeout_seconds))

    def complete(self, messages: list[dict[str, str]]) -> ModelReply:
        local_error: Exception | None = None
        try:
            return ModelReply(self._ollama(messages), "local")
        except (ModelProviderError, OSError, ValueError) as exc:
            local_error = exc

        if self.cloud_url and self.cloud_model and self.cloud_api_key:
            try:
                return ModelReply(self._cloud(messages), "cloud")
            except (ModelProviderError, OSError, ValueError) as exc:
                raise ModelProviderError(
                    f"Local inference failed ({type(local_error).__name__}); "
                    f"cloud fallback failed ({type(exc).__name__}). Check provider configuration and logs."
                ) from exc

        raise ModelProviderError(
            "Local model is unavailable and cloud fallback is not fully configured. "
            "Start Ollama and pull the configured model, or configure JARVIS_CLOUD_BASE_URL, "
            "JARVIS_CLOUD_MODEL, and JARVIS_CLOUD_API_KEY."
        ) from local_error

    def _post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(4_000_000)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            # Do not surface response bodies, which can contain provider details or secrets.
            raise ModelProviderError(f"Model request failed: {type(exc).__name__}") from exc
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ModelProviderError("Model provider returned invalid JSON.") from exc
        if not isinstance(data, dict):
            raise ModelProviderError("Model provider returned an unexpected response shape.")
        return data

    def _ollama(self, messages: list[dict[str, str]]) -> str:
        data = self._post_json(
            f"{self.local_url}/api/chat",
            {"model": self.local_model, "messages": messages, "stream": False, "format": "json"},
        )
        message = data.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ModelProviderError("Local model returned an empty response.")
        return content.strip()

    def _cloud(self, messages: list[dict[str, str]]) -> str:
        data = self._post_json(
            f"{self.cloud_url}/chat/completions",
            {"model": self.cloud_model, "messages": messages, "stream": False, "temperature": 0},
            {"Authorization": f"Bearer {self.cloud_api_key}"},
        )
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ModelProviderError("Cloud model returned an unexpected response shape.")
        message = choices[0].get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ModelProviderError("Cloud model returned an empty response.")
        return content.strip()
