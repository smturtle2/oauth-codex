from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex.client import CodexOAuthLLM
from oauth_codex.types import OAuthTokens, StreamEvent


def _llm() -> CodexOAuthLLM:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    return CodexOAuthLLM(token_store=store)


def _usage_event() -> StreamEvent:
    llm = _llm()
    return StreamEvent(
        type="usage",
        usage=llm._parse_usage(
            {
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
                "input_tokens_details": {"cached_tokens": 2},
                "output_tokens_details": {"reasoning_tokens": 1},
            }
        ),
    )


def test_usage_parse_aliases() -> None:
    usage = _usage_event().usage
    assert usage is not None
    assert usage.cached_tokens == usage.cached_input_tokens == 2
    assert usage.reasoning_tokens == usage.reasoning_output_tokens == 1


def test_sync_generate_usage_consistency(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = _llm()

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="text_delta", delta="ok")
        yield _usage_event()
        yield StreamEvent(type="done")

    monkeypatch.setattr(llm, "_stream_responses_sync", fake_stream)

    result = llm.generate(model="gpt-5.3-codex", prompt="hi", return_details=True)

    assert result.usage is not None
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 5
    assert result.usage.total_tokens == 15
    assert result.usage.cached_tokens == 2
    assert result.usage.reasoning_tokens == 1


@pytest.mark.asyncio
async def test_async_generate_usage_consistency(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = _llm()

    async def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="text_delta", delta="ok")
        yield _usage_event()
        yield StreamEvent(type="done")

    monkeypatch.setattr(llm, "_stream_responses_async", fake_stream)

    result = await llm.agenerate(model="gpt-5.3-codex", prompt="hi", return_details=True)

    assert result.usage is not None
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 5
    assert result.usage.total_tokens == 15
    assert result.usage.cached_tokens == 2
    assert result.usage.reasoning_tokens == 1
