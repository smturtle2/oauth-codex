from __future__ import annotations

import httpx

from conftest import InMemoryTokenStore
from oauth_codex.client import CodexOAuthLLM
from oauth_codex.types import OAuthTokens


class _FakeClient:
    def __init__(self, response: httpx.Response) -> None:
        self._response = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def request(self, method, url, headers=None, json=None):
        _ = method, url, headers, json
        return self._response


def test_observability_hooks_fire(monkeypatch):
    events: dict[str, list[dict]] = {
        "start": [],
        "end": [],
        "auth": [],
        "error": [],
    }

    llm = CodexOAuthLLM(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        ),
        on_request_start=lambda payload: events["start"].append(payload),
        on_request_end=lambda payload: events["end"].append(payload),
        on_auth_refresh=lambda payload: events["auth"].append(payload),
        on_error=lambda payload: events["error"].append(payload),
    )

    monkeypatch.setattr(
        "oauth_codex.client.httpx.Client",
        lambda timeout=None: _FakeClient(httpx.Response(200, json={"input_tokens": 1})),
    )

    out = llm._request_json_sync(path="/responses/input_tokens", payload={"model": "x", "input": []})

    assert out["input_tokens"] == 1
    assert len(events["start"]) == 1
    assert len(events["end"]) == 1
    assert events["start"][0]["request_id"].startswith("req_")
    assert events["end"][0]["request_id"].startswith("req_")
