# Changelog

## 2.1.0

### Added

- Public structured output support on `Client.generate/agenerate/stream/astream`:
  - new `output_schema` option (Pydantic model type or JSON schema dict)
  - new `strict_output` option (`output_schema` is strict by default)
- `generate/agenerate` now parse structured output into a JSON object when `output_schema` is set.
- Strict JSON schema utilities for response formats and tool parameter schemas.

## 2.0.0

### Breaking

- Public API was reduced to a single `Client` class with:
  - `generate(...)`
  - `stream(...)`
  - `agenerate(...)`
  - `astream(...)`
- Removed public surfaces:
  - `AsyncOAuthCodexClient`, `AsyncClient`
  - module-level proxies (`oauth_codex.responses/files/vector_stores/models`)
  - resource-style client access (`client.responses.*`, `client.files.*`, `client.vector_stores.*`, `client.models.*`)
  - `oauth_codex.compat` module exports
- Advanced per-request options are no longer public (`extra_headers`, `extra_query`, `extra_body`, `validation_mode`, `store_behavior`).

### Added

- `generate`-first UX with automatic function-calling loop.
- Image input support in `generate/stream/agenerate/astream`:
  - URL image inputs
  - local file paths converted to data URLs
- `reasoning_effort` public option with default `"medium"`.
- Stream APIs now support automatic function-calling continuation across rounds.

## 1.1.0

### Breaking

- 미지원 리소스/메서드 하드 삭제
  - 제거 리소스: `completions`, `chat`, `embeddings`, `images`, `audio`, `moderations`, `fine_tuning`, `beta`, `batches`, `uploads`, `realtime`, `conversations`, `evals`, `containers`, `videos`, `webhooks`
  - 제거 메서드: `responses.retrieve/cancel/delete/compact/parse`, `responses.input_items.*`, `models.delete`, `vector_stores.files.update`
- legacy 모듈 삭제: `oauth_codex.legacy_types`, `oauth_codex.legacy_auth`, `oauth_codex.client`
- legacy 타입은 `oauth_codex.core_types`로 대체
- legacy 에러 alias 삭제: `LLMRequestError`, `CodexOAuthLLMError`
- 스트림 이벤트 alias `tool_call_delta` 제거 (`tool_call_arguments_delta`만 유지)

## 1.0.0

### Breaking

- `CodexOAuthLLM` alias 제거
- legacy `generate/agenerate/generate_stream/agenerate_stream` 공개 표면 제거
- 패키지 내부 구조를 OpenAI 2.17 스타일로 재구성

### Added

- OpenAI 스타일 코어 모듈
  - `_client`, `_base_client`, `_resource`, `_types`, `_models`, `_exceptions`, `_module_client`
- `resources/` + `types/` 계층 도입
- module-level lazy client 패턴 (`oauth_codex.responses.create(...)`)
- OpenAI 2.17 리소스 트리 골격 전체 노출
- `with_raw_response`, `with_streaming_response` 계층 확장
- `pydantic` 기반 모델 계층

### Supported Runtime Resources

- `responses` (+ `input_tokens`)
- `files`
- `vector_stores` (+ `files`, `file_batches`)
- `models` (`capabilities`)

### Unsupported Runtime Resources

- 구조/모듈/클래스는 노출
- 호출 시 `NotSupportedError(code="not_supported")`

## 0.6.0

### Added

- OpenAI-style Responses 옵션 지원 확장
  - body 옵션: `max_tool_calls`, `parallel_tool_calls`, `truncation`
  - request 옵션: `extra_headers`, `extra_query`, `extra_body`
- 요청 헤더 보호 정책 추가
- Codex profile `previous_response_id` 내부 연속성 에뮬레이션

## 0.5.0

### Added

- Codex profile local compatibility backend
- Local compatibility storage path configuration

## 0.4.0

### Added

- OpenAI-compatible client surface
- 표준 에러/재시도/관측성 훅
