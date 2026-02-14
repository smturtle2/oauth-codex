from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import ContinuityError, OAuthCodexClient
from oauth_codex.types import OAuthTokens, StreamEvent


def _client() -> OAuthCodexClient:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    return OAuthCodexClient(token_store=store)


def test_responses_create_returns_openai_compatible_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="response_started", response_id="resp_1")
        yield StreamEvent(type="text_delta", delta="hello")
        yield StreamEvent(
            type="usage",
            usage=client._engine._parse_usage(
                {
                    "input_tokens": 10,
                    "output_tokens": 3,
                    "total_tokens": 13,
                    "input_tokens_details": {"cached_tokens": 2},
                    "output_tokens_details": {"reasoning_tokens": 1},
                }
            ),
        )
        yield StreamEvent(type="response_completed", response_id="resp_1", finish_reason="stop")
        yield StreamEvent(type="done", response_id="resp_1")

    monkeypatch.setattr(client._engine, "_stream_responses_sync", fake_stream)

    response = client.responses.create(model="gpt-5.3-codex", input="hi")

    assert response.id == "resp_1"
    assert response.output_text == "hello"
    assert response.output[0]["type"] == "message"
    assert response.usage is not None
    assert response.usage.cached_tokens == 2
    assert response.usage.reasoning_tokens == 1


def test_responses_create_continuity_check(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="response_started", response_id="resp_2")
        yield StreamEvent(
            type="response_completed",
            response_id="resp_2",
            raw={"id": "resp_2", "previous_response_id": "other"},
        )
        yield StreamEvent(type="done", response_id="resp_2")

    monkeypatch.setattr(client._engine, "_stream_responses_sync", fake_stream)

    with pytest.raises(ContinuityError):
        client.responses.create(
            model="gpt-5.3-codex",
            input="hi",
            previous_response_id="resp_1",
        )


def test_responses_create_structured_output_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    captured: dict[str, object] = {}

    def fake_sse(**kwargs):
        captured["payload"] = kwargs["payload"]
        captured["extra_headers"] = kwargs.get("extra_headers")
        captured["extra_query"] = kwargs.get("extra_query")
        yield StreamEvent(type="text_delta", delta="ok")
        yield StreamEvent(type="done")

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fake_sse)

    response = client.responses.create(
        model="gpt-5.3-codex",
        input="hi",
        tools=[{"type": "function", "name": "x", "parameters": {"type": "object"}}],
        response_format={"type": "json_object"},
        strict_output=True,
        max_tool_calls=4,
        parallel_tool_calls=False,
        truncation="auto",
        extra_headers={"X-OpenAI-Compat": "1"},
        extra_query={"source": "test"},
        extra_body={"tool_choice": "required", "custom_payload": "yes"},
    )

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["text"] == {"format": {"type": "json_object"}}
    assert payload["tools"][0]["strict"] is True
    assert payload["max_tool_calls"] == 4
    assert payload["parallel_tool_calls"] is False
    assert payload["truncation"] == "auto"
    assert payload["tool_choice"] == "required"
    assert payload["custom_payload"] == "yes"
    assert captured["extra_headers"] == {"X-OpenAI-Compat": "1"}
    assert captured["extra_query"] == {"source": "test"}
    assert response.output_text == "ok"
