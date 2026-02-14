from __future__ import annotations

from conftest import InMemoryTokenStore
from oauth_codex.client import CodexOAuthLLM
from oauth_codex.types import OAuthTokens


def _llm() -> CodexOAuthLLM:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    return CodexOAuthLLM(token_store=store)


def test_tool_call_event_lifecycle_and_call_id() -> None:
    llm = _llm()

    delta_events = llm._map_responses_stream(
        "response.function_call_arguments.delta",
        {
            "type": "response.function_call_arguments.delta",
            "call_id": "call_1",
            "name": "get_weather",
            "delta": '{"city":"Se',
        },
    )
    done_events = llm._map_responses_stream(
        "response.function_call_arguments.done",
        {
            "type": "response.function_call_arguments.done",
            "call_id": "call_1",
            "name": "get_weather",
            "arguments": '{"city":"Seoul"}',
        },
    )

    started = [e for e in delta_events if e.type == "tool_call_started"]
    arg_delta = [e for e in delta_events if e.type == "tool_call_arguments_delta"]
    done = [e for e in done_events if e.type == "tool_call_done"]

    assert len(started) == 1
    assert len(arg_delta) == 1
    assert len(done) == 1
    assert started[0].call_id == "call_1"
    assert arg_delta[0].call_id == "call_1"
    assert done[0].tool_call is not None
    assert done[0].tool_call.id == "call_1"
    assert done[0].tool_call.arguments == {"city": "Seoul"}
