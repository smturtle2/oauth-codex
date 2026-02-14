# Changelog

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
