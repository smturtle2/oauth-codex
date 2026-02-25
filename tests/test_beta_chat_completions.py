from __future__ import annotations

from typing import Any, cast

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import AsyncClient, Client
from oauth_codex.core_types import OAuthTokens


def _client() -> Any:
    return cast(
        Any,
        Client(
            token_store=InMemoryTokenStore(
                OAuthTokens(
                    access_token="a", refresh_token="r", expires_at=9_999_999_999
                )
            )
        ),
    )


def _async_client() -> Any:
    return cast(
        Any,
        AsyncClient(
            token_store=InMemoryTokenStore(
                OAuthTokens(
                    access_token="a", refresh_token="r", expires_at=9_999_999_999
                )
            )
        ),
    )


class _StubResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def to_dict(self, **_kwargs: Any) -> dict[str, Any]:
        return self._payload


def test_chat_create_returns_tool_calls_without_auto_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()

    def fake_create(**_kwargs: Any) -> Any:
        return _StubResponse(
            {
                "id": "resp_1",
                "model": "gpt-5.3-codex",
                "output": [
                    {
                        "type": "function_call",
                        "call_id": "call_1",
                        "name": "get_weather",
                        "arguments": '{"city":"Seoul"}',
                    }
                ],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            }
        )

    monkeypatch.setattr(client.responses, "create", fake_create)

    completion = client.chat.completions.create(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "weather?"}],
        tools=[
            {
                "type": "function",
                "name": "get_weather",
                "parameters": {"type": "object"},
            }
        ],
    )

    message = completion.choices[0].message
    assert message.tool_calls is not None
    assert len(message.tool_calls) == 1
    assert message.tool_calls[0].function.name == "get_weather"
    assert completion.choices[0].finish_reason == "tool_calls"


def test_beta_run_tools_executes_callables(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client()
    captured_inputs: list[list[dict[str, Any]]] = []
    call_count = {"n": 0}

    def fake_create(**kwargs: Any) -> Any:
        call_count["n"] += 1
        captured_inputs.append(list(kwargs["input"]))
        if call_count["n"] == 1:
            return _StubResponse(
                {
                    "id": "resp_1",
                    "model": "gpt-5.3-codex",
                    "output": [
                        {
                            "type": "function_call",
                            "call_id": "call_1",
                            "name": "add",
                            "arguments": '{"a":1,"b":2}',
                        }
                    ],
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                }
            )
        return _StubResponse(
            {
                "id": "resp_2",
                "model": "gpt-5.3-codex",
                "output_text": "3",
                "usage": {"input_tokens": 2, "output_tokens": 1},
                "finish_reason": "stop",
            }
        )

    monkeypatch.setattr(client.responses, "create", fake_create)

    def add(a: int, b: int) -> int:
        return a + b

    completion = client.beta.chat.completions.run_tools(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "add"}],
        tools=[add],
    )

    assert completion.choices[0].message.content == "3"
    assert call_count["n"] == 2
    second_round_messages = captured_inputs[1]
    assert any(message.get("role") == "tool" for message in second_round_messages)


@pytest.mark.asyncio
async def test_beta_arun_tools_supports_async_callables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _async_client()
    call_count = {"n": 0}

    async def fake_create(**_kwargs: Any) -> Any:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _StubResponse(
                {
                    "id": "resp_1",
                    "model": "gpt-5.3-codex",
                    "output": [
                        {
                            "type": "function_call",
                            "call_id": "call_1",
                            "name": "aget_number",
                            "arguments": "{}",
                        }
                    ],
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                }
            )
        return _StubResponse(
            {
                "id": "resp_2",
                "model": "gpt-5.3-codex",
                "output_text": "7",
                "usage": {"input_tokens": 2, "output_tokens": 1},
                "finish_reason": "stop",
            }
        )

    monkeypatch.setattr(client.responses, "create", fake_create)

    async def aget_number() -> int:
        return 7

    completion = await client.beta.chat.completions.arun_tools(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "number"}],
        tools=[aget_number],
    )

    assert completion.choices[0].message.content == "7"
    assert call_count["n"] == 2
