[English](README.md) | [한국어](README.ko.md)

# oauth-codex

Codex 백엔드를 위한 OAuth PKCE 기반 Python SDK입니다.

## 주요 특징

- **OpenAI 스타일 API**: `client.chat.completions.create` 및 `client.responses.create`를 통해 익숙하고 현대적인 인터페이스를 제공합니다.
- **엄격한 동기/비동기 분리**: `oauth_codex.Client`(동기 전용)와 `oauth_codex.AsyncClient`(비동기 전용)가 완전히 분리되어 있습니다.
- **OAuth PKCE 전용 인증**: API 키를 일절 사용하지 않으며, 보안성이 높은 OAuth PKCE 방식만을 지원합니다.
- **자동 도구 실행(Tool Calling)**: 함수 호출 루프를 내장하여 다중 라운드 도구 실행을 자동으로 처리합니다.
- **구조화된 출력**: Pydantic 모델 및 JSON Schema를 통한 응답 검증을 기본 지원합니다.
- **하위 호환성 유지**: 기존의 `.generate()` 및 `.stream()` 메서드를 계속 지원합니다.

## 설치

```bash
pip install oauth-codex
```

## 빠른 시작

### 동기 방식 (`Client`)

```python
from oauth_codex import Client

client = Client(authenticate_on_init=True)

# 현대적인 OpenAI 스타일 API
completion = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "안녕하세요!"}]
)
print(completion.choices[0].message.content)

# 레거시 generate 메서드 (하위 호환)
text = client.generate([{"role": "user", "content": "간단히 자기소개 해줘"}])
print(text)
```

### 비동기 방식 (`AsyncClient`)

```python
import asyncio
from oauth_codex import AsyncClient

async def main():
    client = AsyncClient()
    await client.authenticate()

    # 현대적인 OpenAI 스타일 API
    completion = await client.chat.completions.create(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "비동기로 안녕!"}]
    )
    print(completion.choices[0].message.content)

    # 레거시 generate 메서드 (하위 호환)
    text = await client.generate([{"role": "user", "content": "비동기 방식의 장점은?"}])
    print(text)

asyncio.run(main())
```

> **중요**: `Client`와 `AsyncClient`는 완전히 분리된 클래스입니다. `Client`는 동기 컨텍스트 전용이며, `AsyncClient`는 비동기 컨텍스트(`async def`) 전용입니다. 혼용하지 마십시오.

## 인증 (Authentication)

이 SDK는 **OAuth PKCE 인증만을 독점적으로 사용합니다.** API 키는 지원하지 않습니다.

`client.authenticate()`를 명시적으로 호출하거나, `Client(authenticate_on_init=True)`로 초기화 시 즉시 인증을 수행할 수 있습니다.

```python
# 초기화 시 즉시 인증 (동기)
client = Client(authenticate_on_init=True)

# 명시적 인증 (비동기)
async def main():
    client = AsyncClient()
    await client.authenticate()
```

인증 흐름:
1. 로컬 토큰 저장소에서 유효한 토큰을 조회합니다.
2. 토큰이 없거나 만료된 경우, 인증 URL을 출력하고 브라우저 로그인을 유도합니다.
3. 브라우저 로그인 완료 후, 터미널에 리다이렉트된 `localhost` URL을 붙여넣어 인증을 완료합니다.

API 호출 중 토큰이 만료되면 자동으로 갱신됩니다.

## 현대적 API 안내

### Chat Completions

`chat.completions.create`는 OpenAI 명세를 따릅니다.

```python
response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[
        {"role": "system", "content": "당신은 유능한 코드 리뷰어입니다."},
        {"role": "user", "content": "이 Python 함수의 문제점을 알려줘."}
    ],
    temperature=0.7,
    max_tokens=1024
)
print(response.choices[0].message.content)
```

### Responses 리소스

Codex 백엔드의 핵심 리소스인 `responses`에 직접 접근하여 더 세밀한 제어가 가능합니다.

```python
response = client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "다음 코드를 분석해줘: ..."}]
)
```

`AsyncClient`에서도 동일한 인터페이스를 사용합니다:

```python
response = await client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "비동기 분석 요청"}]
)
```

## 하위 호환성 메서드

기존 v2 사용자를 위해 `.generate()` 및 `.stream()` 메서드를 계속 제공합니다. 이 메서드들은 자동 도구 실행(Tool Calling) 루프를 내장하고 있어, 다단계 함수 호출이 필요한 워크플로우에 편리합니다.

### generate / agenerate

```python
# 도구 자동 실행 포함
def get_weather(location: str) -> str:
    return f"{location}의 날씨는 맑음입니다."

text = client.generate(
    messages=[{"role": "user", "content": "서울의 날씨는?"}],
    tools=[get_weather]
)
print(text)

# 비동기
text = await client.generate(
    messages=[{"role": "user", "content": "서울의 날씨는?"}],
    tools=[get_weather]
)
```

### stream / astream

```python
# 동기 스트리밍
for delta in client.stream(messages=[{"role": "user", "content": "긴 이야기를 들려줘"}]):
    print(delta, end="", flush=True)

# 비동기 스트리밍
async for delta in client.astream(messages=[{"role": "user", "content": "긴 이야기를 들려줘"}]):
    print(delta, end="", flush=True)
```

## 구조화된 출력 (Structured Output)

`generate` 메서드에 Pydantic 모델 또는 JSON Schema를 전달하면 검증된 구조체를 반환합니다.

```python
from pydantic import BaseModel

class UserInfo(BaseModel):
    name: str
    age: int

user = client.generate(
    messages=[{"role": "user", "content": "제 이름은 김철수이고 나이는 30살입니다."}],
    output_schema=UserInfo
)
print(user["name"])  # 김철수
print(user["age"])   # 30
```

## `Client` vs `AsyncClient` — 핵심 차이점

| 항목 | `Client` | `AsyncClient` |
|---|---|---|
| 사용 컨텍스트 | 일반 함수(`def`) | 비동기 함수(`async def`) |
| HTTP 드라이버 | `httpx` (동기) | `httpx` (비동기) |
| `generate` 반환 | `str` / `dict` | `Awaitable[str \| dict]` |
| `stream` 반환 | `Iterator[str]` | `AsyncIterator[str]` |
| 인증 초기화 | `Client(authenticate_on_init=True)` | `await client.authenticate()` |

## 문서

- 영문 문서: [`docs/en/index.md`](docs/en/index.md)
- 한국어 문서: [`docs/ko/index.md`](docs/ko/index.md)

## 개발 및 테스트

```bash
# 테스트 실행
pytest -q
```

## 변경 이력

최신 변경 사항은 [CHANGELOG.md](CHANGELOG.md)에서 확인할 수 있습니다.
