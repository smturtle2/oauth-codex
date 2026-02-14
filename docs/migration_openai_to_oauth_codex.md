# Migration: OpenAI SDK -> oauth-codex

## 1) Client

Before:

```python
from openai import OpenAI
client = OpenAI()
```

After:

```python
from oauth_codex import OAuthCodexClient
client = OAuthCodexClient()
```

Async:

```python
from oauth_codex import AsyncOAuthCodexClient
client = AsyncOAuthCodexClient()
```

## 2) API Mapping

| OpenAI-style | oauth-codex |
|---|---|
| `client.responses.create(...)` | `client.responses.create(...)` |
| `client.responses.input_tokens.count(...)` | `client.responses.input_tokens.count(...)` |
| `client.files.create(...)` | `client.files.create(...)` |
| `client.vector_stores.*` | `client.vector_stores.*` |

## 3) Response Object Mapping

| Field | oauth-codex ResponseCompat |
|---|---|
| `id` | `response.id` |
| `output` | `response.output` |
| `output_text` | `response.output_text` |
| `usage` | `response.usage` |
| `error` | `response.error` |
| reasoning summary | `response.reasoning_summary` |
| reasoning items | `response.reasoning_items` |
| encrypted reasoning | `response.encrypted_reasoning_content` |

## 4) Error Mapping

| Category | Exception |
|---|---|
| request/provider error | `SDKRequestError` |
| unsupported profile action | `NotSupportedError` |
| parameter validation | `ParameterValidationError` |
| continuity mismatch | `ContinuityError` |
| token store read/write/delete | `TokenStoreReadError` / `TokenStoreWriteError` / `TokenStoreDeleteError` |

## 5) Parameter Behavior Notes

- `store=True` + Codex OAuth profile: 기본 `auto_disable` 정책으로 `store=False` 전환
- `service_tier`: 기본 ignore+warn
- `validation_mode`: `warn`(기본), `error`, `ignore`
- `previous_response_id`: Codex OAuth profile에서는 로컬 연속성 저장소로 내부 에뮬레이션
- `max_tool_calls`: support (양수 정수 검증)
- `parallel_tool_calls`: support (bool 검증)
- `truncation`: support (`auto`/`disabled` 검증)
- `extra_headers`: support (헤더 병합, 보호 헤더 override 차단)
- `extra_query`: support (querystring 병합)
- `extra_body`: support (payload 마지막 merge로 override 허용)

Codex profile에서 backend 미지원 기능은 SDK 내부에서 자동 보완됩니다.

- `files.create` -> 로컬 영속 저장소로 처리
- `vector_stores.*` -> 로컬 영속 저장소로 처리
- `previous_response_id` -> 로컬 `responses/index.json` 기반 연속성 복원/검증
- `validate_model=True` -> 로컬 모델명 검증(non-empty string)
- 저장 경로 우선순위
  - `compat_storage_dir` 인자
  - `CODEX_COMPAT_STORAGE_DIR`
  - `~/.oauth_codex/compat`

## 6) Streaming Event Mapping

Recommended parser targets:

- `response_started`
- `text_delta`
- `reasoning_delta`
- `reasoning_done`
- `tool_call_started`
- `tool_call_arguments_delta`
- `tool_call_done`
- `usage`
- `response_completed`
- `error`

See also: `docs/stream_event_schema_v1.md`
