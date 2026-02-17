[English](README.md) | [한국어](README.ko.md)

# oauth-codex

Codex 백엔드를 위한 OAuth PKCE 기반 Python SDK입니다.

## 핵심 변경점 (v2)

- 공개 클라이언트는 `Client` 하나만 제공합니다.
- 기본 사용 흐름은 `generate` 중심입니다.
- async는 동일 클래스의 `agenerate`, `astream` 메서드로 제공합니다.
- 텍스트 생성, 이미지 입력 분석, function calling 자동 실행, `reasoning_effort`를 지원합니다.

## 설치

```bash
pip install oauth-codex
```

## 빠른 시작

```python
from oauth_codex import Client

client = Client()
text = client.generate([{"role": "user", "content": "hello"}])
print(text)
```

## 이미지 입력

```python
text = client.generate(
    [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "이 이미지를 설명해줘"},
                {"type": "input_image", "image_url": "https://example.com/cat.png"},
                {"type": "input_image", "image_url": "data:image/jpeg;base64,..."},
            ],
        }
    ],
)
print(text)
```

## Function Calling (자동 루프)

```python
def add(a: int, b: int) -> dict:
    return {"sum": a + b}

text = client.generate(
    [{"role": "user", "content": "2+3 계산해줘"}],
    tools=[add],
)
print(text)
```

단일 파라미터 Pydantic 입력 툴도 지원합니다.

```python
from pydantic import BaseModel


class ToolInput(BaseModel):
    query: str


def tool(input: ToolInput) -> str:
    return f"Tool received query: {input.query}"


text = client.generate([{"role": "user", "content": "툴을 사용해줘"}], tools=[tool])
print(text)
```

툴 실행 중 예외가 발생하면 SDK는 `{\"error\": ...}` 형태로 모델에 전달하고 루프를 계속 진행합니다.

## Structured Output (Strict JSON Schema / Pydantic)

`generate` / `agenerate`는 `output_schema`로 검증된 JSON 객체 출력을 받을 수 있습니다.

```python
from pydantic import BaseModel
from oauth_codex import Client


class Summary(BaseModel):
    title: str
    score: int


client = Client()
out = client.generate(
    [{"role": "user", "content": "title, score 키를 가진 JSON을 반환해줘"}],
    output_schema=Summary,
)
print(out)  # {"title": "...", "score": 1}
```

raw JSON schema 객체를 직접 전달할 수도 있습니다.

```python
out = client.generate(
    [{"role": "user", "content": "{\"ok\": true} 형태 JSON을 반환해줘"}],
    output_schema={
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
    },
)
print(out)  # {"ok": True}
```

`output_schema`를 지정하면 `strict_output`을 따로 주지 않는 한 strict 모드가 기본 활성화됩니다.
`stream` / `astream`은 기존처럼 text delta만 반환하며 최종 JSON 객체 파싱은 하지 않습니다.

## Async

```python
import asyncio
from oauth_codex import Client


async def main() -> None:
    client = Client()
    text = await client.agenerate([{"role": "user", "content": "hello async"}])
    print(text)


asyncio.run(main())
```

## 버전 2.0 브레이킹 변경

- 제거됨: `AsyncOAuthCodexClient`, module-level proxies, `client.responses/files/vector_stores/models`, `oauth_codex.compat`
- 단일 진입점: `Client.generate/stream/agenerate/astream`

## 문서

- 영문 인덱스: [`docs/en/index.md`](docs/en/index.md)
- 국문 인덱스: [`docs/ko/index.md`](docs/ko/index.md)

## 개발

```bash
pytest -q
```

## 변경 이력

- [`CHANGELOG.md`](CHANGELOG.md)
