from __future__ import annotations

import builtins
import json
from urllib.error import URLError

import pytest

from scripts.ai_providers import (
    DEFAULT_OLLAMA_MODEL,
    OllamaProvider,
    ProviderError,
    get_provider,
)


def _block_import(monkeypatch: pytest.MonkeyPatch, blocked_name: str) -> None:
    """Make `import <blocked_name>` raise ModuleNotFoundError, regardless of
    whether the package is actually installed in the environment running the
    tests. Using the ambient install state directly is fragile: these SDKs
    are optional dependencies, so whether they're missing depends on what
    else happens to be installed alongside the test run.
    """

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object):
        if name == blocked_name:
            raise ModuleNotFoundError(f"No module named '{blocked_name}'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_get_provider_rejects_unknown_name() -> None:
    with pytest.raises(ProviderError):
        get_provider("bogus")


def test_get_provider_ollama_uses_default_model() -> None:
    provider = get_provider("ollama")

    assert isinstance(provider, OllamaProvider)
    assert provider.model == DEFAULT_OLLAMA_MODEL


def test_claude_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ProviderError, match="ANTHROPIC_API_KEY"):
        get_provider("claude")


def test_claude_provider_requires_sdk_when_key_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")
    _block_import(monkeypatch, "anthropic")

    with pytest.raises(ProviderError, match="pip install anthropic"):
        get_provider("claude")


def test_openai_provider_requires_explicit_model() -> None:
    with pytest.raises(ProviderError, match="--model is required"):
        get_provider("openai", model=None)


def test_openai_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ProviderError, match="OPENAI_API_KEY"):
        get_provider("openai", model="gpt-4o-mini")


def test_openai_provider_requires_sdk_when_key_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-test")
    _block_import(monkeypatch, "openai")

    with pytest.raises(ProviderError, match="pip install openai"):
        get_provider("openai", model="gpt-4o-mini")


def test_ollama_provider_complete_returns_response_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OllamaProvider(model="llama3.1:8b")

    class _FakeResponse:
        def read(self) -> bytes:
            return json.dumps({"response": "hello from ollama"}).encode("utf-8")

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

    def fake_urlopen(request, timeout=None):
        return _FakeResponse()

    monkeypatch.setattr(
        "scripts.ai_providers.urllib.request.urlopen", fake_urlopen
    )

    assert provider.complete("draft something") == "hello from ollama"


def test_ollama_provider_complete_raises_when_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OllamaProvider(model="llama3.1:8b")

    def fake_urlopen(request, timeout=None):
        raise URLError("connection refused")

    monkeypatch.setattr(
        "scripts.ai_providers.urllib.request.urlopen", fake_urlopen
    )

    with pytest.raises(ProviderError, match="Is Ollama running"):
        provider.complete("draft something")


def test_ollama_provider_complete_raises_when_response_has_no_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OllamaProvider(model="llama3.1:8b")

    class _FakeResponse:
        def read(self) -> bytes:
            return json.dumps({}).encode("utf-8")

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

    monkeypatch.setattr(
        "scripts.ai_providers.urllib.request.urlopen",
        lambda request, timeout=None: _FakeResponse(),
    )

    with pytest.raises(ProviderError):
        provider.complete("draft something")
