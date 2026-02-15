[English](../../en/methods/vector_stores.md) | [한국어](vector_stores.md)

# Vector Stores 메서드

이 문서는 `oauth-codex`의 `vector_stores` 런타임 메서드를 설명합니다.

## Method Summary

### 루트 리소스

| 메서드 | 지원 여부 | 비고 |
|---|---|---|
| `vector_stores.create(...)` | 지원 | 벡터 스토어 생성 |
| `vector_stores.retrieve(...)` | 지원 | 벡터 스토어 조회 |
| `vector_stores.update(...)` | 지원 | 벡터 스토어 수정 |
| `vector_stores.list(...)` | 지원 | 벡터 스토어 목록 |
| `vector_stores.delete(...)` | 지원 | 벡터 스토어 삭제 |
| `vector_stores.search(...)` | 지원 | 쿼리 검색 |

### 하위 리소스: `vector_stores.files`

| 메서드 | 지원 여부 | 비고 |
|---|---|---|
| `create` | 지원 | 기존 file id attach |
| `create_and_poll` | 지원 | `create` alias |
| `retrieve` | 지원 | attach 상태 조회 |
| `list` | 지원 | vector store 내 파일 목록 |
| `delete` | 지원 | attach 해제 |
| `content` | 지원 | top-level `files.content` 위임 |
| `poll` | 지원 | `retrieve` alias |
| `upload` | 지원 | 파일 업로드 후 attach |
| `upload_and_poll` | 지원 | `upload` alias |
| `update` | 미지원 | `NotSupportedError(code="not_supported")` |

### 하위 리소스: `vector_stores.file_batches`

| 메서드 | 지원 여부 | 비고 |
|---|---|---|
| `create` | 지원 | 로컬 batch 기록 생성 + file attach |
| `create_and_poll` | 지원 | `create` alias |
| `retrieve` | 지원 | 로컬 batch 상태 조회 |
| `list_files` | 지원 | `vector_stores.files.list` 위임 |
| `cancel` | 지원 | 로컬 batch 상태를 cancelled로 표시 |
| `poll` | 지원 | `retrieve` alias |
| `upload_and_poll` | 지원 | 파일 업로드 후 batch attach |

## 루트 메서드 (`vector_stores.*`)

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

### Parameters (루트 메서드)

| 메서드 | 파라미터 | 타입 | 필수 | 기본값 | 동작 |
|---|---|---|---|---|---|
| `create` | `name` | `str | None` | 아니오 | `None` | 벡터 스토어 표시 이름 |
| `create` | `file_ids` | `list[str] | None` | 아니오 | `None` | 초기 파일 멤버십 |
| `create` | `metadata` | `dict[str, Any] | None` | 아니오 | `None` | 메타데이터 필드 |
| `create` | `expires_after` | `dict[str, Any] | None` | 아니오 | `None` | 만료 정책 payload |
| `create` | `**payload` | `dict` | 아니오 | - | 추가 호환성 필드는 그대로 전달 |
| `retrieve` | `vector_store_id` | `str` | 예 | - | 대상 벡터 스토어 ID |
| `update` | `vector_store_id` | `str` | 예 | - | 대상 벡터 스토어 ID |
| `update` | `name` | `str | None` | 아니오 | `None` | 표시 이름 변경 |
| `update` | `file_ids` | `list[str] | None` | 아니오 | `None` | 멤버십 교체 |
| `update` | `metadata` | `dict[str, Any] | None` | 아니오 | `None` | 메타데이터 교체 |
| `update` | `expires_after` | `dict[str, Any] | None` | 아니오 | `None` | 만료 정책 교체 |
| `update` | `**payload` | `dict` | 아니오 | - | 추가 호환성 필드는 그대로 전달 |
| `list` | `after` | `str | None` | 아니오 | `None` | cursor 유사 query 입력 |
| `list` | `before` | `str | None` | 아니오 | `None` | cursor 유사 query 입력 |
| `list` | `limit` | `int | None` | 아니오 | `None` | 최대 항목 수 |
| `list` | `order` | `str | None` | 아니오 | `None` | 정렬 힌트 (`asc`/`desc`) |
| `list` | `**params` | `dict` | 아니오 | - | 추가 query-like 호환성 필드 |
| `delete` | `vector_store_id` | `str` | 예 | - | 대상 벡터 스토어 ID |
| `search` | `vector_store_id` | `str` | 예 | - | 대상 벡터 스토어 ID |
| `search` | `query` | `str` | 예 | - | 검색 텍스트 |
| `search` | `max_num_results` | `int | None` | 아니오 | `None` | 결과 개수 힌트 |
| `search` | `filters` | `dict[str, Any] | None` | 아니오 | `None` | provider filter payload |
| `search` | `ranking_options` | `dict[str, Any] | None` | 아니오 | `None` | provider ranking payload |
| `search` | `rewrite_query` | `bool | None` | 아니오 | `None` | provider query rewrite 힌트 |
| `search` | `**payload` | `dict` | 아니오 | - | 추가 호환성 필드는 그대로 전달 |

