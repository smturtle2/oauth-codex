from __future__ import annotations

import io
from pathlib import Path

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import AsyncOAuthCodexClient, OAuthCodexClient, SDKRequestError
from oauth_codex.types import OAuthTokens, StreamEvent


def _tokens() -> OAuthTokens:
    return OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)


def test_local_compat_storage_persists_between_clients(tmp_path) -> None:
    first = OAuthCodexClient(
        token_store=InMemoryTokenStore(_tokens()),
        compat_storage_dir=str(tmp_path),
    )
    file_out = first.files.create(file=io.BytesIO(b"alpha beta gamma"), purpose="assistants")
    vector_out = first.vector_stores.create(name="docs", file_ids=[file_out["id"]])

    second = OAuthCodexClient(
        token_store=InMemoryTokenStore(_tokens()),
        compat_storage_dir=str(tmp_path),
    )
    retrieved = second.vector_stores.retrieve(vector_out["id"])
    searched = second.vector_stores.search(vector_out["id"], query="alpha")

    assert retrieved["id"] == vector_out["id"]
    assert searched["data"][0]["file_id"] == file_out["id"]


def test_local_compat_not_found_returns_sdk_request_error(tmp_path) -> None:
    client = OAuthCodexClient(
        token_store=InMemoryTokenStore(_tokens()),
        compat_storage_dir=str(tmp_path),
    )

    with pytest.raises(SDKRequestError) as exc:
        client.vector_stores.retrieve("vs_missing")

    assert exc.value.status_code == 404
    assert exc.value.provider_code == "not_found"


def test_local_compat_search_respects_max_results(tmp_path) -> None:
    client = OAuthCodexClient(
        token_store=InMemoryTokenStore(_tokens()),
        compat_storage_dir=str(tmp_path),
    )
    file_one = client.files.create(file=io.BytesIO(b"alpha data one"), purpose="assistants")
    file_two = client.files.create(file=io.BytesIO(b"alpha data two"), purpose="assistants")
    vector = client.vector_stores.create(file_ids=[file_one["id"], file_two["id"]])

    out = client.vector_stores.search(vector["id"], query="alpha", max_num_results=1)

    assert len(out["data"]) == 1
    assert out["has_more"] is True


def test_local_compat_storage_dir_can_be_set_by_env(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_dir = tmp_path / "compat-env"
    monkeypatch.setenv("CODEX_COMPAT_STORAGE_DIR", str(env_dir))
    client = OAuthCodexClient(token_store=InMemoryTokenStore(_tokens()))

    client.files.create(file=io.BytesIO(b"env data"), purpose="assistants")

    assert Path(env_dir / "files" / "index.json").exists()


def test_local_compat_storage_dir_constructor_overrides_env(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_dir = tmp_path / "compat-env"
    arg_dir = tmp_path / "compat-arg"
    monkeypatch.setenv("CODEX_COMPAT_STORAGE_DIR", str(env_dir))
    client = OAuthCodexClient(
        token_store=InMemoryTokenStore(_tokens()),
        compat_storage_dir=str(arg_dir),
    )

    client.files.create(file=io.BytesIO(b"arg data"), purpose="assistants")

    assert Path(arg_dir / "files" / "index.json").exists()
    assert not Path(env_dir / "files" / "index.json").exists()


@pytest.mark.asyncio
async def test_local_compat_sync_async_shape_parity(tmp_path) -> None:
    sync_client = OAuthCodexClient(
        token_store=InMemoryTokenStore(_tokens()),
        compat_storage_dir=str(tmp_path),
    )
    async_client = AsyncOAuthCodexClient(
        token_store=InMemoryTokenStore(_tokens()),
        compat_storage_dir=str(tmp_path),
    )

    file_out = sync_client.files.create(file=io.BytesIO(b"alpha parity"), purpose="assistants")
    vector_out = sync_client.vector_stores.create(name="docs", file_ids=[file_out["id"]])
    sync_result = sync_client.vector_stores.search(vector_out["id"], query="alpha", max_num_results=1)
    async_result = await async_client.vector_stores.search(
        vector_out["id"],
        query="alpha",
        max_num_results=1,
    )

    assert sync_result["object"] == async_result["object"] == "list"
    assert set(sync_result.keys()) == set(async_result.keys())
    assert sync_result["data"]
    assert async_result["data"]
    assert set(sync_result["data"][0].keys()) == set(async_result["data"][0].keys())
    assert async_result["data"][0]["file_id"] == file_out["id"]


def test_local_compat_response_continuity_persists_between_clients(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    first = OAuthCodexClient(
        token_store=InMemoryTokenStore(_tokens()),
        compat_storage_dir=str(tmp_path),
    )

    def first_sse(**kwargs):
        _ = kwargs
        yield StreamEvent(type="response_started", response_id="resp_1")
        yield StreamEvent(type="text_delta", delta="first", response_id="resp_1")
        yield StreamEvent(
            type="response_completed",
            response_id="resp_1",
            raw={
                "id": "resp_1",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "first"}],
                    }
                ],
            },
        )
        yield StreamEvent(type="done", response_id="resp_1")

    monkeypatch.setattr(first._engine, "_stream_sse_sync", first_sse)

    first_resp = first.responses.create(model="gpt-5.3-codex", input="seed")
    assert first_resp.id == "resp_1"

    second = OAuthCodexClient(
        token_store=InMemoryTokenStore(_tokens()),
        compat_storage_dir=str(tmp_path),
    )
    captured: dict[str, object] = {}

    def second_sse(**kwargs):
        payload = kwargs["payload"]
        assert isinstance(payload, dict)
        captured["payload"] = {
            **payload,
            "input": [dict(item) for item in payload.get("input", []) if isinstance(item, dict)],
        }
        yield StreamEvent(type="response_started", response_id="resp_2")
        yield StreamEvent(type="text_delta", delta="second", response_id="resp_2")
        yield StreamEvent(type="response_completed", response_id="resp_2")
        yield StreamEvent(type="done", response_id="resp_2")

    monkeypatch.setattr(second._engine, "_stream_sse_sync", second_sse)

    second.responses.create(
        model="gpt-5.3-codex",
        input="next",
        previous_response_id=first_resp.id,
    )

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert "previous_response_id" not in payload
    merged_input = payload["input"]
    assert isinstance(merged_input, list)
    assert merged_input[0]["content"] == "seed"
    assert merged_input[1]["type"] == "message"
    assert merged_input[2]["content"] == "next"
