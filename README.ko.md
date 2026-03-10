[English](README.md) | [한국어](README.ko.md)

# oauth-codex

Codex 백엔드를 위한 OAuth PKCE 기반 Python SDK입니다.

## 핵심 특징

- `Client`, `AsyncClient` 기반 리소스형 SDK
- OAuth PKCE 전용 인증과 자동 토큰 갱신
- `chat.completions.create(...)` 및 `responses.create(...)`
- `beta.chat.completions.run_tools(...)`를 통한 callable tool loop 지원

## 설치

```bash
pip install oauth-codex
```

Python 3.11 이상이 필요합니다.

## 빠른 시작

### 동기 클라이언트

```python
from oauth_codex import Client

client = Client()
client.authenticate()

completion = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "oauth-codex 안녕"}],
)
print(completion.choices[0].message.content)
```

### 비동기 클라이언트

```python
import asyncio

from oauth_codex import AsyncClient


async def main():
    client = AsyncClient()
    await client.authenticate()

    completion = await client.chat.completions.create(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "비동기 호출"}],
    )
    print(completion.choices[0].message.content)


asyncio.run(main())
```

## 인증

이 SDK는 API 키를 지원하지 않고 OAuth PKCE만 사용합니다.

최초 인증 시 SDK가 브라우저용 인증 URL을 출력하고, 로그인 후 리디렉트된 `localhost` callback URL을 터미널에 붙여넣도록 안내합니다. 이후에는 저장된 토큰을 자동으로 재사용하고 만료 시 자동으로 갱신합니다.

```python
client = Client()
client.authenticate()
```

## 주요 API

### Chat Completions

```python
response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "정렬 함수를 작성해줘"}],
)
print(response.choices[0].message.content)
```

### Responses 리소스

```python
response = client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "다음 코드를 분석해줘"}],
)
print(response.output_text)
```

### 스트리밍

```python
for event in client.responses.stream(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "세 단어로 인사해줘"}],
):
    if event.type == "text_delta" and event.delta:
        print(event.delta, end="", flush=True)
```

### 구조화 출력

```python
from pydantic import BaseModel


class Summary(BaseModel):
    title: str
    score: int


response = client.responses.parse(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "title과 score를 가진 JSON을 반환해줘"}],
    response_format=Summary,
)
print(response.parsed)
```

### Tool Loop

```python
def add(a: int, b: int) -> int:
    return a + b


completion = client.beta.chat.completions.run_tools(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "2 + 3은 얼마야?"}],
    tools=[add],
)
print(completion.choices[0].message.content)
```

## 제공 네임스페이스

- `client.chat.completions`
- `client.responses`
- `client.files`
- `client.vector_stores`
- `client.vector_stores.files`
- `client.vector_stores.file_batches`
- `client.models`
- `client.beta.chat.completions`

`AsyncClient`도 같은 네임스페이스를 비동기 방식으로 제공합니다.

## 4.0에서 제거된 표면

- `authenticate_on_init`
- `generate`, `agenerate`, `stream`, `astream`
- 레거시 `OAuthCodexClient`, `AsyncOAuthCodexClient`
- `oauth_codex.responses.create(...)` 같은 모듈 레벨 프록시 호출

## 문서

- 영문 문서: [`docs/en/index.md`](docs/en/index.md)
- 한국어 문서: [`docs/ko/index.md`](docs/ko/index.md)

## 개발

```bash
pip install -e .[dev]
pytest -q
python -m build
```

## 변경 이력

[CHANGELOG.md](CHANGELOG.md)
