[English](module_level.md) | [한국어](../../ko/methods/module_level.md)

# Module-level Usage

Module-level lazy proxies mirror sync client resources.

## Available module-level resources

- `oauth_codex.responses.*`
- `oauth_codex.files.*`
- `oauth_codex.vector_stores.*`
- `oauth_codex.models.*`

## Lazy client behavior

- First module-level call creates a singleton client.
- Global module options are read at creation time.
- Set options before first call.

## Configuration fields

- `oauth_client_id`, `oauth_scope`, `oauth_audience`
- `oauth_redirect_uri`, `oauth_discovery_url`
- `oauth_authorization_endpoint`, `oauth_token_endpoint`, `oauth_originator`
- `base_url`, `timeout`, `max_retries`
- `default_headers`, `default_query`, `http_client`

## Example

```python
import oauth_codex

oauth_codex.timeout = 90.0
resp = oauth_codex.responses.create(model="gpt-5.3-codex", input="hello")
print(resp.output_text)
```
