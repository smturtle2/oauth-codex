[English](vector_stores.md) | [한국어](../../ko/methods/vector_stores.md)

# Vector Stores Methods

This page documents `vector_stores` runtime methods in `oauth-codex`.

## Method Summary

### Root resource

| Method | Support | Notes |
|---|---|---|
| `vector_stores.create(...)` | Supported | Create vector store |
| `vector_stores.retrieve(...)` | Supported | Retrieve vector store |
| `vector_stores.update(...)` | Supported | Update vector store |
| `vector_stores.list(...)` | Supported | List vector stores |
| `vector_stores.delete(...)` | Supported | Delete vector store |
| `vector_stores.search(...)` | Supported | Search by query |

### Subresource: `vector_stores.files`

| Method | Support | Notes |
|---|---|---|
| `create` | Supported | Attach existing file id |
| `create_and_poll` | Supported | Alias to `create` |
| `retrieve` | Supported | Retrieve file attachment state |
| `list` | Supported | List files in vector store |
| `delete` | Supported | Remove file attachment |
| `content` | Supported | Delegates to top-level `files.content` |
| `poll` | Supported | Alias to `retrieve` |
| `upload` | Supported | Upload file then attach |
| `upload_and_poll` | Supported | Alias of `upload` |
| `update` | Unsupported | Raises `NotSupportedError(code="not_supported")` |

### Subresource: `vector_stores.file_batches`

| Method | Support | Notes |
|---|---|---|
| `create` | Supported | Create local batch record and attach files |
| `create_and_poll` | Supported | Alias to `create` |
| `retrieve` | Supported | Retrieve local batch state |
| `list_files` | Supported | Lists files via `vector_stores.files.list` |
| `cancel` | Supported | Marks local batch state as cancelled |
| `poll` | Supported | Alias to `retrieve` |
| `upload_and_poll` | Supported | Upload files then batch-attach |

## Root Methods (`vector_stores.*`)

### Signatures (sync / async / module-level)

```python
# sync
client.vector_stores.create(
    *,
    name: str | None = None,
    file_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    expires_after: dict[str, Any] | None = None,
    **payload,
) -> VectorStore
client.vector_stores.retrieve(vector_store_id: str) -> VectorStore
client.vector_stores.update(
    vector_store_id: str,
    *,
    name: str | None = None,
    file_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    expires_after: dict[str, Any] | None = None,
    **payload,
) -> VectorStore
client.vector_stores.list(
    *,
    after: str | None = None,
    before: str | None = None,
    limit: int | None = None,
    order: str | None = None,
    **params,
) -> dict
client.vector_stores.delete(vector_store_id: str) -> VectorStoreDeleted
client.vector_stores.search(
    vector_store_id: str,
    *,
    query: str,
    max_num_results: int | None = None,
    filters: dict[str, Any] | None = None,
    ranking_options: dict[str, Any] | None = None,
    rewrite_query: bool | None = None,
    **payload,
) -> dict

# async
await client.vector_stores.create(...) -> VectorStore
await client.vector_stores.retrieve(vector_store_id: str) -> VectorStore
await client.vector_stores.update(...) -> VectorStore
await client.vector_stores.list(...) -> dict
await client.vector_stores.delete(vector_store_id: str) -> VectorStoreDeleted
await client.vector_stores.search(...) -> dict

# module-level
oauth_codex.vector_stores.create(...)
oauth_codex.vector_stores.retrieve(...)
oauth_codex.vector_stores.update(...)
oauth_codex.vector_stores.list(...)
oauth_codex.vector_stores.delete(...)
oauth_codex.vector_stores.search(...)
```

### Parameters (root methods)

