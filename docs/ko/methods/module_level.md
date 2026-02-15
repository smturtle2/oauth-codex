[English](../../en/methods/module_level.md) | [한국어](module_level.md)

# 모듈 레벨 사용법

이 문서는 `import oauth_codex` 기반 모듈 레벨 lazy client 사용법을 설명합니다.

## Method Summary

모듈 레벨 proxy는 sync client 리소스를 미러링합니다.

- `oauth_codex.responses.*`
- `oauth_codex.files.*`
- `oauth_codex.vector_stores.*`
- `oauth_codex.models.*`
- 그 외 OpenAI 스타일 리소스는 구조 호환용으로 노출되며 런타임 미지원일 수 있습니다.

## Lazy Client 동작

### 동작 방식

- 모듈 레벨 첫 호출 시 singleton lazy client가 생성됩니다.
- 모듈 전역 변수는 이 생성 시점 값을 사용합니다.
- lazy client가 생성된 뒤 전역 변수 값을 바꿔도 이미 생성된 인스턴스에는 반영되지 않습니다.

### 순서 주의점 (중요)

`oauth_codex.responses.create(...)` 같은 첫 호출 전에 전역 옵션을 먼저 설정하세요.

## 모듈 레벨 설정 표면

### Configuration fields

| 변수 | 타입 | 기본값 | 의미 |
|---|---|---|---|
| `oauth_client_id` | `str | None` | `None` | OAuth client id override |
| `oauth_scope` | `str | None` | `None` | OAuth scope override |
| `oauth_audience` | `str | None` | `None` | OAuth audience override |
| `oauth_redirect_uri` | `str | None` | `None` | OAuth redirect URI override |
| `oauth_discovery_url` | `str | None` | `None` | OAuth discovery endpoint override |
| `oauth_authorization_endpoint` | `str | None` | `None` | OAuth authorization endpoint override |
| `oauth_token_endpoint` | `str | None` | `None` | OAuth token endpoint override |
| `oauth_originator` | `str | None` | `None` | OAuth originator override |
| `base_url` | `str | None` | `None` | Base URL (`None`이면 Codex profile 기본값) |
| `timeout` | `float` | `60.0` | HTTP timeout |
| `max_retries` | `int` | `2` | retry 횟수 |
| `default_headers` | `dict[str, str] | None` | `None` | client-level default headers 입력 |
| `default_query` | `dict[str, object] | None` | `None` | client-level default query 입력 |
| `http_client` | `Any | None` | `None` | custom HTTP client 입력 |

## Sync / Async / Module-level Signatures

### Module-level 예시

```python
import oauth_codex

# 먼저 설정
oauth_codex.base_url = "https://chatgpt.com/backend-api/codex"
oauth_codex.timeout = 90.0
oauth_codex.max_retries = 3

# 그 다음 호출
resp = oauth_codex.responses.create(model="gpt-5.3-codex", input="hello")
print(resp.output_text)
```

### 동등한 sync client 방식

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient(base_url="https://chatgpt.com/backend-api/codex", timeout=90.0, max_retries=3)
resp = client.responses.create(model="gpt-5.3-codex", input="hello")
```

## Return Shape

- 반환 타입은 sync client 리소스 메서드와 동일합니다.
- 모듈 레벨 proxy는 동일 런타임 리소스 구현을 직접 매핑합니다.

## Error Cases

| 예외 | 발생 조건 |
|---|---|
| `AuthRequiredError` | 인증 누락/만료 상태에서 login/refresh 실패 |
| `SDKRequestError` | provider/network/local-compat 요청 실패 |
| `NotSupportedError` | 미지원 리소스 호출 |
| `ParameterValidationError` | strict validation에서 파라미터 오류 |

## Behavior Notes

- 모듈 레벨 proxy는 sync client 동작을 따릅니다.
- 미지원 리소스도 표면 호환성을 위해 속성은 노출됩니다.
- 비동기 동작이 필요하면 `AsyncOAuthCodexClient`를 직접 사용하세요.

## Runnable Usage Snippets

### Responses + Files

```python
import io
import oauth_codex

oauth_codex.timeout = 60.0

resp = oauth_codex.responses.create(model="gpt-5.3-codex", input="hello")
print(resp.id)

f = oauth_codex.files.create(file=io.BytesIO(b"demo"), purpose="assistants")
print(f.id)
```

### Vector Stores

```python
vs = oauth_codex.vector_stores.create(name="docs", file_ids=[])
print(vs.id)
```

## Pitfalls / Troubleshooting

- 첫 호출 전에 전역 옵션을 설정하세요. 이후 변경은 반영되지 않을 수 있습니다.
- 테스트/재현성을 중요시하면 전역 상태 대신 `OAuthCodexClient` 인스턴스를 직접 생성하세요.
