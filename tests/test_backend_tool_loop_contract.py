from __future__ import annotations

from typing import Any, cast

import pytest

import oauth_codex
from conftest import InMemoryTokenStore
from oauth_codex.core_types import OAuthTokens


def _client() -> Any:
    return cast(
        Any,
        oauth_codex.Client(
            token_store=InMemoryTokenStore(
                OAuthTokens(
                    access_token="a",
                    refresh_token="r",
                    expires_at=9_999_999_999,
                )
            )
        ),
    )


def _async_client() -> Any:
    async_client_cls = cast(Any, getattr(oauth_codex, "AsyncClient"))
    return cast(
        Any,
        async_client_cls(
            token_store=InMemoryTokenStore(
                OAuthTokens(
                    access_token="a",
                    refresh_token="r",
                    expires_at=9_999_999_999,
                )
            )
        ),
    )


class _StubResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def to_dict(self, **_kwargs: Any) -> dict[str, Any]:
        return self._payload


def test_run_tools_uses_previous_response_id_and_function_call_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()
    captured_calls: list[dict[str, Any]] = []
    call_count = {"n": 0}

    def fake_create(**kwargs: Any) -> Any:
        call_count["n"] += 1
        captured_calls.append(dict(kwargs))
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
                            "arguments": '{"a":5,"b":7}',
                        }
                    ],
                    "finish_reason": "tool_calls",
                }
            )
        return _StubResponse(
            {
                "id": "resp_2",
                "model": "gpt-5.3-codex",
                "output_text": "12",
                "finish_reason": "stop",
            }
        )

    monkeypatch.setattr(client.responses, "create", fake_create)

    def add(a: int, b: int) -> int:
        return a + b

    completion = client.beta.chat.completions.run_tools(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "5+7"}],
        tools=[add],
    )

    assert completion.choices[0].message.content == "12"
    assert call_count["n"] == 2
    assert "previous_response_id" not in captured_calls[0]
    assert captured_calls[1]["previous_response_id"] == "resp_1"
    assert captured_calls[1]["input"] == [
        {
            "type": "function_call_output",
            "call_id": "call_1",
            "output": "12",
        }
    ]


def test_run_tools_keeps_first_previous_response_id_then_rolls_forward(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()
    captured_calls: list[dict[str, Any]] = []
    call_count = {"n": 0}

    def fake_create(**kwargs: Any) -> Any:
        call_count["n"] += 1
        captured_calls.append(dict(kwargs))
        if call_count["n"] == 1:
            return _StubResponse(
                {
                    "id": "resp_after_first",
                    "model": "gpt-5.3-codex",
                    "output": [
                        {
                            "type": "function_call",
                            "call_id": "call_1",
                            "name": "tool_name",
                            "arguments": "{}",
                        }
                    ],
                }
            )
        return _StubResponse(
            {
                "id": "resp_done",
                "model": "gpt-5.3-codex",
                "output_text": "ok",
            }
        )

    monkeypatch.setattr(client.responses, "create", fake_create)

    def tool_name() -> str:
        return "ok"

    completion = client.beta.chat.completions.run_tools(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "do it"}],
        tools=[tool_name],
        previous_response_id="resp_seed",
    )

    assert completion.choices[0].message.content == "ok"
    assert call_count["n"] == 2
    assert captured_calls[0]["previous_response_id"] == "resp_seed"
    assert captured_calls[1]["previous_response_id"] == "resp_after_first"


def test_run_tools_serializes_non_string_tool_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()
    captured_calls: list[dict[str, Any]] = []
    call_count = {"n": 0}

    def fake_create(**kwargs: Any) -> Any:
        call_count["n"] += 1
        captured_calls.append(dict(kwargs))
        if call_count["n"] == 1:
            return _StubResponse(
                {
                    "id": "resp_1",
                    "model": "gpt-5.3-codex",
                    "output": [
                        {
                            "type": "function_call",
                            "call_id": "call_json",
                            "name": "tool_json",
                            "arguments": "{}",
                        }
                    ],
                }
            )
        return _StubResponse(
            {
                "id": "resp_2",
                "model": "gpt-5.3-codex",
                "output_text": "done",
            }
        )

    monkeypatch.setattr(client.responses, "create", fake_create)

    def tool_json() -> dict[str, Any]:
        return {"ok": True, "count": 2}

    completion = client.beta.chat.completions.run_tools(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "json"}],
        tools=[tool_json],
    )

    assert completion.choices[0].message.content == "done"
    assert call_count["n"] == 2
    assert captured_calls[1]["input"][0]["type"] == "function_call_output"
    assert captured_calls[1]["input"][0]["call_id"] == "call_json"
    assert captured_calls[1]["input"][0]["output"] == '{"ok": true, "count": 2}'


