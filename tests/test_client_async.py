from __future__ import annotations

import pytest

from oauth_codex.client import CodexOAuthLLM
from oauth_codex.errors import ModelValidationError
from oauth_codex.types import OAuthConfig, OAuthTokens, StreamEvent
from conftest import InMemoryTokenStore


@pytest.mark.asyncio
async def test_agenerate_returns_text(monkeypatch: pytest.MonkeyPatch) -> None:
    store = InMemoryTokenStore(
        OAuthTokens(
            access_token="a",
            refresh_token="r",
            expires_at=9_999_999_999,
        )
    )
    llm = CodexOAuthLLM(token_store=store, oauth_config=OAuthConfig(client_id="cid"))

    async def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="text_delta", delta="hello-async")
        yield StreamEvent(type="done")

    monkeypatch.setattr(llm, "_stream_responses_async", fake_stream)

    text = await llm.agenerate(model="gpt-5.3-codex", prompt="hi")
    assert text == "hello-async"


@pytest.mark.asyncio
async def test_agenerate_passes_responses_request_options(
    monkeypatch: pytest.MonkeyPatch,
    valid_tokens: OAuthTokens,
) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))
    captured: dict[str, object] = {}

    async def fake_stream_sse_async(**kwargs):
        captured["payload"] = kwargs["payload"]
        yield StreamEvent(type="text_delta", delta="ok")
        yield StreamEvent(type="done")

    monkeypatch.setattr(llm, "_stream_sse_async", fake_stream_sse_async)

    text = await llm.agenerate(
        model="gpt-5.3-codex",
        prompt="hi",
        tools=[{"type": "function", "name": "get_weather", "parameters": {"type": "object"}}],
        response_format={"type": "json_object"},
        tool_choice="required",
        strict_output=True,
        store=True,
        reasoning={"effort": "medium"},
    )

    assert text == "ok"

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["store"] is True
    assert payload["tool_choice"] == "required"
    assert payload["reasoning"] == {"effort": "medium"}
    assert payload["text"] == {"format": {"type": "json_object"}}
    assert payload["tools"][0]["strict"] is True


@pytest.mark.asyncio
async def test_agenerate_stream_text(monkeypatch: pytest.MonkeyPatch) -> None:
    store = InMemoryTokenStore(
        OAuthTokens(
            access_token="a",
            refresh_token="r",
            expires_at=9_999_999_999,
        )
    )
    llm = CodexOAuthLLM(token_store=store, oauth_config=OAuthConfig(client_id="cid"))

    async def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="text_delta", delta="a")
        yield StreamEvent(type="text_delta", delta="b")
        yield StreamEvent(type="done")

    monkeypatch.setattr(llm, "_stream_responses_async", fake_stream)

    stream = await llm.agenerate_stream(model="gpt-5.3-codex", prompt="hi")
    out = []
    async for chunk in stream:
        out.append(chunk)

    assert out == ["a", "b"]


@pytest.mark.asyncio
async def test_validate_model_async_is_unsupported() -> None:
    store = InMemoryTokenStore(
        OAuthTokens(
            access_token="a",
            refresh_token="r",
            expires_at=9_999_999_999,
        )
    )
    llm = CodexOAuthLLM(token_store=store, oauth_config=OAuthConfig(client_id="cid"))

    with pytest.raises(ModelValidationError):
        await llm.agenerate(model="gpt-5.3-codex", prompt="hi", validate_model=True)
