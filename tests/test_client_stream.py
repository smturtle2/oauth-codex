from __future__ import annotations

import pytest

from oauth_codex.client import CodexOAuthLLM
from oauth_codex.types import OAuthConfig, OAuthTokens, StreamEvent
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


def test_generate_stream_returns_text_deltas(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = _llm()

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="text_delta", delta="hel")
        yield StreamEvent(type="text_delta", delta="lo")
        yield StreamEvent(type="done")

    monkeypatch.setattr(llm, "_stream_responses_sync", fake_stream)

    chunks = list(
        llm.generate_stream(
            model="gpt-5.3-codex",
            prompt="hi",
        )
    )

    assert chunks == ["hel", "lo"]


def test_generate_stream_requires_raw_events_when_tools_present(valid_tokens: OAuthTokens) -> None:
    llm = CodexOAuthLLM(token_store=InMemoryTokenStore(valid_tokens))

    with pytest.raises(ValueError):
        list(
            llm.generate_stream(
                model="gpt-5.3-codex",
                messages=[{"role": "user", "content": "hi"}],
                tools=[{"type": "function", "name": "x", "parameters": {"type": "object"}}],
                raw_events=False,
            )
        )


def test_generate_stream_raw_events_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = _llm()

    def fake_stream(**kwargs):
        _ = kwargs
        yield StreamEvent(type="tool_call_delta", delta='{"city":')
        yield StreamEvent(type="tool_call_done")
        yield StreamEvent(type="done")

    monkeypatch.setattr(llm, "_stream_responses_sync", fake_stream)

    events = list(
        llm.generate_stream(
            model="gpt-5.3-codex",
            messages=[{"role": "user", "content": "hi"}],
            tools=[{"type": "function", "name": "x", "parameters": {"type": "object"}}],
            raw_events=True,
        )
    )

    assert [e.type for e in events] == ["tool_call_delta", "tool_call_done", "done"]


def test_map_responses_stream_tool_call_lifecycle() -> None:
    llm = _llm()

    payload_delta = {
        "type": "response.function_call_arguments.delta",
        "delta": '{"city":"Se',
    }
    payload_done = {
        "type": "response.function_call_arguments.done",
        "call_id": "call_1",
        "name": "get_weather",
        "arguments": '{"city":"Seoul"}',
    }

    events1 = llm._map_responses_stream("response.function_call_arguments.delta", payload_delta)
    events2 = llm._map_responses_stream("response.function_call_arguments.done", payload_done)
    merged = [*events1, *events2]

    assert any(e.type == "tool_call_delta" for e in merged)
    done = [e for e in merged if e.type == "tool_call_done"]
    assert len(done) == 1
    assert done[0].tool_call is not None
    assert done[0].tool_call.name == "get_weather"
    assert done[0].tool_call.arguments == {"city": "Seoul"}


def test_map_responses_stream_usage_and_done() -> None:
    llm = _llm()

    usage_payload = {
        "type": "response.completed",
        "usage": {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
            "input_tokens_details": {"cached_tokens": 2},
            "output_tokens_details": {"reasoning_tokens": 1},
        },
    }

    events = llm._map_responses_stream("response.completed", usage_payload)

    assert any(e.type == "usage" for e in events)
    assert any(e.type == "done" for e in events)