| Method | Parameter | Type | Required | Default | Behavior |
|---|---|---|---|---|---|
| `create` | `name` | `str | None` | No | `None` | Vector store display name |
| `create` | `file_ids` | `list[str] | None` | No | `None` | Initial file memberships |
| `create` | `metadata` | `dict[str, Any] | None` | No | `None` | Metadata fields |
| `create` | `expires_after` | `dict[str, Any] | None` | No | `None` | Expiration policy payload |
| `create` | `**payload` | `dict` | No | - | Additional compatibility fields are forwarded |
| `retrieve` | `vector_store_id` | `str` | Yes | - | Target vector store id |
| `update` | `vector_store_id` | `str` | Yes | - | Target vector store id |
| `update` | `name` | `str | None` | No | `None` | Update display name |
| `update` | `file_ids` | `list[str] | None` | No | `None` | Replace memberships |
| `update` | `metadata` | `dict[str, Any] | None` | No | `None` | Replace metadata |
| `update` | `expires_after` | `dict[str, Any] | None` | No | `None` | Replace expiration policy |
| `update` | `**payload` | `dict` | No | - | Additional compatibility fields are forwarded |
| `list` | `after` | `str | None` | No | `None` | Cursor-like query input |
| `list` | `before` | `str | None` | No | `None` | Cursor-like query input |
| `list` | `limit` | `int | None` | No | `None` | Maximum items |
| `list` | `order` | `str | None` | No | `None` | Ordering hint (`asc`/`desc`) |
| `list` | `**params` | `dict` | No | - | Additional query-like compatibility fields |
| `delete` | `vector_store_id` | `str` | Yes | - | Target vector store id |
| `search` | `vector_store_id` | `str` | Yes | - | Target vector store id |
| `search` | `query` | `str` | Yes | - | Search text |
| `search` | `max_num_results` | `int | None` | No | `None` | Result count hint |
| `search` | `filters` | `dict[str, Any] | None` | No | `None` | Provider filter payload |
| `search` | `ranking_options` | `dict[str, Any] | None` | No | `None` | Provider ranking payload |
| `search` | `rewrite_query` | `bool | None` | No | `None` | Provider query rewrite hint |
| `search` | `**payload` | `dict` | No | - | Additional compatibility fields are forwarded |

- Compatibility rule: explicit named parameters and extra `**payload/**params` are merged and sent together.

### Return Shapes

- `VectorStore` fields: `id`, `object`, `created_at`, `name`, `metadata`, `file_ids`, `status`, `usage_bytes`, `file_counts`, `expires_after`.
- `VectorStoreDeleted` fields: `id`, `object`, `deleted`.
- `list/search` return dict payloads (`object`, `data`, and backend/local fields).

### Error Cases

| Exception | Trigger |
|---|---|
| `SDKRequestError` | Provider/local compatibility storage failure |
| `NotSupportedError(code="not_supported_on_codex_oauth")` | Disallowed Codex-profile path/method combinations |
| `ParameterValidationError` | Invalid local-compat arguments |

### Behavior Notes

- Codex profile uses local emulation for vector stores.
- Non-Codex profile uses network requests to vector store endpoints.
- In Codex profile, unsupported path patterns in vector store emulation raise `not_supported_on_codex_oauth`.

### Runnable Usage Snippets

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()
vs = client.vector_stores.create(name="docs", file_ids=[])
print(vs.id)

found = client.vector_stores.search(vs.id, query="oauth")
print(found.get("object"))
```

### Pitfalls / Troubleshooting

- In local mode, list/search semantics are compatibility approximations, not full backend parity.

## `vector_stores.files.*`

### Signatures (sync / async / module-level)

```python
# sync
client.vector_stores.files.create(vector_store_id: str, *, file_id: str) -> VectorStoreFile
client.vector_stores.files.create_and_poll(vector_store_id: str, *, file_id: str) -> VectorStoreFile
client.vector_stores.files.retrieve(vector_store_id: str, file_id: str) -> VectorStoreFile
client.vector_stores.files.list(vector_store_id: str) -> dict
client.vector_stores.files.delete(vector_store_id: str, file_id: str) -> dict
client.vector_stores.files.content(vector_store_id: str, file_id: str) -> bytes
client.vector_stores.files.poll(vector_store_id: str, file_id: str) -> VectorStoreFile
client.vector_stores.files.upload(vector_store_id: str, *, file: Any, purpose: str = "assistants") -> VectorStoreFile
client.vector_stores.files.upload_and_poll(vector_store_id: str, *, file: Any, purpose: str = "assistants") -> VectorStoreFile
client.vector_stores.files.update(...)  # unsupported

# async
await client.vector_stores.files.create(...)
await client.vector_stores.files.create_and_poll(...)
await client.vector_stores.files.retrieve(...)
await client.vector_stores.files.list(...)
await client.vector_stores.files.delete(...)
await client.vector_stores.files.content(...)
await client.vector_stores.files.poll(...)
await client.vector_stores.files.upload(...)
await client.vector_stores.files.upload_and_poll(...)
await client.vector_stores.files.update(...)  # unsupported

