from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import AsyncOAuthCodexClient, OAuthCodexClient
from oauth_codex.core_types import OAuthTokens, StreamEvent


def _client() -> OAuthCodexClient:
    return OAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )


def test_responses_create_and_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="response_started", response_id="resp_1")
        yield StreamEvent(type="text_delta", delta="hello", response_id="resp_1")
        yield StreamEvent(type="response_completed", response_id="resp_1", finish_reason="stop")
        yield StreamEvent(type="done", response_id="resp_1")

    monkeypatch.setattr(client._engine, "_stream_responses_sync", fake_stream)

    response = client.responses.create(model="gpt-5.3-codex", input="hi")
    assert response.id == "resp_1"
    assert response.output_text == "hello"

    events = list(client.responses.create(model="gpt-5.3-codex", input="hi", stream=True))
    assert events[0].type == "response_started"
    assert events[-1].type == "done"


@pytest.mark.asyncio
async def test_async_responses_create(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AsyncOAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )

    async def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="response_started", response_id="resp_a")
        yield StreamEvent(type="text_delta", delta="ok", response_id="resp_a")
        yield StreamEvent(type="response_completed", response_id="resp_a", finish_reason="stop")
        yield StreamEvent(type="done", response_id="resp_a")

    monkeypatch.setattr(client._engine, "_stream_responses_async", fake_stream)

    response = await client.responses.create(model="gpt-5.3-codex", input="hi")
    assert response.id == "resp_a"
    assert response.output_text == "ok"


def test_input_tokens_count(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()

    def fake_request(**kwargs):
        assert kwargs["path"] == "/responses/input_tokens"
        return {"input_tokens": 11, "cached_tokens": 2, "total_tokens": 11}

    monkeypatch.setattr(client._engine, "_request_json_sync", fake_request)

    out = client.responses.input_tokens.count(model="gpt-5.3-codex", input="hello")
    assert out.input_tokens == 11
    assert out.cached_tokens == 2
