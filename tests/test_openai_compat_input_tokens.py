from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import OAuthCodexClient, SDKRequestError
from oauth_codex.types import OAuthTokens


def _client() -> OAuthCodexClient:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    return OAuthCodexClient(token_store=store)


def test_input_tokens_count_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()

    def fake_request_json_sync(**kwargs):
        assert kwargs["path"] == "/responses/input_tokens"
        return {"input_tokens": 12, "cached_tokens": 3, "total_tokens": 12}

    monkeypatch.setattr(client._engine, "_request_json_sync", fake_request_json_sync)

    out = client.responses.input_tokens.count(model="gpt-5.3-codex", input="hello")

    assert out.input_tokens == 12
    assert out.cached_tokens == 3
    assert out.total_tokens == 12


def test_input_tokens_count_raises_on_invalid_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()

    monkeypatch.setattr(client._engine, "_request_json_sync", lambda **kwargs: {"cached_tokens": 1})

    with pytest.raises(SDKRequestError):
        client.responses.input_tokens.count(model="gpt-5.3-codex", input="hello")
