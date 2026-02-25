from __future__ import annotations

import importlib
from typing import Any, cast

import pytest

import oauth_codex
from oauth_codex._sdk_client import AsyncClient as SDKAsyncClient
from oauth_codex._sdk_client import Client as SDKClient
from conftest import InMemoryTokenStore
from oauth_codex.core_types import OAuthTokens
from oauth_codex.core_types import listMessage


def _client() -> oauth_codex.Client:
    return oauth_codex.Client(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )


def test_single_client_public_surface() -> None:
    assert oauth_codex.Client is SDKClient
    assert getattr(oauth_codex, "AsyncClient") is SDKAsyncClient
    assert oauth_codex.listMessage is listMessage


def test_removed_async_and_module_level_exports() -> None:
    assert hasattr(oauth_codex, "AsyncClient")
    assert not hasattr(oauth_codex, "OAuthCodexClient")
    assert not hasattr(oauth_codex, "AsyncOAuthCodexClient")

    for name in ["responses", "files", "vector_stores", "models"]:
        assert not hasattr(oauth_codex, name)


def test_client_exposes_chat_completions_and_responses_create() -> None:
    client = cast(Any, _client())

    assert hasattr(client, "chat")
    assert hasattr(client.chat, "completions")
    assert callable(client.chat.completions.create)

    assert hasattr(client, "responses")
    assert callable(client.responses.create)


def test_legacy_modules_removed() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("oauth_codex.legacy_types")

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("oauth_codex.legacy_auth")


def test_compat_module_removed() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("oauth_codex.compat")
