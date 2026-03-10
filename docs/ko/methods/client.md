[English](../../en/methods/client.md) | [한국어](client.md)

# Client 메서드

`oauth-codex`는 두 개의 1급 클라이언트를 제공합니다.

| 클래스 | import | 사용 상황 |
|---|---|---|
| `Client` | `from oauth_codex import Client` | 동기 / blocking 코드 |
| `AsyncClient` | `from oauth_codex import AsyncClient` | `async`/`await` 코드, 이벤트 루프 |

두 클라이언트는 같은 네임스페이스를 제공하며, `AsyncClient`만 비동기 메서드를 사용합니다.

## 생성

```python
from oauth_codex import Client

client = Client()
```

```python
from oauth_codex import AsyncClient

client = AsyncClient()
```

## 인증

필요할 때 `authenticate()`를 한 번 호출하면 인터랙티브 OAuth 로그인이 시작됩니다.

```python
client.authenticate()
await client.authenticate()
```

이후 요청에서는 저장된 토큰을 자동으로 재사용하고 만료 시 자동으로 갱신합니다.

## Chat Completions

```python
response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "안녕!"}],
)
print(response.choices[0].message.content)
```

```python
response = await client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "비동기 안녕!"}],
)
print(response.choices[0].message.content)
```

### 구조화 파싱

```python
from pydantic import BaseModel


class Summary(BaseModel):
    title: str
    score: int


completion = client.chat.completions.parse(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "title과 score를 가진 JSON을 반환해줘"}],
    response_format=Summary,
)
print(completion.parsed)
```

## Responses 리소스

`responses`는 더 낮은 수준의 backend payload shape를 그대로 다룹니다.

```python
response = client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "이 코드를 분석해줘"}],
)
print(response.output_text)
```

### 구조화 파싱

```python
response = client.responses.parse(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "title과 score를 가진 JSON을 반환해줘"}],
    response_format=Summary,
)
print(response.parsed)
```

### 스트리밍 이벤트

```python
for event in client.responses.stream(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "짧게 인사해줘"}],
):
    if event.type == "text_delta" and event.delta:
        print(event.delta, end="", flush=True)
```

### 입력 토큰 계산

```python
tokens = client.responses.input_tokens.count(
    model="gpt-5.3-codex",
    input="hello",
)
print(tokens.input_tokens)
```

## Beta Tool Loop

Python callable tool을 SDK가 여러 라운드에 걸쳐 실행하게 하려면 `beta.chat.completions.run_tools(...)`를 사용합니다.

```python
def add(a: int, b: int) -> int:
    return a + b


completion = client.beta.chat.completions.run_tools(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "1 + 2는 얼마야?"}],
    tools=[add],
)
print(completion.choices[0].message.content)
```

`AsyncClient`에서는 `await client.beta.chat.completions.arun_tools(...)`를 사용합니다.

## Files, Vector Stores, Models

```python
uploaded = client.files.create(file=b"hello", purpose="assistants")
vector_store = client.vector_stores.create(name="docs", file_ids=[uploaded.id])
linked = client.vector_stores.files.create(vector_store.id, file_id=uploaded.id)
batch = client.vector_stores.file_batches.create(vector_store.id, file_ids=[uploaded.id])
models = client.models.list()
print(uploaded.id, vector_store.id, linked.id, batch.id, models.object)
```

## 4.0에서 제거된 표면

- `authenticate_on_init`
- `generate`, `agenerate`, `stream`, `astream`
- `OAuthCodexClient`, `AsyncOAuthCodexClient`
- `oauth_codex.responses.create(...)` 같은 모듈 레벨 프록시 호출

## 함께 보기

- [제거된 API 안내](removed_apis.md)
- [마이그레이션 가이드](../../migration_openai_to_oauth_codex.md)
