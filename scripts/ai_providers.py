"""AI provider abstraction used by scripts/enrich_notes.py.

Three interchangeable providers behind one interface (``AIProvider.complete``):

- ``claude`` -- Anthropic API. Needs ``ANTHROPIC_API_KEY``.
- ``openai`` -- OpenAI API. Needs ``OPENAI_API_KEY``.
- ``ollama`` -- a local Ollama server. No key, nothing leaves the machine.

Important: a ChatGPT Plus or Claude Pro *subscription* does not include API
access. ``claude``/``openai`` here need a separate API key from the Anthropic
Console / OpenAI Platform, billed per token independently of those
subscriptions.

Anthropic and OpenAI SDKs are optional dependencies (``pip install
running-content-engine[enrich]``, or install just the one you use) so the
rest of the pipeline never needs them installed.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Protocol

DEFAULT_CLAUDE_MODEL = "claude-opus-4-8"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
OLLAMA_TIMEOUT_SECONDS = 120.0

PROVIDER_NAMES: tuple[str, ...] = ("claude", "openai", "ollama")


class ProviderError(Exception):
    """Raised when a provider is misconfigured or a completion request fails."""


class AIProvider(Protocol):
    def complete(self, prompt: str) -> str: ...


class ClaudeProvider:
    """Anthropic API provider. Needs ANTHROPIC_API_KEY and the anthropic SDK."""

    def __init__(self, model: str = DEFAULT_CLAUDE_MODEL) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderError(
                "ANTHROPIC_API_KEY is not set. A Claude Pro subscription does not "
                "include API access -- create a separate API key at "
                "https://console.anthropic.com/settings/keys and export it as "
                "ANTHROPIC_API_KEY."
            )
        try:
            import anthropic
        except ModuleNotFoundError as exc:
            raise ProviderError(
                "The 'anthropic' package is required for --provider claude. "
                "Install it with: pip install anthropic"
            ) from exc

        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def complete(self, prompt: str) -> str:
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise ProviderError(f"Claude request failed: {exc}") from exc

        for block in response.content:
            if block.type == "text":
                return block.text
        raise ProviderError("Claude response contained no text content.")


class OpenAIProvider:
    """OpenAI API provider. Needs OPENAI_API_KEY, the openai SDK, and an explicit model.

    No default model is assumed here: OpenAI's recommended model ids change
    over time and guessing one risks a silent 404. Pass --model explicitly.
    """

    def __init__(self, model: str | None) -> None:
        if not model:
            raise ProviderError(
                "--model is required for --provider openai (no default is assumed "
                "since model ids change). Check "
                "https://platform.openai.com/docs/models for a current model id."
            )
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ProviderError(
                "OPENAI_API_KEY is not set. A ChatGPT Plus subscription does not "
                "include API access -- create a separate API key at "
                "https://platform.openai.com/api-keys and export it as "
                "OPENAI_API_KEY."
            )
        try:
            import openai
        except ModuleNotFoundError as exc:
            raise ProviderError(
                "The 'openai' package is required for --provider openai. "
                "Install it with: pip install openai"
            ) from exc

        self._client = openai.OpenAI(api_key=api_key)
        self.model = model

    def complete(self, prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc

        message = response.choices[0].message.content
        if not message:
            raise ProviderError("OpenAI response contained no content.")
        return message


class OllamaProvider:
    """Local Ollama provider. No API key; nothing leaves the machine.

    Needs a running ``ollama serve`` with the requested model pulled
    (``ollama pull <model>``).
    """

    def __init__(self, model: str = DEFAULT_OLLAMA_MODEL, host: str | None = None) -> None:
        self.model = model
        self.host = (host or os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)).rstrip("/")

    def complete(self, prompt: str) -> str:
        payload = json.dumps(
            {"model": self.model, "prompt": prompt, "stream": False}
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise ProviderError(
                f"Could not reach Ollama at {self.host}: {exc}. Is Ollama running? "
                f"Start it with `ollama serve` and pull a model with "
                f"`ollama pull {self.model}`."
            ) from exc

        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderError(f"Could not parse Ollama response: {exc}") from exc

        text = data.get("response")
        if not text:
            raise ProviderError(f"Ollama response contained no text: {data}")
        return text


def get_provider(name: str, model: str | None = None) -> AIProvider:
    """Build the requested provider by name.

    Raises:
        ProviderError: for an unknown provider name, a missing API key/SDK,
            or (for ``openai``) a missing ``model``.
    """

    if name == "claude":
        return ClaudeProvider(model=model or DEFAULT_CLAUDE_MODEL)
    if name == "openai":
        return OpenAIProvider(model=model)
    if name == "ollama":
        return OllamaProvider(model=model or DEFAULT_OLLAMA_MODEL)
    raise ProviderError(
        f"Unknown provider '{name}'. Choose from: {', '.join(PROVIDER_NAMES)}."
    )
