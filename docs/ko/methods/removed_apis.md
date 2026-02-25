[English](../../en/methods/removed_apis.md) | [한국어](removed_apis.md)

# 제거된 API 안내 (v2)

v2부터 모듈 수준 프록시 표면과 레거시 `AsyncOAuthCodexClient` 클래스명이 **공개** API에서 제거되었습니다. 모던 `AsyncClient` 별칭은 **완전히 지원**되며, 권장되는 비동기 엔트리 포인트입니다.

## 제거된 공개 경로

- `AsyncOAuthCodexClient` (내부 클래스명 — `AsyncClient`를 사용하세요)
- 모듈 수준 리소스 프록시: `oauth_codex.responses`, `oauth_codex.files`, `oauth_codex.vector_stores`, `oauth_codex.models`
- 리소스 스타일 단축경로: `client.files.*`, `client.vector_stores.*`, `client.models.*`
- `oauth_codex.compat` 공개 모듈
- 고급 request 옵션 공개 인터페이스

> **`AsyncClient`는 제거되지 않았습니다.** `oauth_codex`에서 정식으로 export되며, 권장 비동기 클라이언트 클래스입니다.

## 현재 공개 API

```python
from oauth_codex import Client       # 동기 클라이언트
from oauth_codex import AsyncClient  # 비동기 클라이언트 (완전 지원)
```

## 대체 사용법 매핑

| 이전 / 제거됨 | 대체 |
|---|---|
| `AsyncOAuthCodexClient(...)` | `AsyncClient(...)` |
| `oauth_codex.responses.create(...)` | `client.responses.create(...)` |
| 모듈 수준 프록시 | `Client` 또는 `AsyncClient` 인스턴스 먼저 생성 |

### 텍스트 생성

```python
# 동기
text = client.generate(messages)

# 비동기 (AsyncClient)
text = await async_client.generate(messages)

# 동기 Client의 async 브릿지
text = await client.agenerate(messages)
```

### 스트리밍

```python
# 동기
for chunk in client.stream(messages):
    print(chunk, end="")

# 비동기 (AsyncClient)
async for chunk in async_client.stream(messages):
    print(chunk, end="")

# 동기 Client의 async 브릿지
async for chunk in client.astream(messages):
    print(chunk, end="")
```

### 이미지 입력

```python
messages = [{"role": "user", "content": [{"type": "input_image", "image_url": "..."}]}]
response = client.chat.completions.create(model="gpt-5.3-codex", messages=messages)
```

### Function calling

```python
tools = [my_callable]  # Python callable 리스트 — 자동 실행
text = client.generate(messages, tools=tools)
```

## 참고

- [Client 메서드](client.md)
- [Migration 문서](../../migration_openai_to_oauth_codex.md)