- 호환 규칙: 명시 파라미터와 추가 `**payload/**params`는 함께 merge되어 전송됩니다.

### Return Shapes

- `VectorStore`: `id`, `object`, `created_at`, `name`, `metadata`, `file_ids`, `status`, `usage_bytes`, `file_counts`, `expires_after`.
- `VectorStoreDeleted`: `id`, `object`, `deleted`.
- `list/search`: `object`, `data` 등을 포함한 dict payload.

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `SDKRequestError` | provider/local compatibility 저장소 실패 |
| `NotSupportedError(code="not_supported_on_codex_oauth")` | Codex profile에서 허용되지 않은 path/method 조합 |
| `ParameterValidationError` | local compat 인자 오류 |

### Behavior Notes

- Codex profile은 vector store를 로컬 에뮬레이션으로 처리합니다.
- non-Codex profile은 vector store endpoint 네트워크 요청을 사용합니다.
- Codex profile에서 에뮬레이션이 다루지 않는 path 패턴은 `not_supported_on_codex_oauth`를 발생시킵니다.

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

- local mode의 list/search는 호환성 중심 구현이며 완전한 백엔드 동등성을 보장하지 않습니다.

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

| 메서드 | 파라미터 |
|---|---|
| `create` / `create_and_poll` | `vector_store_id`, 필수 `file_id` |
| `retrieve` / `poll` | `vector_store_id`, `file_id` |
| `list` | `vector_store_id` |
| `delete` | `vector_store_id`, `file_id` |
| `content` | `vector_store_id`, `file_id` (`files.content` 위임) |
| `upload` / `upload_and_poll` | `vector_store_id`, 필수 `file`, 선택 `purpose="assistants"` |
| `update` | 미지원 |

### Return Shapes

- `VectorStoreFile`: `id`, `object`, `vector_store_id`, `status`, `created_at`.
- `list`: `VectorStoreFile` dict 배열을 담은 dict.
- `delete`: `id`, `object`, `deleted` dict.
- `content`: raw `bytes`.

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `SDKRequestError` | provider/local compatibility 실패 |
| `KeyError` (경로에 따라 래핑) | local vector store membership에 파일 없음 |
| `NotSupportedError(code="not_supported")` | `vector_stores.files.update` 호출 |

### Behavior Notes

- local mode에서는 `file_ids` 배열로 membership을 관리합니다.
- `create_and_poll`, `poll`은 단순 alias이며 추가 원격 polling 워크플로우는 없습니다.
- `content`는 `vector_store_id`를 사용하지 않고 `client.files.content(file_id)`로 위임됩니다.

### Runnable Usage Snippets

```python
import io

uploaded = client.files.create(file=io.BytesIO(b"alpha gamma"), purpose="assistants")
vs = client.vector_stores.create(name="docs", file_ids=[])

attached = client.vector_stores.files.create(vs.id, file_id=uploaded.id)
print(attached.id, attached.vector_store_id)
```

### Pitfalls / Troubleshooting

- `content` 다운로드는 실제로 `file_id`만 중요합니다.

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

| 메서드 | 파라미터 |
|---|---|
| `create` / `create_and_poll` | `vector_store_id`, 필수 `file_ids: list[str]` |
| `retrieve` / `poll` | `vector_store_id`, `batch_id` |
| `list_files` | `vector_store_id`, `batch_id` |
| `cancel` | `vector_store_id`, `batch_id` |
| `upload_and_poll` | `vector_store_id`, 필수 `files: list[Any]`, 선택 `purpose` |

### Return Shapes

- `VectorStoreFileBatch`: `id`, `object`, `vector_store_id`, `status`, `created_at`, `file_counts`.
- `list_files`: `vector_stores.files.list(...)` 반환 dict.

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `SDKRequestError` | 내부 파일/벡터 스토어 작업 실패 |

### Behavior Notes

- batch 기록은 현재 로컬 in-memory 호환 객체입니다.
- `cancel`은 로컬 상태를 `cancelled`로 변경합니다.

### Runnable Usage Snippets

```python
batch = client.vector_stores.file_batches.create(vs.id, file_ids=[uploaded.id])
print(batch.id, batch.status)

listed = client.vector_stores.file_batches.list_files(vs.id, batch.id)
print(listed.get("object"))
```

### Pitfalls / Troubleshooting

- batch 상태는 호환성 중심 상태값이며, 실제 백엔드 워크플로우 상태로 간주하면 안 됩니다.
