from __future__ import annotations

import pytest

from oauth_codex.client import CodexOAuthLLM
from oauth_codex.errors import (
    AuthRequiredError,
    LLMRequestError,
    ModelValidationError,
    ToolCallRequiredError,
)
from oauth_codex.types import OAuthConfig, OAuthTokens, StreamEvent
from conftest import InMemoryTokenStore


def _text_stream(text: str):
    yield StreamEvent(type="text_delta", delta=text)
    yield StreamEvent(type="done")


def test_generate_triggers_lazy_login_when_no_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    store = InMemoryTokenStore(tokens=None)
    llm = CodexOAuthLLM(token_store=store, oauth_config=OAuthConfig(client_id="cid"))

    called = {"login": 0}

    def fake_login() -> None:
        called["login"] += 1
        store.save(
            OAuthTokens(
                access_token="a1",
                refresh_token="r1",
                expires_at=9_999_999_999,
            )
        )

    monkeypatch.setattr(llm, "login", fake_login)
    monkeypatch.setattr(llm, "_stream_sse_sync", lambda **kwargs: _text_stream("hello"))

    text = llm.generate(model="gpt-5.3-codex", prompt="hi")

    assert text == "hello"
    assert called["login"] == 1


def test_generate_refreshes_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    expired = OAuthTokens(access_token="old", refresh_token="r1", expires_at=0)
    store = InMemoryTokenStore(tokens=expired)
    llm = CodexOAuthLLM(token_store=store, oauth_config=OAuthConfig(client_id="cid"))

    called = {"refresh": 0}

    def fake_refresh(tokens: OAuthTokens) -> OAuthTokens:
        _ = tokens
        called["refresh"] += 1
        fresh = OAuthTokens(
            access_token="new",
            refresh_token="r1",
            expires_at=9_999_999_999,
        )
        store.save(fresh)
        return fresh

    monkeypatch.setattr(llm, "_refresh_and_persist_sync", fake_refresh)
    monkeypatch.setattr(llm, "_stream_sse_sync", lambda **kwargs: _text_stream("ok"))

    text = llm.generate(model="gpt-5.3-codex", prompt="hi")

    assert text == "ok"
    assert called["refresh"] >= 1


def test_generate_raises_auth_required_when_refresh_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    expired = OAuthTokens(access_token="old", refresh_token="r1", expires_at=0)
    store = InMemoryTokenStore(tokens=expired)
    llm = CodexOAuthLLM(token_store=store, oauth_config=OAuthConfig(client_id="cid"))

    monkeypatch.setattr(
        llm,
        "_refresh_and_persist_sync",
        lambda tokens: (_ for _ in ()).throw(AuthRequiredError("relogin")),
    )

    with pytest.raises(AuthRequiredError):
        llm.generate(model="gpt-5.3-codex", prompt="hi")


def test_generate_passes_model_name_without_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(OAuthTokens("a", refresh_token="r", expires_at=9_999_999_999)))

    captured: dict[str, str] = {}

    def fake_stream(**kwargs):
        captured["model"] = kwargs["model"]
        return _text_stream("ok")

    monkeypatch.setattr(llm, "_stream_responses_sync", fake_stream)

    llm.generate(model="gpt-5.3-codex", prompt="hi")

    assert captured["model"] == "gpt-5.3-codex"


def test_generate_calls_model_validation_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(OAuthTokens("a", refresh_token="r", expires_at=9_999_999_999)))

    called = {"validate": 0}

    def fake_validate(model: str, tokens: OAuthTokens) -> None:
        called["validate"] += 1
        assert model == "gpt-5.3-codex"
        assert tokens.access_token == "a"

    monkeypatch.setattr(llm, "_validate_model_sync", fake_validate)
    monkeypatch.setattr(llm, "_stream_responses_sync", lambda **kwargs: _text_stream("ok"))

    llm.generate(model="gpt-5.3-codex", prompt="hi", validate_model=True)

    assert called["validate"] == 1


def test_generate_passes_responses_request_options(
    monkeypatch: pytest.MonkeyPatch,
    valid_tokens: OAuthTokens,
) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))
    captured: dict[str, object] = {}

    def fake_stream_sse_sync(**kwargs):
        captured["payload"] = kwargs["payload"]
        return _text_stream("ok")

    monkeypatch.setattr(llm, "_stream_sse_sync", fake_stream_sse_sync)

    text = llm.generate(
        model="gpt-5.3-codex",
        prompt="hi",
        tools=[{"type": "function", "name": "get_weather", "parameters": {"type": "object"}}],
        response_format={"type": "json_object"},
        tool_choice={"type": "function", "name": "get_weather"},
        strict_output=True,
        store=True,
        reasoning={"effort": "high"},
    )

    assert text == "ok"

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["store"] is True
    assert payload["tool_choice"] == {"type": "function", "name": "get_weather"}
    assert payload["reasoning"] == {"effort": "high"}
    assert payload["text"] == {"format": {"type": "json_object"}}
    assert payload["tools"][0]["strict"] is True


