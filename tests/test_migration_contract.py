from __future__ import annotations

from conftest import InMemoryTokenStore
from oauth_codex import CodexOAuthLLM, OAuthCodexClient
from oauth_codex.types import OAuthTokens, StreamEvent


def test_legacy_generate_and_openai_compat_match_output(monkeypatch) -> None:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    legacy = CodexOAuthLLM(token_store=store)
    compat = OAuthCodexClient(token_store=store)

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="response_started", response_id="resp_1")
        yield StreamEvent(type="text_delta", delta="hello")
        yield StreamEvent(type="response_completed", response_id="resp_1", finish_reason="stop")
        yield StreamEvent(type="done", response_id="resp_1")

    monkeypatch.setattr(legacy, "_stream_responses_sync", fake_stream)
    monkeypatch.setattr(compat._engine, "_stream_responses_sync", fake_stream)

    legacy_text = legacy.generate(model="gpt-5.3-codex", prompt="hi")
    compat_resp = compat.responses.create(model="gpt-5.3-codex", input="hi")

    assert legacy_text == compat_resp.output_text == "hello"
    assert compat_resp.id == "resp_1"


def test_core_client_is_directly_openai_compatible(monkeypatch) -> None:
    llm = CodexOAuthLLM(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="response_started", response_id="resp_2")
        yield StreamEvent(type="text_delta", delta="direct")
        yield StreamEvent(type="response_completed", response_id="resp_2", finish_reason="stop")
        yield StreamEvent(type="done", response_id="resp_2")

    monkeypatch.setattr(llm, "_stream_responses_sync", fake_stream)

    resp = llm.responses.create(model="gpt-5.3-codex", input="hi")

    assert resp.id == "resp_2"
    assert resp.output_text == "direct"
