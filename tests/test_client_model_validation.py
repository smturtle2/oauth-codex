from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex.client import CodexOAuthLLM
from oauth_codex.errors import ModelValidationError
from oauth_codex.types import OAuthConfig, OAuthTokens, StreamEvent


def _llm() -> CodexOAuthLLM:
    store = InMemoryTokenStore(
        OAuthTokens(
            access_token="a",
            refresh_token="r",
            expires_at=9_999_999_999,
        )
    )
    return CodexOAuthLLM(token_store=store, oauth_config=OAuthConfig(client_id="cid"))


def _sync_stream(**kwargs):
    _ = kwargs
    yield StreamEvent(type="text_delta", delta="ok")
    yield StreamEvent(type="done")


async def _async_stream(**kwargs):
    _ = kwargs
    yield StreamEvent(type="text_delta", delta="ok")
    yield StreamEvent(type="done")


def test_validate_model_sync_uses_local_validation_on_codex_profile() -> None:
    llm = _llm()
    llm._stream_sse_sync = _sync_stream  # type: ignore[method-assign]

    text = llm.generate(model="gpt-5.3-codex", prompt="hi", validate_model=True)

    assert text == "ok"


def test_validate_model_sync_rejects_blank_model() -> None:
    llm = _llm()

    with pytest.raises(ModelValidationError):
        llm.generate(model="", prompt="hi", validate_model=True)


@pytest.mark.asyncio
async def test_validate_model_async_uses_local_validation_on_codex_profile() -> None:
    llm = _llm()
    llm._stream_sse_async = _async_stream  # type: ignore[method-assign]

    text = await llm.agenerate(model="gpt-5.3-codex", prompt="hi", validate_model=True)

    assert text == "ok"


@pytest.mark.asyncio
async def test_validate_model_async_rejects_blank_model() -> None:
    llm = _llm()

    with pytest.raises(ModelValidationError):
        await llm.agenerate(model="", prompt="hi", validate_model=True)
