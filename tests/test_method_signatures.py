from __future__ import annotations

import inspect

import oauth_codex
import pytest

from conftest import InMemoryTokenStore
from oauth_codex import AsyncOAuthCodexClient, OAuthCodexClient
from oauth_codex._module_client import _reset_client
from oauth_codex.core_types import OAuthTokens, ResponseCompat, StreamEvent


def _sync_client() -> OAuthCodexClient:
    return OAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )


def _async_client() -> AsyncOAuthCodexClient:
    return AsyncOAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )


def _assert_has_varkw(sig: inspect.Signature) -> None:
    assert any(param.kind == inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values())


def test_responses_signatures_expose_core_parameters() -> None:
    client = _sync_client()

    create_params = inspect.signature(client.responses.create).parameters
    expected_create = [
        "model",
        "input",
        "messages",
        "tools",
        "tool_results",
        "response_format",
        "tool_choice",
        "strict_output",
        "store",
        "reasoning",
        "previous_response_id",
        "instructions",
        "temperature",
        "top_p",
        "max_output_tokens",
        "metadata",
        "include",
        "max_tool_calls",
        "parallel_tool_calls",
        "truncation",
        "extra_headers",
        "extra_query",
        "extra_body",
        "service_tier",
        "stream",
        "validation_mode",
    ]
    for name in expected_create:
        assert name in create_params
    _assert_has_varkw(inspect.signature(client.responses.create))

    stream_params = inspect.signature(client.responses.stream).parameters
    assert "stream" not in stream_params
    for name in [item for item in expected_create if item != "stream"]:
        assert name in stream_params
    _assert_has_varkw(inspect.signature(client.responses.stream))


def test_async_responses_signatures_expose_core_parameters() -> None:
    client = _async_client()
    create_sig = inspect.signature(client.responses.create)
    stream_sig = inspect.signature(client.responses.stream)

    assert "model" in create_sig.parameters
    assert "stream" in create_sig.parameters
    _assert_has_varkw(create_sig)

    assert "model" in stream_sig.parameters
    assert "stream" not in stream_sig.parameters
    _assert_has_varkw(stream_sig)


def test_vector_store_root_signatures_expose_named_parameters() -> None:
    client = _sync_client()

    create_params = inspect.signature(client.vector_stores.create).parameters
    for name in ["name", "file_ids", "metadata", "expires_after"]:
        assert name in create_params
    _assert_has_varkw(inspect.signature(client.vector_stores.create))

    list_params = inspect.signature(client.vector_stores.list).parameters
    for name in ["after", "before", "limit", "order"]:
        assert name in list_params
    _assert_has_varkw(inspect.signature(client.vector_stores.list))

    update_params = inspect.signature(client.vector_stores.update).parameters
    for name in ["vector_store_id", "name", "file_ids", "metadata", "expires_after"]:
        assert name in update_params
    _assert_has_varkw(inspect.signature(client.vector_stores.update))

    search_params = inspect.signature(client.vector_stores.search).parameters
    for name in ["vector_store_id", "query", "max_num_results", "filters", "ranking_options", "rewrite_query"]:
        assert name in search_params
    _assert_has_varkw(inspect.signature(client.vector_stores.search))


def test_module_level_signatures_match_named_parameters() -> None:
    _reset_client()
    try:
        responses_sig = inspect.signature(oauth_codex.responses.create)
        assert "model" in responses_sig.parameters
        assert "stream" in responses_sig.parameters
        _assert_has_varkw(responses_sig)

        vector_create_sig = inspect.signature(oauth_codex.vector_stores.create)
        for name in ["name", "file_ids", "metadata", "expires_after"]:
            assert name in vector_create_sig.parameters
        _assert_has_varkw(vector_create_sig)
    finally:
        _reset_client()


def test_responses_create_and_stream_forward_named_and_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _sync_client()
    captured_create: dict[str, object] = {}
    captured_stream: dict[str, object] = {}

    def fake_create(**kwargs):
        captured_create.update(kwargs)
        return ResponseCompat(id="resp_sig", output_text="ok")

    def fake_stream(**kwargs):
        captured_stream.update(kwargs)
        yield StreamEvent(type="response_started", response_id="resp_stream")
        yield StreamEvent(type="done", response_id="resp_stream")

    monkeypatch.setattr(client._engine, "responses_create", fake_create)
    out = client.responses.create(
        model="gpt-5.3-codex",
        input="hello",
        top_p=0.5,
        custom_flag=True,
    )
    assert out.id == "resp_sig"
    assert captured_create["model"] == "gpt-5.3-codex"
    assert captured_create["input"] == "hello"
    assert captured_create["top_p"] == 0.5
    assert captured_create["custom_flag"] is True
    assert captured_create["stream"] is False

    monkeypatch.setattr(client._engine, "responses_create", fake_stream)
    events = list(
        client.responses.stream(
            model="gpt-5.3-codex",
            input="hello",
            validation_mode="warn",
            extra_debug=True,
        )
    )
    assert events[0].type == "response_started"
    assert captured_stream["stream"] is True
    assert captured_stream["validation_mode"] == "warn"
    assert captured_stream["extra_debug"] is True


