[English](files.md) | [한국어](../../ko/methods/files.md)

# Files Methods

This page documents `files` runtime methods in `oauth-codex`.

## Method Summary

| Method | Support | Notes |
|---|---|---|
| `files.create(...)` | Supported | Upload/create file metadata |
| `files.retrieve(...)` | Supported | Get one file |
| `files.list(...)` | Supported | List files |
| `files.delete(...)` | Supported | Delete a file |
| `files.content(...)` | Supported | Download raw bytes |
| `files.retrieve_content(...)` | Supported | Alias to `content(...)` |
| `files.wait_for_processing(...)` | Supported | Poll file status until processed/completed/timeout |

## `files.create`

### Sync / Async / Module-level Signatures

```python
# sync
client.files.create(*, file: Any, purpose: str, **metadata) -> FileObject

# async
await client.files.create(*, file: Any, purpose: str, **metadata) -> FileObject

# module-level
oauth_codex.files.create(...)
```

### Parameters

| Parameter | Type | Required | Default | Validation / Behavior |
|---|---|---|---|---|
| `file` | `Any` | Yes | - | File-like object or upload input accepted by HTTP multipart/local compat layer |
| `purpose` | `str` | Yes | - | File purpose string (commonly `"assistants"`) |
| `**metadata` | `dict` | No | `{}` | Extra metadata is forwarded |

### Return Shape

Returns `FileObject`:

- `id: str`
- `object: str` (`"file"`)
- `bytes: int | None`
- `created_at: int | None`
- `filename: str | None`
- `purpose: str | None`
- `metadata: dict | None`

### Error Cases

| Exception | Trigger |
|---|---|
| `AuthRequiredError` | Missing/invalid auth where network call is needed |
| `SDKRequestError` | Provider failure, local compatibility storage error |
| `ParameterValidationError` | Invalid local compatibility input |

### Behavior Notes

- Codex profile: file operations use local compatibility storage.
- Non-Codex profile: uploads via multipart `/files` endpoint.

### Runnable Usage Snippets

```python
import io
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()
out = client.files.create(file=io.BytesIO(b"alpha beta"), purpose="assistants")
print(out.id)
```

### Pitfalls / Troubleshooting

- If the backend is Codex profile, file records are persisted locally, not remotely.

## `files.retrieve`

### Sync / Async / Module-level Signatures

```python
client.files.retrieve(file_id: str) -> FileObject
await client.files.retrieve(file_id: str) -> FileObject
oauth_codex.files.retrieve(file_id)
```

### Parameters

| Parameter | Type | Required | Default | Validation / Behavior |
|---|---|---|---|---|
| `file_id` | `str` | Yes | - | Target file identifier |

### Return Shape

- `FileObject` (same shape as `files.create`).

### Error Cases

| Exception | Trigger |
|---|---|
| `SDKRequestError` | Not found, provider error, local storage read error |

### Behavior Notes

- Codex profile retrieval reads local compatibility index.

### Runnable Usage Snippets

```python
file_obj = client.files.retrieve("file_123")
print(file_obj.filename, file_obj.purpose)
```

### Pitfalls / Troubleshooting

- A deleted/nonexistent file in local compat path maps to SDK request error semantics.

## `files.list`

### Sync / Async / Module-level Signatures

```python
client.files.list(*, after=None, limit=None, order=None, purpose=None) -> dict
await client.files.list(*, after=None, limit=None, order=None, purpose=None) -> dict
oauth_codex.files.list(...)
```

### Parameters

| Parameter | Type | Required | Default | Validation / Behavior |
|---|---|---|---|---|
| `after` | `str | None` | No | `None` | Cursor hint |
| `limit` | `int | None` | No | `None` | Positive item cap recommended |
| `order` | `str | None` | No | `None` | `"desc"` supported for local list reversal |
| `purpose` | `str | None` | No | `None` | Filters by purpose |

### Return Shape

- Dict list payload with `object`, `data`, and paging-like fields.
- `data` items are normalized `FileObject` dictionaries.

### Error Cases

| Exception | Trigger |
|---|---|
| `SDKRequestError` | Provider/local storage failure |

### Behavior Notes

- Codex profile list currently returns `has_more=False` from local compatibility storage.

