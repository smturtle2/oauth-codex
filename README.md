# oauth-codex

OAuth PKCE 기반 Codex SDK.

`oauth-codex 1.0`은 OpenAI Python `2.17.0` 스타일의 패키지 구조를 따르되, 인증만 OAuth 방식으로 동작합니다.

## 1.0 Highlights

- OpenAI 스타일 구조 도입
  - `oauth_codex._client`, `_base_client`, `_resource`, `_types`, `_models`, `_exceptions`, `_module_client`
  - `oauth_codex.resources.*`, `oauth_codex.types.*`
- 공개 클라이언트
  - `OAuthCodexClient`
  - `AsyncOAuthCodexClient`
- 모듈 레벨 lazy client 지원
  - `oauth_codex.responses.create(...)`
  - `oauth_codex.files.create(...)`
  - `oauth_codex.vector_stores.create(...)`
- 지원 리소스
  - `responses` (+ `input_tokens`)
  - `files`
  - `vector_stores` (+ `files`, `file_batches`)
  - `models` (`capabilities` 포함)
- OpenAI 2.17 리소스 트리 전체 골격 노출
  - 미지원 호출은 `NotSupportedError(code="not_supported")`
- `CodexOAuthLLM` legacy alias 제거 (breaking)

## Install

```bash
pip install oauth-codex
```

개발 환경:

```bash
python3 -m pip install -e ".[dev]"
```

## Quick Start (Client)

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()

resp = client.responses.create(
    model="gpt-5.3-codex",
    input="Return JSON with keys: ok, source",
)

print(resp.id)
print(resp.output_text)
```

## Quick Start (Module-level)

```python
import oauth_codex

resp = oauth_codex.responses.create(
    model="gpt-5.3-codex",
    input="hello",
)

print(resp.output_text)
```

## OAuth Module-level Settings

- `oauth_client_id`
- `oauth_scope`
- `oauth_audience`
- `oauth_redirect_uri`
- `oauth_discovery_url`
- `oauth_authorization_endpoint`
- `oauth_token_endpoint`
- `oauth_originator`
- `base_url`
- `timeout`
- `max_retries`
- `default_headers`
- `default_query`
- `http_client`

## Codex Local Compatibility

Codex profile(`https://chatgpt.com/backend-api/codex`)에서 backend 미지원 기능은 SDK 내부 로컬 저장소로 보완됩니다.

- `files.*`
- `vector_stores.*`
- `previous_response_id` continuity

저장 경로 우선순위:

1. `compat_storage_dir` 인자
2. `CODEX_COMPAT_STORAGE_DIR`
3. `~/.oauth_codex/compat`

## Development

```bash
pytest -q
```

## Examples

- `examples/login_smoke_test.py`
- `examples/request_options_smoke_test.py`
- `examples/module_level_smoke_test.py`
- `examples/async_smoke_test.py`
