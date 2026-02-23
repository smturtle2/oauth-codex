from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import Client
from oauth_codex._client import _EngineClient
from oauth_codex.core_types import OAuthTokens


def _tokens() -> OAuthTokens:
    return OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)


def test_client_does_not_authenticate_on_init_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_calls = 0

    def fake_ensure(self: _EngineClient) -> OAuthTokens:
        nonlocal ensure_calls
        ensure_calls += 1
        return _tokens()

    monkeypatch.setattr(_EngineClient, "_ensure_authenticated_sync", fake_ensure)

    Client(token_store=InMemoryTokenStore(_tokens()))

    assert ensure_calls == 0


def test_client_authenticates_on_init_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_calls = 0

    def fake_ensure(self: _EngineClient) -> OAuthTokens:
        nonlocal ensure_calls
        ensure_calls += 1
        return _tokens()

    monkeypatch.setattr(_EngineClient, "_ensure_authenticated_sync", fake_ensure)

    Client(token_store=InMemoryTokenStore(), authenticate_on_init=True)

    assert ensure_calls == 1
