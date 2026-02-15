from __future__ import annotations

import pytest
from pydantic import BaseModel

from conftest import InMemoryTokenStore
from oauth_codex import Client
from oauth_codex.core_types import GenerateResult, OAuthTokens, StreamEvent, ToolCall


class ToolInput(BaseModel):
    query: str


def _client() -> Client:
    return Client(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )


@pytest.mark.asyncio
async def test_agenerate_auto_function_calling(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    calls: list[dict[str, object]] = []

    async def fake_agenerate(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return GenerateResult(
                text="",
                tool_calls=[ToolCall(id="call_1", name="add_async", arguments_json='{"a":5,"b":7}')],
                finish_reason="tool_calls",
                response_id="resp_1",
            )
        return GenerateResult(text="12", tool_calls=[], finish_reason="stop", response_id="resp_2")

    monkeypatch.setattr(client._engine, "agenerate", fake_agenerate)

    async def add_async(a: int, b: int) -> dict[str, int]:
        return {"sum": a + b}

    out = await client.agenerate("5+7", tools=[add_async])

    assert out == "12"
    assert calls[1]["previous_response_id"] == "resp_1"
    tool_results = calls[1]["tool_results"]
    assert tool_results[0].output == {"sum": 12}


@pytest.mark.asyncio
async def test_astream_supports_tool_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    calls: list[dict[str, object]] = []

    async def fake_astream(**kwargs):
        calls.append(kwargs)

        async def first_round():
            yield StreamEvent(type="text_delta", delta="X", response_id="resp_1")
            yield StreamEvent(
                type="tool_call_done",
                tool_call=ToolCall(id="call_1", name="mul", arguments_json='{"a":3,"b":4}'),
                response_id="resp_1",
            )
            yield StreamEvent(type="done", response_id="resp_1")

        async def second_round():
            yield StreamEvent(type="text_delta", delta="Y", response_id="resp_2")
            yield StreamEvent(type="done", response_id="resp_2")

        if len(calls) == 1:
            return first_round()
        return second_round()

    monkeypatch.setattr(client._engine, "agenerate_stream", fake_astream)

    def mul(a: int, b: int) -> dict[str, int]:
        return {"product": a * b}

    out: list[str] = []
    async for delta in client.astream("calc", tools=[mul]):
        out.append(delta)

    assert out == ["X", "Y"]
    assert calls[1]["previous_response_id"] == "resp_1"
    tool_results = calls[1]["tool_results"]
    assert tool_results[0].output == {"product": 12}


@pytest.mark.asyncio
async def test_agenerate_supports_single_pydantic_tool_input(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    calls: list[dict[str, object]] = []

    async def fake_agenerate(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return GenerateResult(
                text="",
                tool_calls=[ToolCall(id="call_1", name="tool", arguments_json='{"query":"hello"}')],
                finish_reason="tool_calls",
                response_id="resp_1",
            )
        return GenerateResult(text="done", tool_calls=[], finish_reason="stop", response_id="resp_2")

    monkeypatch.setattr(client._engine, "agenerate", fake_agenerate)

    def tool(input: ToolInput) -> str:
        return f"Tool received query: {input.query}"

    out = await client.agenerate("run", tools=[tool])

    assert out == "done"
    tool_results = calls[1]["tool_results"]
    assert tool_results[0].output == {"output": "Tool received query: hello"}
