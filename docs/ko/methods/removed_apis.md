[English](../../en/methods/removed_apis.md) | [한국어](removed_apis.md)

# 제거된 API 안내 (v4.0)

4.0에서는 generate-first 및 레거시 호환 표면이 제거되고, 리소스형 `Client` / `AsyncClient` 인터페이스만 공식 지원됩니다.

## 제거된 API

- `authenticate_on_init`
- `generate`, `agenerate`, `stream`, `astream`
- `OAuthCodexClient`
- `AsyncOAuthCodexClient`
- 모듈 수준 프록시: `oauth_codex.responses`, `oauth_codex.files`, `oauth_codex.vector_stores`, `oauth_codex.models`
- local compatibility storage 및 레거시 continuation internals
- `oauth_codex.compat`

## 대체 방법

| 제거된 항목 | 대체 방법 |
|---|---|
| `Client(authenticate_on_init=True)` | `client = Client(); client.authenticate()` |
| `AsyncOAuthCodexClient(...)` | `AsyncClient(...)` |
| `client.generate(...)` | `client.chat.completions.create(...)` 또는 `client.responses.create(...)` |
| `client.stream(...)` | `client.responses.stream(...)` |
| `client.generate(..., tools=[...])` | `client.beta.chat.completions.run_tools(...)` |
| `oauth_codex.responses.create(...)` | `client.responses.create(...)` |
| 모듈 수준 프록시 | 먼저 `Client` 또는 `AsyncClient`를 생성 |

## 함께 보기

- [Client 메서드](client.md)
- [마이그레이션 가이드](../../migration_openai_to_oauth_codex.md)
