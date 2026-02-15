[English](../../en/methods/module_level.md) | [한국어](module_level.md)

# 모듈 레벨 사용법

모듈 레벨 lazy proxy는 sync client 리소스를 그대로 노출합니다.

## 사용 가능한 모듈 레벨 리소스

- `oauth_codex.responses.*`
- `oauth_codex.files.*`
- `oauth_codex.vector_stores.*`
- `oauth_codex.models.*`

## Lazy client 동작

- 첫 호출에서 singleton client가 생성됩니다.
- 전역 옵션은 생성 시점 값이 사용됩니다.
- 첫 호출 전에 옵션을 설정하세요.

## 주요 설정 필드

- `oauth_client_id`, `oauth_scope`, `oauth_audience`
- `oauth_redirect_uri`, `oauth_discovery_url`
- `oauth_authorization_endpoint`, `oauth_token_endpoint`, `oauth_originator`
- `base_url`, `timeout`, `max_retries`
- `default_headers`, `default_query`, `http_client`

## 예시

```python
import oauth_codex

oauth_codex.timeout = 90.0
resp = oauth_codex.responses.create(model="gpt-5.3-codex", input="hello")
print(resp.output_text)
```
