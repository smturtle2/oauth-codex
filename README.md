# oauth-codex

OAuth PKCE 기반 Codex SDK with OpenAI-compatible surface.

## What's New (0.5.0)

- OpenAI-style 표면을 코어 클라이언트에 직접 통합
  - `OAuthCodexClient.responses.create(...)`
  - `OAuthCodexClient.responses.input_tokens.count(...)`
  - `OAuthCodexClient.files.create(...)`
  - `OAuthCodexClient.vector_stores.*`
  - `OAuthCodexClient.models.capabilities(...)`
- 기존 `CodexOAuthLLM` API는 하위호환 alias로 유지
- `validation_mode` (`warn`/`error`/`ignore`) + 파라미터 검증기 추가
- `store_behavior` (`auto_disable`/`error`/`passthrough`) 추가
- 표준 에러 모델(`SDKRequestError`) 및 토큰 저장소 read/write/delete 분리 예외 추가
- reasoning/tool-call 스트리밍 이벤트 스키마 v1 고정
- 재시도 기본 정책 추가
  - `401`: refresh 후 재시도
  - `429/5xx`: 지수 백오프 + jitter
- 관측성 훅 추가
  - `on_request_start`, `on_request_end`, `on_auth_refresh`, `on_error`
- Codex profile 로컬 호환 백엔드 추가
  - `files.create`, `vector_stores.*` 자동 로컬 폴백
  - `validate_model=True` 시 로컬 모델명 검증

## Highlights

- `CodexOAuthLLM` legacy API 유지 (`generate/agenerate/generate_stream/agenerate_stream`)
- OpenAI-compatible client 추가
  - `OAuthCodexClient.responses.create(...)`
  - `OAuthCodexClient.responses.input_tokens.count(...)`
  - `OAuthCodexClient.files.create(...)`
  - `OAuthCodexClient.vector_stores.*`
- Sync/async 옵션/이벤트/에러 동등성 강화
- OAuth 토큰 수명 API
  - `is_authenticated()`
  - `is_expired()`
  - `refresh_if_needed()`
- 표준 에러 모델 + 재시도 정책(401 refresh, 429/5xx backoff)
- 관측성 훅
  - `on_request_start`, `on_request_end`, `on_auth_refresh`, `on_error`

## Requirements

- Python 3.11+

## Install

```bash
pip install oauth-codex
```

For local development:

```bash
python3 -m pip install -e ".[dev]"
```

## Quick Start (Legacy)

```python
from oauth_codex import CodexOAuthLLM

llm = CodexOAuthLLM()
text = llm.generate(model="gpt-5.3-codex", prompt="Explain OAuth PKCE in 3 bullets.")
print(text)
```

## Quick Start (OpenAI-compatible)

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()

response = client.responses.create(
    model="gpt-5.3-codex",
    input="Return JSON with keys: ok, source",
    response_format={"type": "json_object"},
    reasoning={"effort": "high", "summary": "auto"},
)

print(response.id)
print(response.output_text)
print(response.usage)
```

## OpenAI Compatibility Surface

- `OAuthCodexClient.responses.create(...)`
- `OAuthCodexClient.responses.input_tokens.count(...)`
- `OAuthCodexClient.files.create(...)`
- `OAuthCodexClient.vector_stores.create/retrieve/list/update/delete/search(...)`
- `OAuthCodexClient.models.capabilities(model)`

`AsyncOAuthCodexClient`에서 동일 리소스를 async로 제공합니다.

Codex profile(`https://chatgpt.com/backend-api/codex`)에서는 backend 미지원 기능을 라이브러리 내부에서 자동으로 보완합니다.

- `files.create`, `vector_stores.*` -> 로컬 영속 저장소로 처리
- `validate_model=True` -> 로컬 모델명(non-empty string) 검증
- 저장 경로 우선순위
  - `compat_storage_dir` 인자
  - `CODEX_COMPAT_STORAGE_DIR`
  - `~/.oauth_codex/compat` (기본)

예시:

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient(compat_storage_dir="~/.oauth_codex/compat")
```

## Parameter Policy (Code + Docs)

| Parameter | Default Policy | Notes |
|---|---|---|
| `temperature` | support | 전달 + 타입/범위 검증 |
| `top_p` | support | 전달 + 타입/범위 검증 |
| `max_output_tokens` | support | 전달 + 양수 정수 검증 |
| `metadata` | support | dict 검증 후 전달 |
| `include` | support | `list[str]` 검증 후 전달 |
| `service_tier` | ignore+warn | `validation_mode="error"`일 때 예외 |
| `store` | auto-disable | Codex OAuth profile에서 `True`면 `False`로 보정 + 경고 |

Validation mode:

- `warn` (default)
- `error`
- `ignore`

Store behavior:

- `auto_disable` (default)
- `error`
- `passthrough`

## Streaming Event Schema

이벤트 타입은 `schema_version="v1"` 기준으로 고정됩니다.

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

자세한 스키마: `docs/stream_event_schema_v1.md`

## Error Model

`SDKRequestError` fields:

- `status_code`
- `provider_code`
- `user_message`
- `retryable`
- `request_id`
- `raw_error`

Token store failures:

- `TokenStoreReadError`
- `TokenStoreWriteError`
- `TokenStoreDeleteError`

Unsupported profile actions:

- `NotSupportedError`

## Retry Policy

Default:

- `401`: refresh 후 1회 재시도
- `429/5xx`: 지수 백오프 + jitter 재시도

## Authentication and Storage

- 최초 인증이 없으면 OAuth 로그인 플로우 실행
- 기본 저장 우선순위
  - keyring: `oauth-codex`
  - file fallback: `~/.oauth_codex/auth.json`
- legacy migration
  - keyring: `codex-oauth-llm`
  - file: `~/.codex_oauth_llm/auth.json`

## Environment Variables

- `CODEX_OAUTH_CLIENT_ID`
- `CODEX_OAUTH_SCOPE`
- `CODEX_OAUTH_AUDIENCE`
- `CODEX_OAUTH_REDIRECT_URI`
- `CODEX_OAUTH_DISCOVERY_URL`
- `CODEX_OAUTH_AUTHORIZATION_ENDPOINT`
- `CODEX_OAUTH_TOKEN_ENDPOINT`
- `CODEX_OAUTH_ORIGINATOR`
- `CODEX_COMPAT_STORAGE_DIR`

## Migration Guide

OpenAI SDK -> oauth-codex 대응표:

- `docs/migration_openai_to_oauth_codex.md`

## Development

```bash
python3 -m pip install -e ".[dev]"
pytest -q
```
