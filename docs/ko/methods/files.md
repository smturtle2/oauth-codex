[English](../../en/methods/files.md) | [한국어](files.md)

# Files 메서드

이 문서는 `oauth-codex`의 `files` 런타임 메서드를 설명합니다.

## Method Summary

| 메서드 | 지원 여부 | 비고 |
|---|---|---|
| `files.create(...)` | 지원 | 파일 업로드/메타데이터 생성 |
| `files.retrieve(...)` | 지원 | 단일 파일 조회 |
| `files.list(...)` | 지원 | 파일 목록 조회 |
| `files.delete(...)` | 지원 | 파일 삭제 |
| `files.content(...)` | 지원 | 원본 바이트 다운로드 |
| `files.retrieve_content(...)` | 지원 | `content(...)` alias |
| `files.wait_for_processing(...)` | 지원 | 상태가 완료될 때까지 polling |

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

| 파라미터 | 타입 | 필수 | 기본값 | 검증/동작 |
|---|---|---|---|---|
| `file` | `Any` | 예 | - | HTTP multipart/local compat 계층이 처리 가능한 파일 입력 |
| `purpose` | `str` | 예 | - | 용도 문자열 (보통 `"assistants"`) |
| `**metadata` | `dict` | 아니오 | `{}` | 추가 메타데이터 전달 |

### Return Shape

`FileObject` 반환:

- `id: str`
- `object: str` (`"file"`)
- `bytes: int | None`
- `created_at: int | None`
- `filename: str | None`
- `purpose: str | None`
- `metadata: dict | None`

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `AuthRequiredError` | 네트워크 호출이 필요한 경로에서 인증 누락 |
| `SDKRequestError` | provider 실패, local compatibility 저장소 오류 |
| `ParameterValidationError` | local compatibility 입력 오류 |

### Behavior Notes

- Codex profile에서는 file 작업을 local compatibility storage로 처리합니다.
- non-Codex profile에서는 `/files` multipart 업로드를 사용합니다.

### Runnable Usage Snippets

```python
import io
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()
out = client.files.create(file=io.BytesIO(b"alpha beta"), purpose="assistants")
print(out.id)
```

### Pitfalls / Troubleshooting

- Codex profile에서는 파일 레코드가 원격이 아니라 로컬에 저장됩니다.

## `files.retrieve`

### Sync / Async / Module-level Signatures

```python
client.files.retrieve(file_id: str) -> FileObject
await client.files.retrieve(file_id: str) -> FileObject
oauth_codex.files.retrieve(file_id)
```

### Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 검증/동작 |
|---|---|---|---|---|
| `file_id` | `str` | 예 | - | 대상 파일 ID |

### Return Shape

- `FileObject` (`files.create`와 동일).

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `SDKRequestError` | not found/provider/local 저장소 오류 |

### Behavior Notes

- Codex profile 조회는 local compatibility index에서 읽습니다.

### Runnable Usage Snippets

```python
file_obj = client.files.retrieve("file_123")
print(file_obj.filename, file_obj.purpose)
```

### Pitfalls / Troubleshooting

- 로컬 저장소에서 삭제/미존재 상태면 SDK request 오류로 매핑됩니다.

## `files.list`

### Sync / Async / Module-level Signatures

```python
client.files.list(*, after=None, limit=None, order=None, purpose=None) -> dict
await client.files.list(*, after=None, limit=None, order=None, purpose=None) -> dict
oauth_codex.files.list(...)
```

### Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 검증/동작 |
|---|---|---|---|---|
| `after` | `str | None` | 아니오 | `None` | cursor 힌트 |
| `limit` | `int | None` | 아니오 | `None` | 양수 권장 |
| `order` | `str | None` | 아니오 | `None` | 로컬에서는 `"desc"`면 역순 |
| `purpose` | `str | None` | 아니오 | `None` | purpose 필터 |

### Return Shape

- `object`, `data`, paging 유사 필드가 있는 dict.
- `data`는 정규화된 `FileObject` dict 항목.

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `SDKRequestError` | provider/local 저장소 실패 |

### Behavior Notes

- Codex profile local list는 현재 `has_more=False` 반환.

### Runnable Usage Snippets

