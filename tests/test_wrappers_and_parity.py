from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import AsyncOAuthCodexClient, OAuthCodexClient
from oauth_codex.core_types import OAuthTokens, StreamEvent


def _sync_client() -> OAuthCodexClient:
    return OAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )


@pytest.mark.asyncio
async def test_sync_async_payload_parity(monkeypatch: pytest.MonkeyPatch) -> None:
    sync_client = _sync_client()
    async_client = AsyncOAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )

    captured: dict[str, dict] = {}

    def fake_sync(**kwargs):
        captured["sync"] = kwargs
        yield StreamEvent(type="response_started", response_id="resp_1")
        yield StreamEvent(type="text_delta", delta="ok", response_id="resp_1")
        yield StreamEvent(type="response_completed", response_id="resp_1")
        yield StreamEvent(type="done", response_id="resp_1")

    async def fake_async(**kwargs):
        captured["async"] = kwargs
        yield StreamEvent(type="response_started", response_id="resp_1")
        yield StreamEvent(type="text_delta", delta="ok", response_id="resp_1")
        yield StreamEvent(type="response_completed", response_id="resp_1")
        yield StreamEvent(type="done", response_id="resp_1")

    monkeypatch.setattr(sync_client._engine, "_stream_responses_sync", fake_sync)
    monkeypatch.setattr(async_client._engine, "_stream_responses_async", fake_async)

    sync_client.responses.create(
        model="gpt-5.3-codex",
        input="hello",
        reasoning={"effort": "high"},
        max_output_tokens=128,
        extra_body={"custom": True},
    )
    await async_client.responses.create(
        model="gpt-5.3-codex",
        input="hello",
        reasoning={"effort": "high"},
        max_output_tokens=128,
        extra_body={"custom": True},
    )

    assert captured["sync"]["model"] == captured["async"]["model"]
    assert captured["sync"]["reasoning"] == captured["async"]["reasoning"]
    assert captured["sync"]["max_output_tokens"] == captured["async"]["max_output_tokens"]


def test_raw_wrapper_on_supported_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _sync_client()

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="response_started", response_id="resp_w")
        yield StreamEvent(type="text_delta", delta="wrap", response_id="resp_w")
        yield StreamEvent(type="response_completed", response_id="resp_w")
        yield StreamEvent(type="done", response_id="resp_w")

    monkeypatch.setattr(client._engine, "_stream_responses_sync", fake_stream)

    raw = client.responses.with_raw_response.create(model="gpt-5.3-codex", input="hi")
    parsed = raw.parse()

    assert parsed.id == "resp_w"
    assert parsed.output_text == "wrap"
