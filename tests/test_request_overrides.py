from __future__ import annotations

import httpx
import pytest

from conftest import InMemoryTokenStore
from oauth_codex.client import CodexOAuthLLM
from oauth_codex.types import OAuthTokens, StreamEvent


class _FakeJSONClient:
    def __init__(self, response: httpx.Response, captured: dict[str, object]) -> None:
        self._response = response
        self._captured = captured

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def request(self, method, url, headers=None, json=None, params=None):
        self._captured["method"] = method
        self._captured["url"] = url
        self._captured["headers"] = headers
        self._captured["json"] = json
        self._captured["params"] = params
        return self._response


class _FakeStreamResponse:
    def __init__(self, captured: dict[str, object]) -> None:
        self._captured = captured
        self.status_code = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def iter_lines(self):
        return iter(["data: [DONE]", ""])

    def read(self):
        return b""


class _FakeStreamClient:
    def __init__(self, captured: dict[str, object]) -> None:
        self._captured = captured

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def stream(self, method, url, headers=None, json=None, params=None):
        self._captured["method"] = method
        self._captured["url"] = url
        self._captured["headers"] = headers
        self._captured["json"] = json
        self._captured["params"] = params
        return _FakeStreamResponse(self._captured)


def test_request_json_sync_applies_extra_query_and_safe_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llm = CodexOAuthLLM(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="access-1", refresh_token="refresh-1", expires_at=9_999_999_999)
        )
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "oauth_codex.client.httpx.Client",
        lambda timeout=None: _FakeJSONClient(httpx.Response(200, json={"input_tokens": 1}), captured),
    )

    with pytest.warns(RuntimeWarning):
        out = llm._request_json_sync(
            path="/responses/input_tokens",
            payload={"model": "x", "input": []},
            extra_headers={"Authorization": "bad", "X-Trace-Id": "trace-1"},
            extra_query={"source": "test"},
            validation_mode="warn",
        )

    assert out["input_tokens"] == 1
    assert captured["params"] == {"source": "test"}
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["Authorization"] == "Bearer access-1"
    assert headers["X-Trace-Id"] == "trace-1"


def test_stream_sse_sync_applies_extra_query_and_protects_account_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tokens = OAuthTokens(
        access_token="access-1",
        refresh_token="refresh-1",
        expires_at=9_999_999_999,
        account_id="acct-1",
    )
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(tokens))
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "oauth_codex.client.httpx.Client",
        lambda timeout=None: _FakeStreamClient(captured),
    )

    with pytest.warns(RuntimeWarning):
        events = list(
            llm._stream_sse_sync(
                path="/responses",
                payload={"model": "x", "stream": True},
                parser=lambda _event, _payload: [],
                tokens=tokens,
                extra_headers={"ChatGPT-Account-ID": "override", "X-Trace-Id": "trace-2"},
                extra_query={"source": "test"},
                validation_mode="warn",
            )
        )

    assert events[-1] == StreamEvent(type="done")
    assert captured["params"] == {"source": "test"}
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["ChatGPT-Account-ID"] == "acct-1"
    assert headers["X-Trace-Id"] == "trace-2"