```python
files_out = client.files.list(limit=20, order="desc")
print(files_out["object"], len(files_out.get("data", [])))
```

### Pitfalls / Troubleshooting

- local compat 모드의 pagination 필드는 백엔드와 완전 동일하다고 가정하면 안 됩니다.

## `files.delete`

### Sync / Async / Module-level Signatures

```python
client.files.delete(file_id: str) -> FileDeleted
await client.files.delete(file_id: str) -> FileDeleted
oauth_codex.files.delete(file_id)
```

### Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 검증/동작 |
|---|---|---|---|---|
| `file_id` | `str` | 예 | - | 대상 파일 ID |

### Return Shape

`FileDeleted` 반환:

- `id: str`
- `object: str` (`"file.deleted"`)
- `deleted: bool`

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `SDKRequestError` | provider/local 저장소 실패 |

### Behavior Notes

- Codex profile에서는 local index와 blob(`<file_id>.bin`)를 정리합니다.

### Runnable Usage Snippets

```python
deleted = client.files.delete("file_123")
print(deleted.deleted)
```

### Pitfalls / Troubleshooting

- local mode에서는 없는 파일 삭제도 구조화된 삭제 응답을 돌려줄 수 있습니다.

## `files.content`

### Sync / Async / Module-level Signatures

```python
client.files.content(file_id: str) -> bytes
await client.files.content(file_id: str) -> bytes
oauth_codex.files.content(file_id)
```

### Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 검증/동작 |
|---|---|---|---|---|
| `file_id` | `str` | 예 | - | 대상 파일 ID |

### Return Shape

- 파일 원본 `bytes`.

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `SDKRequestError` | HTTP/content endpoint 오류 |
| `KeyError` (경로에 따라 래핑) | 로컬 blob 미존재 |

### Behavior Notes

- Codex profile: local blob bytes를 반환.
- non-Codex profile: `/files/{file_id}/content` GET.

### Runnable Usage Snippets

```python
data = client.files.content("file_123")
print(len(data))
```

### Pitfalls / Troubleshooting

- binary 데이터이므로 텍스트 디코딩은 인코딩을 확실히 아는 경우에만 하세요.

## `files.retrieve_content`

### Sync / Async / Module-level Signatures

```python
client.files.retrieve_content(file_id: str) -> bytes
await client.files.retrieve_content(file_id: str) -> bytes
oauth_codex.files.retrieve_content(file_id)
```

### Parameters

- `files.content(...)`와 동일.

### Return Shape

- `files.content(...)`와 동일한 `bytes`.

### Error Cases

- `files.content(...)`와 동일.

### Behavior Notes

- alias 편의 메서드입니다.

### Runnable Usage Snippets

```python
blob = client.files.retrieve_content("file_123")
```

### Pitfalls / Troubleshooting

- 팀 코드에서 `content`와 `retrieve_content` 중 하나로 통일하는 것이 좋습니다.

## `files.wait_for_processing`

### Sync / Async / Module-level Signatures

```python
client.files.wait_for_processing(file_id: str, *, timeout: float = 60.0, poll_interval: float = 0.5) -> FileObject
await client.files.wait_for_processing(file_id: str, *, timeout: float = 60.0, poll_interval: float = 0.5) -> FileObject
oauth_codex.files.wait_for_processing(...)
```

### Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 검증/동작 |
|---|---|---|---|---|
| `file_id` | `str` | 예 | - | 대상 파일 ID |
| `timeout` | `float` | 아니오 | `60.0` | polling timeout(초) |
| `poll_interval` | `float` | 아니오 | `0.5` | polling 간격(초) |

### Return Shape

- 완료 조건 또는 timeout 직전의 최신 `FileObject`.

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `SDKRequestError` | polling 중 retrieve 실패 |

### Behavior Notes

- metadata 상태가 `None`, `processed`, `completed` 중 하나면 종료.
- timeout 초과 시 마지막 조회 결과를 그대로 반환.

### Runnable Usage Snippets

```python
final_file = client.files.wait_for_processing("file_123", timeout=30.0)
print(final_file.metadata)
```

### Pitfalls / Troubleshooting

- local compat 모드에서는 상태가 비어(`None`) 즉시 종료될 수 있습니다.