def test_generate_defaults_to_store_false(
    monkeypatch: pytest.MonkeyPatch,
    valid_tokens: OAuthTokens,
) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))
    captured: dict[str, object] = {}

    def fake_stream_sse_sync(**kwargs):
        captured["payload"] = kwargs["payload"]
        return _text_stream("ok")

    monkeypatch.setattr(llm, "_stream_sse_sync", fake_stream_sse_sync)

    llm.generate(model="gpt-5.3-codex", prompt="hi")

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["store"] is False


def test_generate_propagates_model_validation_error() -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(OAuthTokens("a", refresh_token="r", expires_at=9_999_999_999)))

    with pytest.raises(ModelValidationError):
        llm.generate(model="gpt-5.3-codex", prompt="hi", validate_model=True)


def test_generate_requires_prompt_or_messages_exclusively(valid_tokens: OAuthTokens) -> None:
    store = InMemoryTokenStore(tokens=valid_tokens)
    llm = CodexOAuthLLM(token_store=store)

    with pytest.raises(ValueError):
        llm.generate(model="gpt-5.3-codex")

    with pytest.raises(ValueError):
        llm.generate(
            model="gpt-5.3-codex",
            prompt="a",
            messages=[{"role": "user", "content": "b"}],
        )


def test_generate_rejects_non_responses_mode(valid_tokens: OAuthTokens) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))

    with pytest.raises(ValueError):
        llm.generate(model="gpt-5.3-codex", prompt="hi", api_mode="chat_completions")  # type: ignore[arg-type]


def test_generate_raises_tool_call_required_when_not_returning_details(
    monkeypatch: pytest.MonkeyPatch,
    valid_tokens: OAuthTokens,
) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(
            type="tool_call_done",
            tool_call=llm._build_tool_call("call_1", "get_weather", '{"city":"Seoul"}'),
        )
        yield StreamEvent(type="done")

    monkeypatch.setattr(llm, "_stream_responses_sync", fake_stream)

    with pytest.raises(ToolCallRequiredError) as exc:
        llm.generate(
            model="gpt-5.3-codex",
            messages=[{"role": "user", "content": "weather?"}],
            tools=[{"type": "function", "name": "get_weather", "parameters": {"type": "object"}}],
            return_details=False,
        )

    assert len(exc.value.tool_calls) == 1
    assert exc.value.tool_calls[0].name == "get_weather"


def test_generate_returns_details_with_tool_calls(
    monkeypatch: pytest.MonkeyPatch,
    valid_tokens: OAuthTokens,
) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(
            type="tool_call_done",
            tool_call=llm._build_tool_call("call_1", "get_weather", '{"city":"Seoul"}'),
        )
        yield StreamEvent(type="done")

    monkeypatch.setattr(llm, "_stream_responses_sync", fake_stream)

    result = llm.generate(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "weather?"}],
        tools=[{"type": "function", "name": "get_weather", "parameters": {"type": "object"}}],
        return_details=True,
    )

    assert result.finish_reason == "tool_calls"
    assert result.tool_calls[0].arguments == {"city": "Seoul"}


def test_generate_includes_tool_results_for_responses(
    monkeypatch: pytest.MonkeyPatch,
    valid_tokens: OAuthTokens,
) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))

    captured = {}

    def fake_stream(**kwargs):
        captured.update(kwargs)
        return _text_stream("done")

    monkeypatch.setattr(llm, "_stream_responses_sync", fake_stream)

    llm.generate(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "continue"}],
        tools=[{"type": "function", "name": "x", "parameters": {"type": "object"}}],
        tool_results=[{"tool_call_id": "c1", "name": "x", "output": {"ok": True}}],
    )

    assert captured["tool_results"][0].tool_call_id == "c1"
    assert captured["tool_results"][0].name == "x"


def test_auth_headers_use_access_token(valid_tokens: OAuthTokens) -> None:
    valid_tokens.api_key = "sk-exchanged"
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))

    headers = llm._auth_headers(valid_tokens)

    assert headers["Authorization"] == "Bearer access-1"


def test_resolve_request_url_uses_codex_backend(valid_tokens: OAuthTokens) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))

    url = llm._resolve_request_url("/responses")

    assert url == "https://chatgpt.com/backend-api/codex/responses"


def test_resolve_request_url_rejects_non_responses_path(valid_tokens: OAuthTokens) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))

    with pytest.raises(LLMRequestError):
        llm._resolve_request_url("/chat/completions")


def test_generate_collects_from_stream_on_codex_backend(
    monkeypatch: pytest.MonkeyPatch,
    valid_tokens: OAuthTokens,
) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="text_delta", delta="OK")
        yield StreamEvent(
            type="usage",
            usage=llm._parse_usage({"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}),
        )
        yield StreamEvent(type="done")

    monkeypatch.setattr(llm, "_stream_responses_sync", fake_stream)

    result = llm.generate(
        model="gpt-5.3-codex",
        prompt="hi",
        return_details=True,
    )

    assert result.text == "OK"
    assert result.finish_reason == "stop"
    assert result.usage is not None
    assert result.usage.total_tokens == 3
