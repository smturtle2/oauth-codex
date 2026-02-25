[English](../../en/methods/client.md) | [한국어](client.md)

# Client 메서드

`oauth-codex`는 두 개의 대칭 클라이언트 클래스를 제공합니다:

| 클래스 | 임포트 | 사용 시점 |
|---|---|---|
| `Client` | `from oauth_codex import Client` | 동기(블로킹) 코드 |
| `AsyncClient` | `from oauth_codex import AsyncClient` | `async`/`await` 코드, 이벤트 루프 |

두 클래스 모두 **동일한** `chat.completions.create`, `generate`, `stream`, `responses` 인터페이스를 제공합니다. `AsyncClient` 메서드는 async-native(`await` / `async for`)이며, `Client` 메서드는 동기입니다 — 단, `agenerate`/`astream` 브릿지 메서드를 통해 sync Client에서 async도 호출 가능합니다.

---

## 생성

### Sync Client

```python
from oauth_codex import Client

client = Client()
```

### Async Client

```python
from oauth_codex import AsyncClient

client = AsyncClient()
```

생성 시 즉시 인증 (sync 전용):

```python
client = Client(authenticate_on_init=True)
```

---

## 인증

토큰은 로컬에 저장되며 자동으로 갱신됩니다. 저장된 토큰이 없거나 만료된 경우 대화형 OAuth 로그인이 실행됩니다.

```python
# 동기: 로그인 완료까지 블록
client.authenticate()

# 비동기: 이벤트 루프 비블로킹
await client.authenticate()
```

생성자 옵션:

```python
client = Client(authenticate_on_init=True)  # __init__에서 바로 로그인
```

---

## Chat Completions

기본 인터페이스 — OpenAI Python SDK와 동일합니다.

### Sync 예시

```python
response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "안녕!"}],
)
print(response.choices[0].message.content)
```

### Async 예시

```python
response = await client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "안녕 async!"}],
)
print(response.choices[0].message.content)
```

### 시스템 프롬프트 포함 예시

```python
response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[
        {"role": "system", "content": "당신은 유능한 어시스턴트입니다."},
        {"role": "user", "content": "리스트를 정렬하는 Python 함수를 작성해줘."},
    ],
    temperature=0.7,
    max_tokens=500,
)
print(response.choices[0].message.content)
```

---

## `generate` — 자동 툴 실행을 포함한 텍스트 생성

`generate`는 최종 텍스트(또는 `output_schema` 지정 시 검증된 dict)를 반환합니다. 멀티 라운드 function calling을 자동으로 처리합니다.

### Sync (`Client`)

```python
text = client.generate([{"role": "user", "content": "안녕"}])
print(text)
```

### Async (`AsyncClient`)

```python
text = await client.generate([{"role": "user", "content": "안녕"}])
print(text)
```

> **참고:** sync `Client`에도 async 편의 메서드 `agenerate`가 있습니다:
> `text = await sync_client.agenerate([...])`

---

## `stream` — 스트리밍 텍스트 델타

### Sync 스트리밍 (`Client`)

```python
for chunk in client.stream([{"role": "user", "content": "이야기를 들려줘"}]):
    print(chunk, end="", flush=True)
```

### Async 스트리밍 (`AsyncClient`)

```python
async for chunk in client.stream([{"role": "user", "content": "이야기를 들려줘"}]):
    print(chunk, end="", flush=True)
```

> sync `Client`에도 async 편의 메서드 `astream`이 있습니다.

---

## 이미지 입력 분석

`client.chat.completions.create`로 멀티모달 콘텐츠를 전달합니다:

```python
response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "이 이미지를 설명해줘"},
                {"type": "input_image", "image_url": "https://example.com/photo.png"},
            ],
        }
    ],
)
```

---

## Function Calling (자동)

Python callable을 직접 전달하면 됩니다. SDK가 함수 시그니처를 직렬화하고, 툴 정의를 모델에 전송하며, 반환된 호출을 자동으로 실행합니다.

```python
def get_weather(city: str) -> dict:
    return {"city": city, "weather": "sunny"}

# 동기
text = client.generate(
    [{"role": "user", "content": "서울 날씨 알려줘"}],
    tools=[get_weather],
)

# 비동기
text = await async_client.generate(
    [{"role": "user", "content": "서울 날씨 알려줘"}],
    tools=[get_weather],
)
```

`AsyncClient.generate`(및 `Client.agenerate`)에서는 async 툴도 지원됩니다:

```python
async def fetch_data(url: str) -> dict:
    ...  # async I/O

text = await async_client.generate([...], tools=[fetch_data])
```

---

## Structured Output

Pydantic 모델 또는 JSON Schema dict를 전달하면 응답이 검증된 dict로 반환됩니다.

```python
from pydantic import BaseModel

class Summary(BaseModel):
    title: str
    score: int

out = client.generate(
    [{"role": "user", "content": "JSON을 반환해줘"}],
    output_schema=Summary,
)
print(out)  # {"title": "...", "score": 1}
```

---

## Responses 리소스 (저수준)

Codex 백엔드 responses API에 직접 접근할 때 사용합니다:

```python
# 동기
response = client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "코드를 분석해줘."}],
)

# 비동기
response = await client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "코드를 분석해줘."}],
)
```

---

## API 요약

### `oauth_codex.Client` (동기)

| 메서드 | 반환값 |
|---|---|
| `client.chat.completions.create(...)` | `ChatCompletion` |
| `client.responses.create(...)` | raw response |
| `client.generate(messages, ...)` | `str \| dict` |
| `client.stream(messages, ...)` | `Iterator[str]` |
| `client.agenerate(messages, ...)` | `Awaitable[str \| dict]` |
| `client.astream(messages, ...)` | `AsyncIterator[str]` |
| `client.authenticate()` | `None` |

### `oauth_codex.AsyncClient` (비동기)

| 메서드 | 반환값 |
|---|---|
| `await client.chat.completions.create(...)` | `ChatCompletion` |
| `await client.responses.create(...)` | raw response |
| `await client.generate(messages, ...)` | `str \| dict` |
| `async for chunk in client.stream(...)` | `AsyncIterator[str]` |
| `await client.authenticate()` | `None` |

---

## 참고

- [제거된 API 안내](removed_apis.md)
- [Migration 문서](../../migration_openai_to_oauth_codex.md)