### Runnable Usage Snippets

```python
files_out = client.files.list(limit=20, order="desc")
print(files_out["object"], len(files_out.get("data", [])))
```

### Pitfalls / Troubleshooting

- Do not assume backend-style pagination fields are fully equivalent in local compat mode.

## `files.delete`

### Sync / Async / Module-level Signatures

```python
client.files.delete(file_id: str) -> FileDeleted
await client.files.delete(file_id: str) -> FileDeleted
oauth_codex.files.delete(file_id)
```

### Parameters

| Parameter | Type | Required | Default | Validation / Behavior |
|---|---|---|---|---|
| `file_id` | `str` | Yes | - | Target file identifier |

### Return Shape

Returns `FileDeleted`:

- `id: str`
- `object: str` (`"file.deleted"`)
- `deleted: bool`

### Error Cases

| Exception | Trigger |
|---|---|
| `SDKRequestError` | Provider/local storage failure |

### Behavior Notes

- Codex profile removes file entry and local blob (`<file_id>.bin`) if present.

### Runnable Usage Snippets

```python
deleted = client.files.delete("file_123")
print(deleted.deleted)
```

### Pitfalls / Troubleshooting

- In local mode, deleting a missing file can still return a structured deletion payload.

## `files.content`

### Sync / Async / Module-level Signatures

```python
client.files.content(file_id: str) -> bytes
await client.files.content(file_id: str) -> bytes
oauth_codex.files.content(file_id)
```

### Parameters

| Parameter | Type | Required | Default | Validation / Behavior |
|---|---|---|---|---|
| `file_id` | `str` | Yes | - | Target file identifier |

### Return Shape

- Raw `bytes` for the file content.

### Error Cases

| Exception | Trigger |
|---|---|
| `SDKRequestError` | HTTP/content endpoint error |
| `KeyError` (wrapped on some paths) | Missing local file blob |

### Behavior Notes

- Codex profile reads local blob bytes.
- Non-Codex profile performs GET on `/files/{file_id}/content`.

### Runnable Usage Snippets

```python
data = client.files.content("file_123")
print(len(data))
```

### Pitfalls / Troubleshooting

- Treat content as binary; decode only if you know text encoding.

## `files.retrieve_content`

### Sync / Async / Module-level Signatures

```python
client.files.retrieve_content(file_id: str) -> bytes
await client.files.retrieve_content(file_id: str) -> bytes
oauth_codex.files.retrieve_content(file_id)
```

### Parameters

- Same as `files.content(...)`.

### Return Shape

- Alias of `files.content(...)`; returns `bytes`.

### Error Cases

- Same as `files.content(...)`.

### Behavior Notes

- This is an alias convenience method.

### Runnable Usage Snippets

```python
blob = client.files.retrieve_content("file_123")
```

### Pitfalls / Troubleshooting

- Prefer one method consistently in your codebase to avoid confusion.

## `files.wait_for_processing`

### Sync / Async / Module-level Signatures

```python
client.files.wait_for_processing(file_id: str, *, timeout: float = 60.0, poll_interval: float = 0.5) -> FileObject
await client.files.wait_for_processing(file_id: str, *, timeout: float = 60.0, poll_interval: float = 0.5) -> FileObject
oauth_codex.files.wait_for_processing(...)
```

### Parameters

| Parameter | Type | Required | Default | Validation / Behavior |
|---|---|---|---|---|
| `file_id` | `str` | Yes | - | Target file identifier |
| `timeout` | `float` | No | `60.0` | Polling timeout seconds |
| `poll_interval` | `float` | No | `0.5` | Sleep interval between retrieval attempts |

### Return Shape

- Returns final `FileObject` seen before completion criteria or timeout.

### Error Cases

| Exception | Trigger |
|---|---|
| `SDKRequestError` | Retrieval failure during polling |

### Behavior Notes

- Completes when status in metadata is `None`, `processed`, or `completed`.
- If timeout is exceeded, returns the latest seen file object.

### Runnable Usage Snippets

```python
final_file = client.files.wait_for_processing("file_123", timeout=30.0)
print(final_file.metadata)
```

### Pitfalls / Troubleshooting

- In local compat mode, status may be absent (`None`), which ends polling immediately.
