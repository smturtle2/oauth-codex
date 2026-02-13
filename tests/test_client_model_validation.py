from __future__ import annotations

import pytest

from oauth_codex.client import CodexOAuthLLM
from oauth_codex.errors import ModelValidationError
from oauth_codex.types import OAuthConfig, OAuthTokens
from conftest import InMemoryTokenStore


def _llm() -> CodexOAuthLLM:
    store = InMemoryTokenStore(
        OAuthTokens(
            access_token="a",
            refresh_token="r",
            expires_at=9_999_999_999,
        )
    )
    return CodexOAuthLLM(token_store=store, oauth_config=OAuthConfig(client_id="cid"))


def test_validate_model_sync_is_unsupported() -> None:
    llm = _llm()

    with pytest.raises(ModelValidationError):
        llm.generate(model="gpt-5.3-codex", prompt="hi", validate_model=True)


@pytest.mark.asyncio
async def test_validate_model_async_is_unsupported() -> None:
    llm = _llm()

    with pytest.raises(ModelValidationError):
        await llm.agenerate(model="gpt-5.3-codex", prompt="hi", validate_model=True)
