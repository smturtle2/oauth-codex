from __future__ import annotations

import io

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import NotSupportedError, OAuthCodexClient
from oauth_codex.types import OAuthTokens


def _client(base_url: str = "https://chatgpt.com/backend-api/codex") -> OAuthCodexClient:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    return OAuthCodexClient(token_store=store, chatgpt_base_url=base_url)


def test_files_create_not_supported_on_codex_profile() -> None:
    client = _client()

    with pytest.raises(NotSupportedError) as exc:
        client.files.create(file=io.BytesIO(b"x"), purpose="assistants")

    assert exc.value.code == "files_not_supported_on_codex_oauth"


def test_vector_stores_not_supported_on_codex_profile() -> None:
    client = _client()

    with pytest.raises(NotSupportedError) as exc:
        client.vector_stores.create(name="docs")

    assert exc.value.code == "vector_stores_not_supported_on_codex_oauth"


def test_vector_stores_calls_remote_when_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(base_url="https://api.openai.com/v1")

    def fake_request(**kwargs):
        assert kwargs["path"] == "/vector_stores"
        assert kwargs["method"] == "POST"
        return {"id": "vs_1"}

    monkeypatch.setattr(client._engine, "_request_json_sync", fake_request)

    out = client.vector_stores.create(name="docs")

    assert out["id"] == "vs_1"
