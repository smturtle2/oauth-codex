[English](../../en/methods/client.md) | [한국어](client.md)

# Client 메서드

`oauth-codex` v2는 `Client` 단일 클래스를 제공합니다.

## 생성

```python
from oauth_codex import Client

client = Client()
```

## 핵심 메서드

- `generate(...)`: 최종 텍스트를 반환하며, `output_schema` 사용 시 JSON 객체를 반환합니다.
- `stream(...)`: 텍스트 delta를 동기 이터레이터로 반환합니다.
- `agenerate(...)`: async 텍스트 생성이며, `output_schema` 사용 시 JSON 객체를 반환합니다.
- `astream(...)`: async 텍스트 스트림입니다.

## 공통 주요 옵션

- `prompt`: 텍스트 프롬프트
- `images`: 이미지 입력(URL 문자열 또는 로컬 파일 경로)
- `tools`: Python callable 리스트 (function calling 자동 실행)
- `model`: 생략 시 기본 `gpt-5.3-codex`
- `reasoning_effort`: `low | medium | high` (기본 `medium`)
- `temperature`, `top_p`, `max_output_tokens`
- `output_schema`: structured output용 Pydantic 모델 타입 또는 JSON schema dict
- `strict_output`: 툴/출력 스키마 strict 모드. `output_schema` 지정 시 기본 `True`

## 텍스트 생성

```python
text = client.generate("hello")
print(text)
```

## 이미지 입력 분석

```python
text = client.generate(
    "이 이미지를 설명해줘",
    images=["https://example.com/photo.png", "./photo.jpg"],
)
print(text)
```

로컬 파일 경로는 내부적으로 data URL로 변환됩니다.

## Function Calling (자동)

```python
def get_weather(city: str) -> dict:
    return {"city": city, "weather": "sunny"}

text = client.generate("서울 날씨 알려줘", tools=[get_weather])
```

단일 파라미터 Pydantic 입력 툴도 지원합니다.

```python
from pydantic import BaseModel


class ToolInput(BaseModel):
    query: str


def tool(input: ToolInput) -> str:
    return f"Tool received query: {input.query}"


text = client.generate("툴을 사용해줘", tools=[tool])
```

툴 실행 예외는 `{ "error": "..." }` 형태로 모델에 전달되어 루프가 이어집니다.

## Structured Output

```python
from pydantic import BaseModel


class Summary(BaseModel):
    title: str
    score: int


out = client.generate("JSON을 반환해줘", output_schema=Summary)
print(out)  # {"title": "...", "score": 1}
```

raw JSON schema dict도 지원합니다.

```python
out = client.generate(
    "JSON을 반환해줘",
    output_schema={
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
    },
)
```

`stream` / `astream`은 기존처럼 text delta만 반환합니다. structured JSON 파싱은 `generate` / `agenerate`에서만 수행됩니다.

## 스트리밍

```python
for delta in client.stream("hello"):
    print(delta, end="")
```

## Async

```python
text = await client.agenerate("hello")

async for delta in client.astream("hello"):
    print(delta, end="")
```

## 참고

- [제거된 API 안내](removed_apis.md)
- [Migration 문서](../../migration_openai_to_oauth_codex.md)
