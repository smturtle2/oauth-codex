from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import AsyncOAuthCodexClient, ContinuityError, OAuthCodexClient, SDKRequestError
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


def test_codex_previous_response_id_local_continuity_non_stream(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    client = OAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        ),
        compat_storage_dir=str(tmp_path),
    )
    captured_payloads: list[dict[str, object]] = []

    def fake_sse(**kwargs):
        payload = kwargs["payload"]
        assert isinstance(payload, dict)
        captured_payloads.append(
            {
                **payload,
                "input": [dict(item) for item in payload.get("input", []) if isinstance(item, dict)],
            }
        )
        idx = len(captured_payloads)
        response_id = f"resp_{idx}"
        text = "first" if idx == 1 else "second"
        output_item = {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": text}],
        }
        yield StreamEvent(type="response_started", response_id=response_id)
        yield StreamEvent(type="text_delta", delta=text, response_id=response_id)
        yield StreamEvent(
            type="response_completed",
            response_id=response_id,
            raw={"id": response_id, "output": [output_item]},
        )
        yield StreamEvent(type="done", response_id=response_id)

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fake_sse)

    first = client.responses.create(model="gpt-5.3-codex", input="hi")
    second = client.responses.create(
        model="gpt-5.3-codex",
        input="next",
        previous_response_id=first.id,
    )

    assert second.id == "resp_2"
    assert "previous_response_id" not in captured_payloads[1]
    second_input = captured_payloads[1]["input"]
    assert isinstance(second_input, list)
    assert second_input[0]["role"] == "user"
    assert second_input[0]["content"] == "hi"
    assert second_input[1]["type"] == "message"
    assert second_input[2]["role"] == "user"
    assert second_input[2]["content"] == "next"
    assert (tmp_path / "responses" / "index.json").exists()


def test_codex_previous_response_id_missing_returns_not_found(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    client = OAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        ),
        compat_storage_dir=str(tmp_path),
    )

    def fail_sse(**kwargs):
        _ = kwargs
        raise AssertionError("backend request should not be attempted when previous_response_id is missing")

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fail_sse)

    with pytest.raises(SDKRequestError) as exc:
        client.responses.create(
            model="gpt-5.3-codex",
            input="follow-up",
            previous_response_id="resp_missing",
        )

    assert exc.value.status_code == 404
    assert exc.value.provider_code == "not_found"


def test_codex_previous_response_id_local_continuity_stream_raw_events(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    client = OAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        ),
        compat_storage_dir=str(tmp_path),
    )
    captured_payloads: list[dict[str, object]] = []

    def fake_sse(**kwargs):
        payload = kwargs["payload"]
        assert isinstance(payload, dict)
        captured_payloads.append(
            {
                **payload,
                "input": [dict(item) for item in payload.get("input", []) if isinstance(item, dict)],
            }
        )
        idx = len(captured_payloads)
        response_id = f"resp_{idx}"
        text = f"stream-{idx}"
        output_item = {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": text}],
        }
        yield StreamEvent(type="response_started", response_id=response_id)
        yield StreamEvent(type="text_delta", delta=text, response_id=response_id)
        yield StreamEvent(
            type="response_completed",
            response_id=response_id,
            raw={"id": response_id, "output": [output_item]},
        )
        yield StreamEvent(type="done", response_id=response_id)

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fake_sse)

    first_events = list(client.responses.create(model="gpt-5.3-codex", input="hi", stream=True))
    second_events = list(
        client.responses.create(
            model="gpt-5.3-codex",
            input="later",
            previous_response_id="resp_1",
            stream=True,
        )
    )

    assert first_events[-1].type == "done"
    assert second_events[-1].type == "done"
    assert "previous_response_id" not in captured_payloads[1]
    second_input = captured_payloads[1]["input"]
    assert isinstance(second_input, list)
    assert second_input[0]["content"] == "hi"
    assert second_input[1]["type"] == "message"
    assert second_input[2]["content"] == "later"


