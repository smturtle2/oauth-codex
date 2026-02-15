[English](README.md) | [한국어](README.ko.md)

# oauth-codex

OAuth PKCE-based Python SDK for the Codex backend.

## Highlights

- OpenAI-style sync/async clients: `OAuthCodexClient`, `AsyncOAuthCodexClient`
- Module-level lazy proxies: `oauth_codex.responses`, `oauth_codex.files`, `oauth_codex.vector_stores`, `oauth_codex.models`
- Runtime-supported resources only (no structure-only stubs)
- Typed response objects (`pydantic`) and structured SDK errors

## Install

```bash
pip install oauth-codex
```

## Supported Runtime Surface

- `responses` (`create`, `stream`, `input_tokens.count`)
- `files`
- `vector_stores` (`files`, `file_batches` 포함)
- `models` (`capabilities`, `retrieve`, `list`)

## Quick Start

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()
resp = client.responses.create(model="gpt-5.3-codex", input="hello")
print(resp.output_text)
```

## Core Types

Legacy type module is removed.
Use:

- `oauth_codex.core_types`

Example:

```python
from oauth_codex.core_types import OAuthTokens
```

## Documentation

- English index: [`docs/en/index.md`](docs/en/index.md)
- Korean index: [`docs/ko/index.md`](docs/ko/index.md)

## Development

```bash
pytest -q
```

## Changelog

- [`CHANGELOG.md`](CHANGELOG.md)