@pytest.mark.asyncio
async def test_arun_tools_contract_matches_responses_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _async_client()
    captured_calls: list[dict[str, Any]] = []
    call_count = {"n": 0}

    async def fake_create(**kwargs: Any) -> Any:
        call_count["n"] += 1
        captured_calls.append(dict(kwargs))
        if call_count["n"] == 1:
            return _StubResponse(
                {
                    "id": "resp_async_1",
                    "model": "gpt-5.3-codex",
                    "output": [
                        {
                            "type": "function_call",
                            "call_id": "call_async_1",
                            "name": "aget_number",
                            "arguments": "{}",
                        }
                    ],
                    "finish_reason": "tool_calls",
                }
            )
        return _StubResponse(
            {
                "id": "resp_async_2",
                "model": "gpt-5.3-codex",
                "output_text": "7",
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
    assert captured_calls[1]["previous_response_id"] == "resp_async_1"
    assert captured_calls[1]["input"] == [
        {
            "type": "function_call_output",
            "call_id": "call_async_1",
            "output": "7",
        }
    ]


def test_run_tools_handles_multi_round_and_multi_tool_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client()
    captured_calls: list[dict[str, Any]] = []
    call_count = {"n": 0}

    def fake_create(**kwargs: Any) -> Any:
        call_count["n"] += 1
        captured_calls.append(dict(kwargs))
        if call_count["n"] == 1:
            return _StubResponse(
                {
                    "id": "resp_round_1",
                    "model": "gpt-5.3-codex",
                    "output": [
                        {
                            "type": "function_call",
                            "call_id": "call_add",
                            "name": "add",
                            "arguments": '{"a":2,"b":3}',
                        },
                        {
                            "type": "function_call",
                            "call_id": "call_subtract",
                            "name": "subtract",
                            "arguments": '{"a":10,"b":4}',
                        },
                    ],
                    "finish_reason": "tool_calls",
                }
            )
        if call_count["n"] == 2:
            return _StubResponse(
                {
                    "id": "resp_round_2",
                    "model": "gpt-5.3-codex",
                    "output": [
                        {
                            "type": "function_call",
                            "call_id": "call_join",
                            "name": "join_values",
                            "arguments": '{"left":5,"right":6}',
                        }
                    ],
                    "finish_reason": "tool_calls",
                }
            )
        return _StubResponse(
            {
                "id": "resp_final",
                "model": "gpt-5.3-codex",
                "output_text": "5,6",
                "finish_reason": "stop",
            }
        )

    monkeypatch.setattr(client.responses, "create", fake_create)

    def add(a: int, b: int) -> int:
        return a + b

    def subtract(a: int, b: int) -> int:
        return a - b

    def join_values(left: int, right: int) -> str:
        return f"{left},{right}"

    completion = client.beta.chat.completions.run_tools(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "tools chain"}],
        tools=[add, subtract, join_values],
    )

    assert completion.choices[0].message.content == "5,6"
    assert call_count["n"] == 3
    assert captured_calls[1]["previous_response_id"] == "resp_round_1"
    assert captured_calls[1]["input"] == [
        {
            "type": "function_call_output",
            "call_id": "call_add",
            "output": "5",
        },
        {
            "type": "function_call_output",
            "call_id": "call_subtract",
            "output": "6",
        },
    ]
    assert captured_calls[2]["previous_response_id"] == "resp_round_2"
    assert captured_calls[2]["input"] == [
        {
            "type": "function_call_output",
            "call_id": "call_join",
            "output": "5,6",
        }
    ]
