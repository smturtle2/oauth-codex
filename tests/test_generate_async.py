from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from conftest import InMemoryTokenStore
from oauth_codex import Client
from oauth_codex.core_types import GenerateResult, OAuthTokens, StreamEvent, ToolCall


class ToolInput(BaseModel):
    query: str


class StructuredOutput(BaseModel):
    answer: str
    count: int


def _client() -> Client:
    return Client(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )


@pytest.mark.asyncio
async def test_agenerate_rejects_non_list_messages() -> None:
    client = _client()

    with pytest.raises(TypeError, match="non-empty list"):
        await client.agenerate("hello")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_agenerate_rejects_empty_messages() -> None:
    client = _client()

    with pytest.raises(ValueError, match="non-empty list"):
        await client.agenerate([])


@pytest.mark.asyncio
async def test_agenerate_preserves_mixed_content_message_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()
    captured: dict[str, object] = {}

    async def fake_agenerate(**kwargs):
        captured.update(kwargs)
        return GenerateResult(text="ok", tool_calls=[], finish_reason="stop")

    monkeypatch.setattr(client._engine, "agenerate", fake_agenerate)

    mixed_messages = [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "describe"},
                {"type": "input_image", "image_url": "https://example.com/cat.png"},
                {"type": "input_text", "text": "focus on the cat"},
            ],
        }
    ]
    out = await client.agenerate(messages=mixed_messages)

    assert out == "ok"
    assert captured["messages"] == mixed_messages


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

    out = await client.agenerate([{"role": "user", "content": "5+7"}], tools=[add_async])

    assert out == "12"
    assert calls[1]["previous_response_id"] == "resp_1"
    assert calls[1]["messages"] == []
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
    async for delta in client.astream([{"role": "user", "content": "calc"}], tools=[mul]):
        out.append(delta)

    assert out == ["X", "Y"]
    assert calls[1]["previous_response_id"] == "resp_1"
    assert calls[1]["messages"] == []
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

    out = await client.agenerate([{"role": "user", "content": "run"}], tools=[tool])

    assert out == "done"
    tool_results = calls[1]["tool_results"]
    assert tool_results[0].output == {"output": "Tool received query: hello"}


@pytest.mark.asyncio
async def test_agenerate_supports_structured_output_with_pydantic_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()
    captured: dict[str, object] = {}

    async def fake_agenerate(**kwargs):
        captured.update(kwargs)
        return GenerateResult(
            text='{"answer":"ok","count":1}',
            tool_calls=[],
            finish_reason="stop",
            response_id="resp_1",
        )

    monkeypatch.setattr(client._engine, "agenerate", fake_agenerate)

    out = await client.agenerate(
        [{"role": "user", "content": "return json"}],
        output_schema=StructuredOutput,
    )

    assert out == {"answer": "ok", "count": 1}
    response_format = captured["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["name"] == "StructuredOutput"
    assert response_format["strict"] is True
    assert response_format["schema"]["required"] == ["answer", "count"]
    assert captured["strict_output"] is True


@pytest.mark.asyncio
async def test_agenerate_structured_output_rejects_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()

    async def fake_agenerate(**kwargs):
        _ = kwargs
        return GenerateResult(
            text="not-json",
            tool_calls=[],
            finish_reason="stop",
        )

    monkeypatch.setattr(client._engine, "agenerate", fake_agenerate)

    with pytest.raises(ValueError, match="valid JSON"):
        await client.agenerate(
            [{"role": "user", "content": "return json"}],
            output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
        )


@pytest.mark.asyncio
async def test_agenerate_structured_output_enforces_pydantic_strict_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()

    async def fake_agenerate(**kwargs):
        _ = kwargs
        return GenerateResult(
            text='{"answer":"ok","count":"1"}',
            tool_calls=[],
            finish_reason="stop",
        )

    monkeypatch.setattr(client._engine, "agenerate", fake_agenerate)

    with pytest.raises(ValidationError):
        await client.agenerate(
            [{"role": "user", "content": "return json"}],
            output_schema=StructuredOutput,
        )


@pytest.mark.asyncio
async def test_astream_accepts_output_schema_and_keeps_text_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()
    calls: list[dict[str, object]] = []

    async def fake_astream(**kwargs):
        calls.append(kwargs)

        async def events():
            yield StreamEvent(type="text_delta", delta="{", response_id="resp_1")
            yield StreamEvent(type="text_delta", delta='"ok":true}', response_id="resp_1")
            yield StreamEvent(type="done", response_id="resp_1")

        return events()

    monkeypatch.setattr(client._engine, "agenerate_stream", fake_astream)

    out: list[str] = []
    async for delta in client.astream(
        messages=[{"role": "user", "content": "return json"}],
        output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
    ):
        out.append(delta)

    assert out == ["{", '"ok":true}']
    assert calls[0]["strict_output"] is True
    response_format = calls[0]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["strict"] is True
