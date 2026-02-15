[English](README.md) | [한국어](README.ko.md)

# oauth-codex

Codex 백엔드를 위한 OAuth PKCE 기반 Python SDK입니다.

## 핵심 특징

- OpenAI 스타일 sync/async 클라이언트: `OAuthCodexClient`, `AsyncOAuthCodexClient`
- 모듈 레벨 lazy proxy: `oauth_codex.responses`, `oauth_codex.files`, `oauth_codex.vector_stores`, `oauth_codex.models`
- 구조 호환용 stub 없이, 런타임 지원 리소스만 노출
- `pydantic` 기반 타입 + 구조화된 SDK 에러

## 설치

```bash
pip install oauth-codex
```

## 지원 리소스

- `responses` (`create`, `stream`, `input_tokens.count`)
- `files`
- `vector_stores` (`files`, `file_batches` 포함)
- `models` (`capabilities`, `retrieve`, `list`)

## 빠른 시작

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()
resp = client.responses.create(model="gpt-5.3-codex", input="hello")
print(resp.output_text)
```

## Core 타입

`legacy_types`는 제거되었습니다.
아래 경로를 사용하세요.

- `oauth_codex.core_types`

예시:

```python
from oauth_codex.core_types import OAuthTokens
```

## 문서

- 영문 인덱스: [`docs/en/index.md`](docs/en/index.md)
- 국문 인덱스: [`docs/ko/index.md`](docs/ko/index.md)

## 개발

```bash
pytest -q
```

## 변경 이력

- [`CHANGELOG.md`](CHANGELOG.md)
