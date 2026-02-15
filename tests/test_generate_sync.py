from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import Client
from oauth_codex.core_types import GenerateResult, OAuthTokens, StreamEvent, ToolCall


def _client() -> Client:
    return Client(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )


def test_generate_uses_default_model_and_reasoning_effort(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    captured: dict[str, object] = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return GenerateResult(text="ok", tool_calls=[], finish_reason="stop")

    monkeypatch.setattr(client._engine, "generate", fake_generate)

    out = client.generate("hello")

    assert out == "ok"
    assert captured["model"] == "gpt-5.3-codex"
    assert captured["reasoning"] == {"effort": "medium"}


def test_generate_accepts_url_and_local_image_inputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    client = _client()
    captured: dict[str, object] = {}

    image_path = tmp_path / "photo.png"
    image_path.write_bytes(b"PNGDATA")

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return GenerateResult(text="ok", tool_calls=[], finish_reason="stop")

    monkeypatch.setattr(client._engine, "generate", fake_generate)

    out = client.generate(
        "describe",
        images=["https://example.com/cat.png", image_path],
    )

    assert out == "ok"
    messages = captured["messages"]
    assert isinstance(messages, list)
    content = messages[0]["content"]
    assert content[0]["type"] == "input_text"
    assert content[1] == {"type": "input_image", "image_url": "https://example.com/cat.png"}
    assert content[2]["type"] == "input_image"
    assert content[2]["image_url"].startswith("data:image/png;base64,")


def test_generate_auto_function_calling(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    calls: list[dict[str, object]] = []

    def fake_generate(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return GenerateResult(
                text="",
                tool_calls=[ToolCall(id="call_1", name="add", arguments_json='{"a":2,"b":3}')],
                finish_reason="tool_calls",
                response_id="resp_1",
            )
        return GenerateResult(text="5", tool_calls=[], finish_reason="stop", response_id="resp_2")

    monkeypatch.setattr(client._engine, "generate", fake_generate)

    def add(a: int, b: int) -> dict[str, int]:
        return {"sum": a + b}

    out = client.generate("2+3", tools=[add])

    assert out == "5"
    assert calls[1]["previous_response_id"] == "resp_1"
    tool_results = calls[1]["tool_results"]
    assert len(tool_results) == 1
    assert tool_results[0].name == "add"
    assert tool_results[0].output == {"sum": 5}


def test_generate_tool_failure_is_forwarded_to_model(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    calls: list[dict[str, object]] = []

    def fake_generate(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return GenerateResult(
                text="",
                tool_calls=[ToolCall(id="call_1", name="bad_tool", arguments_json='{"x":1}')],
                finish_reason="tool_calls",
                response_id="resp_1",
            )
        return GenerateResult(text="handled", tool_calls=[], finish_reason="stop", response_id="resp_2")

    monkeypatch.setattr(client._engine, "generate", fake_generate)

    def bad_tool(x: int) -> str:
        _ = x
        raise ValueError("boom")

    out = client.generate("run", tools=[bad_tool])

    assert out == "handled"
    tool_results = calls[1]["tool_results"]
    assert tool_results[0].output == {"error": "boom"}


def test_generate_raises_when_tool_round_limit_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    client.max_tool_rounds = 2

    def fake_generate(**kwargs):
        _ = kwargs
        return GenerateResult(
            text="",
            tool_calls=[ToolCall(id="call_1", name="loop", arguments_json="{}")],
            finish_reason="tool_calls",
            response_id="resp_loop",
        )

    monkeypatch.setattr(client._engine, "generate", fake_generate)

    def loop() -> dict[str, bool]:
        return {"ok": True}

    with pytest.raises(RuntimeError, match="exceeded"):
        client.generate("loop", tools=[loop])


def test_stream_supports_tool_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    calls: list[dict[str, object]] = []

    def fake_stream(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            yield StreamEvent(type="text_delta", delta="A", response_id="resp_1")
            yield StreamEvent(
                type="tool_call_done",
                tool_call=ToolCall(id="call_1", name="add", arguments_json='{"a":1,"b":2}'),
                response_id="resp_1",
            )
            yield StreamEvent(type="done", response_id="resp_1")
            return

        yield StreamEvent(type="text_delta", delta="B", response_id="resp_2")
        yield StreamEvent(type="done", response_id="resp_2")

    monkeypatch.setattr(client._engine, "generate_stream", fake_stream)

    def add(a: int, b: int) -> dict[str, int]:
        return {"sum": a + b}

    out = list(client.stream("calc", tools=[add]))

    assert out == ["A", "B"]
    assert calls[1]["previous_response_id"] == "resp_1"
    tool_results = calls[1]["tool_results"]
    assert tool_results[0].output == {"sum": 3}
