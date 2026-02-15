[English](../../en/methods/removed_apis.md) | [한국어](removed_apis.md)

# 제거된 API 안내 (v2)

v2부터 공개 API는 `Client` 단일 클래스만 제공합니다.

## 제거된 공개 경로

- `AsyncOAuthCodexClient`, `AsyncClient`
- module-level proxy (`oauth_codex.responses`, `oauth_codex.files`, `oauth_codex.vector_stores`, `oauth_codex.models`)
- 리소스 스타일 (`client.responses.*`, `client.files.*`, `client.vector_stores.*`, `client.models.*`)
- `oauth_codex.compat` 공개 모듈
- 고급 request 옵션 공개 인터페이스

## 대체 사용법

- 텍스트 생성: `client.generate(...)`
- 텍스트 스트림: `client.stream(...)`
- async 생성: `await client.agenerate(...)`
- async 스트림: `async for d in client.astream(...): ...`
- 이미지 입력 분석: `images=` (URL/로컬 경로)
- function calling: `tools=[callable, ...]` (자동 실행)

## 참고

- [Client 메서드](client.md)
- [Migration 문서](../../migration_openai_to_oauth_codex.md)
