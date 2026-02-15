[English](README.md) | [한국어](README.ko.md)

# oauth-codex

OpenAI 스타일 클라이언트 표면을 유지하면서 OAuth PKCE 인증을 제공하는 Codex 백엔드용 Python SDK입니다.

[![PyPI version](https://img.shields.io/pypi/v/oauth-codex.svg)](https://pypi.org/project/oauth-codex/)
[![Python](https://img.shields.io/pypi/pyversions/oauth-codex.svg)](https://pypi.org/project/oauth-codex/)
[![Publish to PyPI](https://github.com/dongju/project/codex-api/actions/workflows/publish-pypi.yml/badge.svg)](.github/workflows/publish-pypi.yml)

## Table of Contents

- [Why oauth-codex](#why-oauth-codex)
- [Feature Highlights](#feature-highlights)
- [Install](#install)
- [Quick Start](#quick-start)
- [Request Options at a Glance](#request-options-at-a-glance)
- [Supported Runtime Matrix](#supported-runtime-matrix)
- [Local Compatibility Behavior (Codex Profile)](#local-compatibility-behavior-codex-profile)
- [Errors and Validation Modes](#errors-and-validation-modes)
- [Documentation Index](#documentation-index)
- [Examples](#examples)
- [Development](#development)
- [Changelog](#changelog)

## Why oauth-codex

- 마이그레이션 친화적인 OpenAI 스타일 API 형태를 제공합니다.
- 사용자 계정 기반 워크플로우에 맞는 OAuth PKCE 인증을 사용합니다.
- Codex profile에서 `files`, `vector_stores`, 응답 연속성을 로컬 호환 계층으로 보완합니다.
- `pydantic` 기반 타입과 구조화된 SDK 예외를 제공합니다.

## Feature Highlights

| 영역 | 제공 내용 |
|---|---|
| Client surface | `OAuthCodexClient`, `AsyncOAuthCodexClient`, 모듈 레벨 lazy proxy (`oauth_codex.responses.create(...)`) |
| Runtime 지원 리소스 | `responses`, `responses.input_tokens`, `files`, `vector_stores` (+ `files`, `file_batches`), `models` |
| 요청 제어 옵션 | `extra_headers`, `extra_query`, `extra_body`, `validation_mode`, retry/timeout |
| Streaming | 정규화된 SSE 이벤트 (`text_delta`, `tool_call_*`, `usage`, `response_completed`) |
| 호환성 동작 | Codex profile에서 로컬 영속 저장소 기반 보정 |
| 구조 호환성 | OpenAI 2.17 스타일 리소스 트리를 노출하고, 미지원 호출은 `NotSupportedError(code="not_supported")` |

## Install

```bash
pip install oauth-codex
```

개발 설치:

```bash
python3 -m pip install -e ".[dev]"
```

## Quick Start

### Sync Client

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()

response = client.responses.create(
    model="gpt-5.3-codex",
    input="Return JSON with keys: ok, source",
    response_format={"type": "json_object"},
)

print(response.id)
print(response.output_text)
```

### Async Client

```python
import asyncio
from oauth_codex import AsyncOAuthCodexClient


async def main() -> None:
    client = AsyncOAuthCodexClient()
    response = await client.responses.create(
        model="gpt-5.3-codex",
        input="Summarize OAuth PKCE in 2 bullets",
    )
    print(response.output_text)


asyncio.run(main())
```

### Module-level Lazy Client

```python
import oauth_codex

oauth_codex.timeout = 90.0
oauth_codex.max_retries = 3

response = oauth_codex.responses.create(
    model="gpt-5.3-codex",
    input="hello",
)

print(response.output_text)
```

## Request Options at a Glance

주요 요청 옵션은 현재 `responses.create(...)`, `responses.stream(...)` 경로에서 사용됩니다.

- `extra_headers`: 요청 헤더에 병합되며 보호 헤더는 차단됩니다.
- `extra_query`: 쿼리 파라미터로 병합됩니다.
- `extra_body`: JSON body에 마지막으로 병합되어 기존 필드를 덮어쓸 수 있습니다.
- `validation_mode`: `"warn"`(기본), `"error"`, `"ignore"`.
- `store`: Codex profile에서는 `store_behavior` (`auto_disable`, `error`, `passthrough`)에 따라 동작합니다.

상세 규칙: [`docs/ko/methods/request_options.md`](docs/ko/methods/request_options.md)

## Supported Runtime Matrix

| 리소스 | 상태 | 비고 |
|---|---|---|
| `responses` | 지원 | `create`, `stream` |
| `responses.input_tokens` | 지원 | `count` |
| `files` | 지원 | create/retrieve/list/delete/content |
| `vector_stores` | 지원 | 루트 CRUD + search |
| `vector_stores.files` | 지원 | attach/list/delete/content/upload helper |
| `vector_stores.file_batches` | 지원 | create/retrieve/cancel/poll/list_files/upload_and_poll |
| `models` | 부분 지원 | `capabilities`, `retrieve`, `list`; `delete` 미지원 |
| 기타 OpenAI 스타일 리소스 | 구조만 노출 | `NotSupportedError(code="not_supported")` |

전체 매트릭스: [`docs/ko/unsupported-matrix.md`](docs/ko/unsupported-matrix.md)

## Local Compatibility Behavior (Codex Profile)

`base_url`이 Codex profile (`https://chatgpt.com/backend-api/codex`)이면, 백엔드 미지원 영역은 로컬 호환 계층이 처리합니다.

- `files.*`는 로컬 compatibility storage를 사용합니다.
- `vector_stores.*`는 로컬 에뮬레이션으로 동작합니다.
- `previous_response_id` 연속성은 로컬 continuity 기록으로 복원합니다.

호환 저장 경로 우선순위:

1. 생성자 인자 `compat_storage_dir`
2. 환경 변수 `CODEX_COMPAT_STORAGE_DIR`
3. `~/.oauth_codex/compat`

## Errors and Validation Modes

자주 사용하는 SDK 예외:

- `AuthRequiredError`
- `SDKRequestError`
- `NotSupportedError`
- `ParameterValidationError`
- `ContinuityError`
- `TokenStoreReadError` / `TokenStoreWriteError` / `TokenStoreDeleteError`

검증 모드:

- `validation_mode="warn"` (기본): 경고를 내고 요청은 계속 진행
- `validation_mode="error"`: 잘못된/미지원 파라미터에서 `ParameterValidationError` 발생
- `validation_mode="ignore"`: 검증 경고/에러를 생략

## Documentation Index

- 영문 문서: [`docs/en/index.md`](docs/en/index.md)
- 국문 문서: [`docs/ko/index.md`](docs/ko/index.md)

메서드 레퍼런스:

- [`docs/ko/methods/responses.md`](docs/ko/methods/responses.md)
- [`docs/ko/methods/files.md`](docs/ko/methods/files.md)
- [`docs/ko/methods/vector_stores.md`](docs/ko/methods/vector_stores.md)
- [`docs/ko/methods/models.md`](docs/ko/methods/models.md)
- [`docs/ko/methods/module_level.md`](docs/ko/methods/module_level.md)
- [`docs/ko/methods/request_options.md`](docs/ko/methods/request_options.md)

보조 문서:

- [`docs/migration_openai_to_oauth_codex.md`](docs/migration_openai_to_oauth_codex.md)
- [`docs/stream_event_schema_v1.md`](docs/stream_event_schema_v1.md)

## Examples

- `examples/login_smoke_test.py`
- `examples/request_options_smoke_test.py`
- `examples/module_level_smoke_test.py`
- `examples/async_smoke_test.py`

## Development

```bash
pytest -q
```

## Changelog

- [`CHANGELOG.md`](CHANGELOG.md)
