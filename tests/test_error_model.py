from __future__ import annotations

import httpx
import pytest

from conftest import InMemoryTokenStore
from oauth_codex import SDKRequestError, TokenStoreReadError, TokenStoreWriteError
from oauth_codex.client import CodexOAuthLLM
from oauth_codex.types import OAuthTokens


class FailingStore:
    def load(self):
        raise RuntimeError("load fail")

    def save(self, tokens):
        _ = tokens
        raise RuntimeError("save fail")

    def delete(self):
        return None


def _llm() -> CodexOAuthLLM:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    return CodexOAuthLLM(token_store=store)


def test_sdk_error_model_from_http_response() -> None:
    llm = _llm()
    response = httpx.Response(
        429,
        json={"error": {"code": "rate_limit_exceeded", "message": "too many"}},
    )

    err = llm._build_sdk_request_error(response, request_id="req_1")

    assert isinstance(err, SDKRequestError)
    assert err.status_code == 429
    assert err.provider_code == "rate_limit_exceeded"
    assert err.user_message == "too many"
    assert err.retryable is True
    assert err.request_id == "req_1"


def test_token_store_read_error_is_distinct() -> None:
    llm = CodexOAuthLLM(token_store=FailingStore())

    with pytest.raises(TokenStoreReadError):
        llm.is_authenticated()


def test_token_store_write_error_is_distinct() -> None:
    llm = CodexOAuthLLM(token_store=FailingStore())

    with pytest.raises(TokenStoreWriteError):
        llm._save_tokens_sync(OAuthTokens(access_token="a"))
