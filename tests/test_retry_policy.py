from __future__ import annotations

import httpx
import pytest

from conftest import InMemoryTokenStore
from oauth_codex.client import CodexOAuthLLM
from oauth_codex.types import OAuthTokens


def _llm() -> CodexOAuthLLM:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    return CodexOAuthLLM(token_store=store)


class _FakeClient:
    def __init__(self, responses):
        self._responses = responses

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def request(self, method, url, headers=None, json=None):
        _ = method, url, headers, json
        return self._responses.pop(0)


def test_retry_401_refresh_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = _llm()
    tokens = OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    refreshed = OAuthTokens(access_token="b", refresh_token="r", expires_at=9_999_999_999)

    responses = [
        httpx.Response(401, json={"error": {"message": "expired"}}),
        httpx.Response(200, json={"input_tokens": 1}),
    ]

    monkeypatch.setattr("oauth_codex.client.httpx.Client", lambda timeout=None: _FakeClient(responses))
    monkeypatch.setattr(llm, "_ensure_authenticated_sync", lambda: tokens)

    called = {"refresh": 0}

    def fake_refresh(_tokens):
        called["refresh"] += 1
        return refreshed

    monkeypatch.setattr(llm, "_refresh_and_persist_sync", fake_refresh)

    out = llm._request_json_sync(path="/responses/input_tokens", payload={"model": "x", "input": []})

    assert out["input_tokens"] == 1
    assert called["refresh"] == 1


def test_retry_429_backoff_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = _llm()

    responses = [
        httpx.Response(429, json={"error": {"message": "rate limit"}}),
        httpx.Response(200, json={"input_tokens": 2}),
    ]

    monkeypatch.setattr("oauth_codex.client.httpx.Client", lambda timeout=None: _FakeClient(responses))
    monkeypatch.setattr(llm, "_ensure_authenticated_sync", lambda: OAuthTokens(access_token="a"))

    slept: list[float] = []
    monkeypatch.setattr("oauth_codex.client.time.sleep", lambda seconds: slept.append(seconds))

    out = llm._request_json_sync(path="/responses/input_tokens", payload={"model": "x", "input": []})

    assert out["input_tokens"] == 2
    assert len(slept) == 1
