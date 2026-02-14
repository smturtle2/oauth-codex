from __future__ import annotations

import io

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import OAuthCodexClient, SDKRequestError
from oauth_codex.types import OAuthTokens


def _client(
    *,
    base_url: str = "https://chatgpt.com/backend-api/codex",
    compat_storage_dir: str | None = None,
) -> OAuthCodexClient:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    return OAuthCodexClient(
        token_store=store,
        chatgpt_base_url=base_url,
        compat_storage_dir=compat_storage_dir,
    )


def test_files_create_uses_local_compat_on_codex_profile(tmp_path) -> None:
    client = _client(compat_storage_dir=str(tmp_path))

    out = client.files.create(file=io.BytesIO(b"x"), purpose="assistants")

    assert out["id"].startswith("file_")
    assert out["object"] == "file"
    assert out["bytes"] == 1


def test_vector_stores_use_local_compat_on_codex_profile(tmp_path) -> None:
    client = _client(compat_storage_dir=str(tmp_path))
    file_out = client.files.create(file=io.BytesIO(b"alpha beta"), purpose="assistants")

    created = client.vector_stores.create(name="docs", file_ids=[file_out["id"]])
    retrieved = client.vector_stores.retrieve(created["id"])
    listed = client.vector_stores.list()
    searched = client.vector_stores.search(created["id"], query="alpha")
    updated = client.vector_stores.update(created["id"], name="docs-v2")
    deleted = client.vector_stores.delete(created["id"])

    assert retrieved["id"] == created["id"]
    assert any(item["id"] == created["id"] for item in listed["data"])
    assert searched["object"] == "list"
    assert searched["data"][0]["file_id"] == file_out["id"]
    assert updated["name"] == "docs-v2"
    assert deleted == {"id": created["id"], "object": "vector_store.deleted", "deleted": True}

    with pytest.raises(SDKRequestError) as exc:
        client.vector_stores.retrieve(created["id"])
    assert exc.value.status_code == 404
    assert exc.value.provider_code == "not_found"


def test_vector_stores_calls_remote_when_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(base_url="https://api.openai.com/v1")

    def fake_request(**kwargs):
        assert kwargs["path"] == "/vector_stores"
        assert kwargs["method"] == "POST"
        return {"id": "vs_1"}

    monkeypatch.setattr(client._engine, "_request_json_sync", fake_request)

    out = client.vector_stores.create(name="docs")

    assert out["id"] == "vs_1"


def test_files_create_calls_remote_when_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(base_url="https://api.openai.com/v1")

    def fake_request(**kwargs):
        assert kwargs["path"] == "/files"
        assert kwargs["data"]["purpose"] == "assistants"
        assert "file" in kwargs["files"]
        return {"id": "file_1", "object": "file"}

    monkeypatch.setattr(client._engine, "_request_multipart_sync", fake_request)

    out = client.files.create(file=io.BytesIO(b"remote"), purpose="assistants")

    assert out["id"] == "file_1"
