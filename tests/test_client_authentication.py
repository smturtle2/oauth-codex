from __future__ import annotations

from typing import Any

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import AsyncClient, Client
from oauth_codex.core_types import OAuthTokens


def _tokens() -> OAuthTokens:
    return OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)


def test_client_constructs_without_authentication_side_effects() -> None:
    Client(token_store=InMemoryTokenStore(_tokens()))


def test_client_no_longer_supports_authenticate_on_init_flag() -> None:
    with pytest.raises(TypeError):
        Client(token_store=InMemoryTokenStore(), authenticate_on_init=True)


def test_client_authenticate_delegates_to_auth_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Client(token_store=InMemoryTokenStore(_tokens()))
    called: dict[str, Any] = {}

    def fake_ensure_valid(*, interactive: bool = True) -> None:
        called["interactive"] = interactive

    monkeypatch.setattr(client.auth, "ensure_valid", fake_ensure_valid)

    out = client.authenticate()

    assert out is None
    assert called == {"interactive": True}


@pytest.mark.asyncio
async def test_async_client_authenticate_delegates_to_auth_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AsyncClient(token_store=InMemoryTokenStore(_tokens()))
    called: dict[str, Any] = {}

    async def fake_aensure_valid(*, interactive: bool = True) -> None:
        called["interactive"] = interactive

    monkeypatch.setattr(client.auth, "aensure_valid", fake_aensure_valid)

    out = await client.authenticate()

    assert out is None
    assert called == {"interactive": True}
