from __future__ import annotations

import oauth_codex
from oauth_codex import OAuthCodexClient
from oauth_codex._module_client import _load_client
from oauth_codex.legacy_types import OAuthTokens, StreamEvent


class InMemoryTokenStore:
    def __init__(self) -> None:
        self.tokens = OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)

    def load(self):
        return self.tokens

    def save(self, tokens):
        self.tokens = tokens

    def delete(self):
        self.tokens = None


def test_module_proxy_uses_lazy_client(monkeypatch) -> None:
    client = OAuthCodexClient(token_store=InMemoryTokenStore())

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="response_started", response_id="resp_m")
        yield StreamEvent(type="text_delta", delta="module", response_id="resp_m")
        yield StreamEvent(type="response_completed", response_id="resp_m", finish_reason="stop")
        yield StreamEvent(type="done", response_id="resp_m")

    monkeypatch.setattr(client._engine, "_stream_responses_sync", fake_stream)
    monkeypatch.setattr("oauth_codex._module_client._load_client", lambda: client)

    resp = oauth_codex.responses.create(model="gpt-5.3-codex", input="hi")
    assert resp.id == "resp_m"
    assert resp.output_text == "module"

    # Ensure module globals exist for OAuth-centric settings.
    assert hasattr(oauth_codex, "oauth_client_id")
    assert hasattr(oauth_codex, "oauth_redirect_uri")


def test_load_client_builds_default_client() -> None:
    client = _load_client()
    assert isinstance(client, OAuthCodexClient)
