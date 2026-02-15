from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex._engine import OAuthCodexClient as EngineClient
from oauth_codex.core_types import OAuthTokens, ToolResult
from oauth_codex.errors import SDKRequestError
from oauth_codex.tooling import tool_results_to_response_items


def _engine() -> EngineClient:
    return EngineClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )


def test_map_stream_restores_call_id_from_item_id_on_response_completed() -> None:
    engine = _engine()

    delta_events = engine._map_responses_stream(
        "message",
        {"type": "response.function_call_arguments.delta", "item_id": "fc_123", "delta": '{"x":'},
    )
    assert len(delta_events) == 1
    assert delta_events[0].type == "tool_call_arguments_delta"
    assert delta_events[0].call_id is None

    done_events = engine._map_responses_stream(
        "message",
        {"type": "response.function_call_arguments.done", "item_id": "fc_123", "arguments": '{"x":1}'},
    )
    assert not [event for event in done_events if event.type == "tool_call_done"]

    completed_events = engine._map_responses_stream(
        "message",
        {
            "type": "response.completed",
            "response": {
                "id": "resp_1",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_123",
                        "call_id": "call_abc",
                        "name": "tool",
                        "arguments": '{"x":1}',
                    }
                ],
            },
        },
    )
    done = [event for event in completed_events if event.type == "tool_call_done"]
    assert len(done) == 1
    assert done[0].tool_call is not None
    assert done[0].tool_call.id == "call_abc"
    assert any(event.type == "response_completed" for event in completed_events)


def test_map_stream_raises_when_call_id_cannot_be_restored() -> None:
    engine = _engine()

    engine._map_responses_stream(
        "message",
        {"type": "response.function_call_arguments.done", "item_id": "fc_missing", "arguments": "{}"},
    )

    with pytest.raises(SDKRequestError) as exc_info:
        engine._map_responses_stream(
            "message",
            {"type": "response.completed", "response": {"id": "resp_1", "output": []}},
        )
    assert exc_info.value.provider_code == "tool_call_id_unresolved"


def test_tool_results_to_response_items_rejects_empty_tool_call_id() -> None:
    with pytest.raises(SDKRequestError) as exc_info:
        tool_results_to_response_items([ToolResult(tool_call_id="  ", name="tool", output={"ok": True})])
    assert exc_info.value.provider_code == "invalid_tool_call_id"


def test_build_effective_responses_input_sanitizes_legacy_continuity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _engine()

    legacy_continuation = [
        {
            "type": "message",
            "id": "msg_1",
            "status": "completed",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "hello", "annotations": [{"x": 1}]}],
        },
        {"type": "reasoning_summary", "id": "rs_1", "summary": "drop this"},
        {
            "type": "function_call",
            "id": "fc_1",
            "status": "completed",
            "call_id": "call_1",
            "name": "tool",
            "arguments": "{}",
        },
        {
            "type": "function_call_output",
            "id": "fco_1",
            "status": "completed",
            "call_id": "call_1",
            "output": {"ok": True},
        },
        {"id": "msg_user", "role": "user", "content": "next"},
    ]

    monkeypatch.setattr(
        engine._compat_store,
        "get_response_continuity",
        lambda _response_id: {"continuation_input": legacy_continuation},
    )

    effective_input, upstream_previous_response_id = engine._build_effective_responses_input(
        messages=[{"role": "user", "content": "current turn"}],
        tool_results=[],
        previous_response_id="resp_prev",
    )

    assert upstream_previous_response_id is None
    assert not any(item.get("type") == "reasoning_summary" for item in effective_input)
    assert any(item.get("type") == "function_call" for item in effective_input)
    assert any(item.get("type") == "function_call_output" for item in effective_input)
    assert all("id" not in item for item in effective_input)
    assert all("status" not in item for item in effective_input)


def test_extract_output_items_for_continuation_sanitizes_response_output() -> None:
    engine = _engine()

    raw_response = {
        "response": {
            "id": "resp_1",
            "output": [
                {
                    "type": "message",
                    "id": "msg_1",
                    "status": "completed",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "hello", "annotations": [{"x": 1}]}],
                },
                {"type": "reasoning_summary", "id": "rs_1", "summary": "drop this"},
                {
                    "type": "function_call",
                    "id": "fc_1",
                    "status": "completed",
                    "call_id": "call_1",
                    "name": "tool",
                    "arguments": "{}",
                },
            ],
        }
    }

    items = engine._extract_output_items_for_continuation(
        raw_response=raw_response,
        text_parts=["hello"],
        tool_calls=[],
    )
    assert [item.get("type") for item in items] == ["message", "function_call"]
    assert all("id" not in item for item in items)
    assert all("status" not in item for item in items)
