from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex.client import CodexOAuthLLM
from oauth_codex.types import OAuthTokens, StreamEvent


@pytest.mark.asyncio
async def test_sync_async_payload_parity(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = CodexOAuthLLM(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )

    captured: dict[str, dict] = {}

    def fake_sync(**kwargs):
        captured["sync"] = kwargs["payload"]
        yield StreamEvent(type="text_delta", delta="ok")
        yield StreamEvent(type="done")

    async def fake_async(**kwargs):
        captured["async"] = kwargs["payload"]
        yield StreamEvent(type="text_delta", delta="ok")
        yield StreamEvent(type="done")

    monkeypatch.setattr(llm, "_stream_sse_sync", fake_sync)
    monkeypatch.setattr(llm, "_stream_sse_async", fake_async)

    llm.generate(
        model="gpt-5.3-codex",
        prompt="hi",
        response_format={"type": "json_object"},
        reasoning={"effort": "high", "summary": "auto"},
        temperature=0.2,
        top_p=0.8,
        max_output_tokens=256,
        metadata={"k": "v"},
        include=["reasoning"],
    )
    await llm.agenerate(
        model="gpt-5.3-codex",
        prompt="hi",
        response_format={"type": "json_object"},
        reasoning={"effort": "high", "summary": "auto"},
        temperature=0.2,
        top_p=0.8,
        max_output_tokens=256,
        metadata={"k": "v"},
        include=["reasoning"],
    )

    assert captured["sync"] == captured["async"]