def test_vector_store_methods_forward_named_and_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _sync_client()
    calls: list[dict[str, object]] = []

    def fake_vector_store_request(*, method: str, path: str, payload: dict[str, object]):
        calls.append({"method": method, "path": path, "payload": dict(payload)})
        if method == "GET" and path == "/vector_stores":
            return {"object": "list", "data": []}
        if method == "POST" and path.endswith("/search"):
            return {"object": "list", "data": []}
        vector_id = "vs_sig"
        if path.startswith("/vector_stores/") and path.count("/") == 2:
            vector_id = path.rsplit("/", 1)[-1]
        return {
            "id": vector_id,
            "object": "vector_store",
            "created_at": 1,
            "name": payload.get("name"),
            "metadata": payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
            "file_ids": payload.get("file_ids") if isinstance(payload.get("file_ids"), list) else [],
            "status": "completed",
        }

    monkeypatch.setattr(client._engine, "vector_store_request", fake_vector_store_request)

    created = client.vector_stores.create(
        name="docs",
        file_ids=["file_1"],
        metadata={"team": "sdk"},
        expires_after={"anchor": "last_active_at", "days": 7},
        custom_create=True,
    )
    assert created.id == "vs_sig"

    listed = client.vector_stores.list(after="a", before="b", limit=5, order="desc", custom_list=True)
    assert listed["object"] == "list"

    updated = client.vector_stores.update(
        "vs_sig",
        name="docs-v2",
        metadata={"team": "sdk2"},
        custom_update=True,
    )
    assert updated.id == "vs_sig"

    searched = client.vector_stores.search(
        "vs_sig",
        query="alpha",
        max_num_results=3,
        filters={"type": "eq"},
        ranking_options={"ranker": "default_2024_08_21"},
        rewrite_query=True,
        custom_search=True,
    )
    assert searched["object"] == "list"

    create_payload = calls[0]["payload"]
    assert create_payload["name"] == "docs"
    assert create_payload["file_ids"] == ["file_1"]
    assert create_payload["metadata"] == {"team": "sdk"}
    assert create_payload["expires_after"] == {"anchor": "last_active_at", "days": 7}
    assert create_payload["custom_create"] is True

    list_payload = calls[1]["payload"]
    assert list_payload["after"] == "a"
    assert list_payload["before"] == "b"
    assert list_payload["limit"] == 5
    assert list_payload["order"] == "desc"
    assert list_payload["custom_list"] is True

    update_payload = calls[2]["payload"]
    assert update_payload["name"] == "docs-v2"
    assert update_payload["metadata"] == {"team": "sdk2"}
    assert update_payload["custom_update"] is True

    search_payload = calls[3]["payload"]
    assert search_payload["query"] == "alpha"
    assert search_payload["max_num_results"] == 3
    assert search_payload["filters"] == {"type": "eq"}
    assert search_payload["ranking_options"] == {"ranker": "default_2024_08_21"}
    assert search_payload["rewrite_query"] is True
    assert search_payload["custom_search"] is True


def test_removed_methods_absent() -> None:
    client = _sync_client()
    assert not hasattr(client.responses, "retrieve")
    assert not hasattr(client.responses, "cancel")
    assert not hasattr(client.responses, "delete")
    assert not hasattr(client.responses, "compact")
    assert not hasattr(client.responses, "parse")
    assert not hasattr(client.responses, "input_items")
    assert not hasattr(client.models, "delete")
    assert not hasattr(client.vector_stores.files, "update")


def test_stream_events_do_not_emit_tool_call_delta_alias() -> None:
    client = _sync_client()
    events = client._engine._map_responses_stream(
        "response.function_call_arguments.delta",
        {
            "type": "response.function_call_arguments.delta",
            "id": "call_1",
            "name": "tool_1",
            "delta": "{\"a\":",
        },
    )
    event_types = [event.type for event in events]
    assert "tool_call_arguments_delta" in event_types
    assert "tool_call_delta" not in event_types