# module-level
oauth_codex.vector_stores.files.<method>(...)
```

### Parameters

| Method | Parameters |
|---|---|
| `create` / `create_and_poll` | `vector_store_id`, required `file_id` |
| `retrieve` / `poll` | `vector_store_id`, `file_id` |
| `list` | `vector_store_id` |
| `delete` | `vector_store_id`, `file_id` |
| `content` | `vector_store_id`, `file_id` (delegates to top-level files content) |
| `upload` / `upload_and_poll` | `vector_store_id`, required `file`, optional `purpose="assistants"` |
| `update` | Unsupported |

### Return Shapes

- `VectorStoreFile`: `id`, `object`, `vector_store_id`, `status`, `created_at`.
- `list`: dict payload with `data` entries of `VectorStoreFile` dicts.
- `delete`: dict with `id`, `object`, `deleted`.
- `content`: raw `bytes`.

### Error Cases

| Exception | Trigger |
|---|---|
| `SDKRequestError` | Provider/local compatibility error |
| `KeyError` (wrapped on some paths) | Missing file in local vector store membership |
| `NotSupportedError(code="not_supported")` | Calling `vector_stores.files.update` |

### Behavior Notes

- In local mode, file membership is maintained by `file_ids` in vector store records.
- `create_and_poll` and `poll` are shortcut aliases; no additional remote polling workflow is added.
- `content` ignores `vector_store_id` and delegates to `client.files.content(file_id)`.

### Runnable Usage Snippets

```python
import io

uploaded = client.files.create(file=io.BytesIO(b"alpha gamma"), purpose="assistants")
vs = client.vector_stores.create(name="docs", file_ids=[])

attached = client.vector_stores.files.create(vs.id, file_id=uploaded.id)
print(attached.id, attached.vector_store_id)
```

### Pitfalls / Troubleshooting

- `vector_store_id` is not used for byte download in `content`; only `file_id` matters there.

## `vector_stores.file_batches.*`

### Signatures (sync / async / module-level)

```python
# sync
client.vector_stores.file_batches.create(vector_store_id: str, *, file_ids: list[str]) -> VectorStoreFileBatch
client.vector_stores.file_batches.create_and_poll(vector_store_id: str, *, file_ids: list[str]) -> VectorStoreFileBatch
client.vector_stores.file_batches.retrieve(vector_store_id: str, batch_id: str) -> VectorStoreFileBatch
client.vector_stores.file_batches.list_files(vector_store_id: str, batch_id: str) -> dict
client.vector_stores.file_batches.cancel(vector_store_id: str, batch_id: str) -> VectorStoreFileBatch
client.vector_stores.file_batches.poll(vector_store_id: str, batch_id: str) -> VectorStoreFileBatch
client.vector_stores.file_batches.upload_and_poll(vector_store_id: str, *, files: list[Any], purpose: str = "assistants") -> VectorStoreFileBatch

# async
await client.vector_stores.file_batches.create(...)
await client.vector_stores.file_batches.create_and_poll(...)
await client.vector_stores.file_batches.retrieve(...)
await client.vector_stores.file_batches.list_files(...)
await client.vector_stores.file_batches.cancel(...)
await client.vector_stores.file_batches.poll(...)
await client.vector_stores.file_batches.upload_and_poll(...)

# module-level
oauth_codex.vector_stores.file_batches.<method>(...)
```

### Parameters

| Method | Parameters |
|---|---|
| `create` / `create_and_poll` | `vector_store_id`, required `file_ids: list[str]` |
| `retrieve` / `poll` | `vector_store_id`, `batch_id` |
| `list_files` | `vector_store_id`, `batch_id` |
| `cancel` | `vector_store_id`, `batch_id` |
| `upload_and_poll` | `vector_store_id`, required `files: list[Any]`, optional `purpose` |

### Return Shapes

- `VectorStoreFileBatch`: `id`, `object`, `vector_store_id`, `status`, `created_at`, `file_counts`.
- `list_files`: dict payload from `vector_stores.files.list(...)`.

### Error Cases

| Exception | Trigger |
|---|---|
| `SDKRequestError` | Underlying file/vector-store operations fail |

### Behavior Notes

- Batch records are local in-memory compatibility objects in current implementation.
- `cancel` updates local batch status to `cancelled`.

### Runnable Usage Snippets

```python
batch = client.vector_stores.file_batches.create(vs.id, file_ids=[uploaded.id])
print(batch.id, batch.status)

listed = client.vector_stores.file_batches.list_files(vs.id, batch.id)
print(listed.get("object"))
```

### Pitfalls / Troubleshooting

- Batch status is compatibility-oriented and should not be treated as authoritative backend workflow state.
