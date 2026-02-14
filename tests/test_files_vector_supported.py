from __future__ import annotations

import io

from conftest import InMemoryTokenStore
from oauth_codex import OAuthCodexClient
from oauth_codex.legacy_types import OAuthTokens


def _client(tmp_path) -> OAuthCodexClient:
    return OAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        ),
        compat_storage_dir=str(tmp_path),
    )


def test_files_crud_and_content_local_compat(tmp_path) -> None:
    client = _client(tmp_path)

    created = client.files.create(file=io.BytesIO(b"alpha beta"), purpose="assistants")
    retrieved = client.files.retrieve(created.id)
    listed = client.files.list()
    content = client.files.content(created.id)
    deleted = client.files.delete(created.id)

    assert retrieved.id == created.id
    assert any(item["id"] == created.id for item in listed["data"])
    assert content == b"alpha beta"
    assert deleted.deleted is True


def test_vector_store_and_subresources_local_compat(tmp_path) -> None:
    client = _client(tmp_path)

    file_out = client.files.create(file=io.BytesIO(b"alpha gamma"), purpose="assistants")
    vs = client.vector_stores.create(name="docs", file_ids=[file_out.id])
    assert vs.id.startswith("vs_")

    search = client.vector_stores.search(vs.id, query="alpha")
    assert search["object"] == "list"

    files_list = client.vector_stores.files.list(vs.id)
    assert files_list["data"][0]["id"] == file_out.id

    batch = client.vector_stores.file_batches.create(vs.id, file_ids=[file_out.id])
    listed_batch_files = client.vector_stores.file_batches.list_files(vs.id, batch.id)
    assert listed_batch_files["object"] == "list"

    deleted = client.vector_stores.delete(vs.id)
    assert deleted.deleted is True
