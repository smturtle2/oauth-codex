[English](module_level.md) | [한국어](../../ko/methods/module_level.md)

# Module-level Usage

This page documents module-level lazy client usage (`import oauth_codex`).

## Method Summary

Module-level proxies mirror sync client resources:

- `oauth_codex.responses.*`
- `oauth_codex.files.*`
- `oauth_codex.vector_stores.*`
- `oauth_codex.models.*`
- Additional OpenAI-style resources are exposed for structure parity and may be unsupported at runtime.

## Lazy Client Behavior

### What happens

- The first module-level resource call creates a singleton lazy client.
- Global module variables are read at that creation moment.
- Later changes to module globals do not affect an already-created lazy client instance.

### Ordering caveat (important)

Set module-level options **before** the first call such as `oauth_codex.responses.create(...)`.

## Module-level Configuration Surface

### Configuration fields

| Variable | Type | Default | Meaning |
|---|---|---|---|
| `oauth_client_id` | `str | None` | `None` | OAuth client id override |
| `oauth_scope` | `str | None` | `None` | OAuth scope override |
| `oauth_audience` | `str | None` | `None` | OAuth audience override |
| `oauth_redirect_uri` | `str | None` | `None` | OAuth redirect URI override |
| `oauth_discovery_url` | `str | None` | `None` | OAuth discovery endpoint override |
| `oauth_authorization_endpoint` | `str | None` | `None` | OAuth authorization endpoint override |
| `oauth_token_endpoint` | `str | None` | `None` | OAuth token endpoint override |
| `oauth_originator` | `str | None` | `None` | OAuth originator override |
| `base_url` | `str | None` | `None` | Base URL (`None` -> Codex profile default) |
| `timeout` | `float` | `60.0` | HTTP timeout |
| `max_retries` | `int` | `2` | Retry count |
| `default_headers` | `dict[str, str] | None` | `None` | Client-level default headers input |
| `default_query` | `dict[str, object] | None` | `None` | Client-level default query input |
| `http_client` | `Any | None` | `None` | Custom HTTP client input |

## Sync / Async / Module-level Signatures

### Module-level examples

```python
import oauth_codex

# configure first
oauth_codex.base_url = "https://chatgpt.com/backend-api/codex"
oauth_codex.timeout = 90.0
oauth_codex.max_retries = 3

# then call
resp = oauth_codex.responses.create(model="gpt-5.3-codex", input="hello")
print(resp.output_text)
```

### Equivalent sync client style

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient(base_url="https://chatgpt.com/backend-api/codex", timeout=90.0, max_retries=3)
resp = client.responses.create(model="gpt-5.3-codex", input="hello")
```

## Return Shape

- Return types are identical to sync client resource methods.
- Module-level proxies map directly to the same runtime resource implementations.

## Error Cases

| Exception | Trigger |
|---|---|
| `AuthRequiredError` | Authentication missing/expired and login-refresh cannot complete |
| `SDKRequestError` | Provider/network/local-compat request failures |
| `NotSupportedError` | Unsupported resource call |
| `ParameterValidationError` | Invalid request parameters under strict validation |

## Behavior Notes

- Module-level proxy uses sync client behavior.
- Unsupported resources still exist as attributes for API surface parity.
- If you need async behavior, use `AsyncOAuthCodexClient` directly.

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

- Configure globals before first call; otherwise your changes may not apply.
- For deterministic per-test setup, instantiate `OAuthCodexClient` directly instead of relying on global module state.
