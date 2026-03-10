from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

from conftest import InMemoryTokenStore
from oauth_codex import Client
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


def test_client_exposes_resource_namespaces() -> None:
    client = _client()

    assert client.responses is client.responses
    assert client.files is client.files
    assert client.vector_stores is client.vector_stores
    assert client.vector_stores.files is client.vector_stores.files
    assert client.vector_stores.file_batches is client.vector_stores.file_batches
    assert client.models is client.models
    assert client.chat is client.chat


def test_client_responses_resource_uses_engine_create(monkeypatch) -> None:
    client = _client()
    captured: dict[str, object] = {}

    def fake_responses_create(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return SimpleNamespace(
            id="resp_1",
            output=[],
            output_text="",
            usage=None,
            error=None,
            reasoning_summary=None,
            reasoning_items=[],
            encrypted_reasoning_content=None,
            finish_reason="stop",
            previous_response_id=None,
            raw_response=None,
        )

    def fake_responses_input_tokens_count(**_kwargs: Any) -> Any:
        return {"input_tokens": 42, "cached_tokens": 0, "total_tokens": 42}

    monkeypatch.setattr(client._engine, "responses_create", fake_responses_create)
    monkeypatch.setattr(
        client._engine,
        "responses_input_tokens_count",
        fake_responses_input_tokens_count,
    )

    out = client.responses.create(
        model="gpt-5.3-codex", messages=[{"role": "user", "content": "hi"}]
    )
    assert out.id == "resp_1"
    assert captured["model"] == "gpt-5.3-codex"

    tokens = client.responses.input_tokens.count(model="gpt-5.3-codex", input="hello")
    assert tokens.input_tokens == 42
    assert tokens.total_tokens == 42


def test_client_other_resources_delegate_to_engine(monkeypatch) -> None:
    client = _client()

    class _Resp:
        def __init__(self, payload: dict[str, Any]) -> None:
            self._payload = payload

        def json(self) -> dict[str, Any]:
            return self._payload

    def fake_request(
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json_data: Any = None,
        data: Any = None,
        files: Any = None,
        timeout: float | None = None,
    ) -> _Resp:
        _ = (params, headers, json_data, data, files, timeout)
        if method == "POST" and path == "/files":
            return _Resp({"id": "file_1", "object": "file"})
        if method == "POST" and path == "/vector_stores":
            return _Resp({"id": "vs_1", "object": "vector_store"})
        if method == "GET" and path == "/models":
            return _Resp({"object": "list", "data": []})
        raise AssertionError(f"unexpected request: {method} {path}")

    monkeypatch.setattr(client, "request", fake_request)

    out_file = client.files.create(file=b"abc", purpose="assistants")
    assert out_file.id == "file_1"

    out_vs = client.vector_stores.create(name="x")
    assert out_vs.id == "vs_1"

    out_model = client.models.list()
    assert out_model.object == "list"


def test_vector_store_file_batches_use_client_state(
    monkeypatch: Any,
) -> None:
    client = _client()
    uploaded_files: list[tuple[str, str]] = []
    file_ids = {"next": 0}

    def fake_file_create(*, file: Any, purpose: str, **metadata: Any) -> Any:
        _ = (file, purpose, metadata)
        file_ids["next"] += 1
        return SimpleNamespace(id=f"file_{file_ids['next']}", object="file")

    def fake_vs_file_create(vector_store_id: str, *, file_id: str) -> Any:
        uploaded_files.append((vector_store_id, file_id))
        return SimpleNamespace(
            id=file_id,
            object="vector_store.file",
            vector_store_id=vector_store_id,
        )

    monkeypatch.setattr(client.files, "create", fake_file_create)
    monkeypatch.setattr(client.vector_stores.files, "create", fake_vs_file_create)

    batch = client.vector_stores.file_batches.upload_and_poll(
        "vs_123",
        files=[b"one", b"two"],
    )

    assert batch.vector_store_id == "vs_123"
    assert batch.status == "completed"
    assert uploaded_files == [("vs_123", "file_1"), ("vs_123", "file_2")]