def test_codex_previous_response_id_local_continuity_text_stream(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    client = OAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        ),
        compat_storage_dir=str(tmp_path),
    )
    captured_payloads: list[dict[str, object]] = []

    def fake_sse(**kwargs):
        payload = kwargs["payload"]
        assert isinstance(payload, dict)
        captured_payloads.append(
            {
                **payload,
                "input": [dict(item) for item in payload.get("input", []) if isinstance(item, dict)],
            }
        )
        idx = len(captured_payloads)
        response_id = f"resp_{idx}"
        text = f"text-{idx}"
        output_item = {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": text}],
        }
        yield StreamEvent(type="response_started", response_id=response_id)
        yield StreamEvent(type="text_delta", delta=text, response_id=response_id)
        yield StreamEvent(
            type="response_completed",
            response_id=response_id,
            raw={"id": response_id, "output": [output_item]},
        )
        yield StreamEvent(type="done", response_id=response_id)

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fake_sse)

    out1 = "".join(client.generate_stream(model="gpt-5.3-codex", prompt="hello"))
    out2 = "".join(
        client.generate_stream(
            model="gpt-5.3-codex",
            prompt="world",
            previous_response_id="resp_1",
        )
    )

    assert out1 == "text-1"
    assert out2 == "text-2"
    assert "previous_response_id" not in captured_payloads[1]
    second_input = captured_payloads[1]["input"]
    assert isinstance(second_input, list)
    assert second_input[0]["content"] == "hello"
    assert second_input[1]["type"] == "message"
    assert second_input[2]["content"] == "world"


def test_non_codex_profile_preserves_previous_response_id_passthrough(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = OAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        ),
        chatgpt_base_url="https://api.example.com/v1",
    )
    captured: dict[str, object] = {}

    def fake_sse(**kwargs):
        captured["payload"] = kwargs["payload"]
        yield StreamEvent(type="response_started", response_id="resp_1")
        yield StreamEvent(type="text_delta", delta="ok", response_id="resp_1")
        yield StreamEvent(type="response_completed", response_id="resp_1")
        yield StreamEvent(type="done", response_id="resp_1")

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fake_sse)

    client.responses.create(
        model="gpt-5.3-codex",
        input="hi",
        previous_response_id="resp_prev",
    )

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["previous_response_id"] == "resp_prev"


@pytest.mark.asyncio
async def test_codex_previous_response_id_local_continuity_non_stream_async(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    client = AsyncOAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        ),
        compat_storage_dir=str(tmp_path),
    )
    captured_payloads: list[dict[str, object]] = []

    async def fake_sse(**kwargs):
        payload = kwargs["payload"]
        assert isinstance(payload, dict)
        captured_payloads.append(
            {
                **payload,
                "input": [dict(item) for item in payload.get("input", []) if isinstance(item, dict)],
            }
        )
        idx = len(captured_payloads)
        response_id = f"resp_{idx}"
        text = f"async-{idx}"
        output_item = {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": text}],
        }
        yield StreamEvent(type="response_started", response_id=response_id)
        yield StreamEvent(type="text_delta", delta=text, response_id=response_id)
        yield StreamEvent(
            type="response_completed",
            response_id=response_id,
            raw={"id": response_id, "output": [output_item]},
        )
        yield StreamEvent(type="done", response_id=response_id)

    monkeypatch.setattr(client._engine, "_stream_sse_async", fake_sse)

    first = await client.responses.create(model="gpt-5.3-codex", input="hello")
    second = await client.responses.create(
        model="gpt-5.3-codex",
        input="again",
        previous_response_id=first.id,
    )

    assert first.id == "resp_1"
    assert second.id == "resp_2"
    assert "previous_response_id" not in captured_payloads[1]
    merged_input = captured_payloads[1]["input"]
    assert isinstance(merged_input, list)
    assert merged_input[0]["content"] == "hello"
    assert merged_input[1]["type"] == "message"
    assert merged_input[2]["content"] == "again"
