[English](README.md) | [한국어](README.ko.md)

# oauth-codex

Codex 백엔드를 위한 OAuth PKCE 기반 Python SDK입니다.

## 주요 특징

- **OpenAI 스타일 API**: `client.chat.completions.create` 및 `client.responses.create`를 통해 익숙하고 현대적인 인터페이스를 제공합니다.
- **엄격한 동기/비동기 분리**: `oauth_codex.Client`(동기 전용)와 `oauth_codex.AsyncClient`(비동기 전용)가 완전히 분리되어 있습니다.
- **OAuth PKCE 전용 인증**: API 키를 일절 사용하지 않으며, 보안성이 높은 OAuth PKCE 방식만을 지원합니다.

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

## `Client` vs `AsyncClient` — 핵심 차이점

| 항목 | `Client` | `AsyncClient` |
|---|---|---|
| 사용 컨텍스트 | 일반 함수(`def`) | 비동기 함수(`async def`) |
| HTTP 드라이버 | `httpx` (동기) | `httpx` (비동기) |
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
