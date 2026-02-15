[English](README.md) | [한국어](README.ko.md)

# oauth-codex

OAuth PKCE-based Python SDK for the Codex backend, with an OpenAI-style client surface and OAuth-native authentication.

[![PyPI version](https://img.shields.io/pypi/v/oauth-codex.svg)](https://pypi.org/project/oauth-codex/)
[![Python](https://img.shields.io/pypi/pyversions/oauth-codex.svg)](https://pypi.org/project/oauth-codex/)
[![Publish to PyPI](https://github.com/dongju/project/codex-api/actions/workflows/publish-pypi.yml/badge.svg)](.github/workflows/publish-pypi.yml)

## Table of Contents

- [Why oauth-codex](#why-oauth-codex)
- [Feature Highlights](#feature-highlights)
- [Install](#install)
- [Quick Start](#quick-start)
- [Request Options at a Glance](#request-options-at-a-glance)
- [Supported Runtime Matrix](#supported-runtime-matrix)
- [Local Compatibility Behavior (Codex Profile)](#local-compatibility-behavior-codex-profile)
- [Errors and Validation Modes](#errors-and-validation-modes)
- [Documentation Index](#documentation-index)
- [Examples](#examples)
- [Development](#development)
- [Changelog](#changelog)

## Why oauth-codex

- OpenAI-style API shape for migration-friendly code.
- OAuth PKCE authentication flow for user-account workflows.
- Codex-profile local compatibility fallback for `files`, `vector_stores`, and response continuity.
- Strictly typed response objects (`pydantic`) and structured SDK errors.

## Feature Highlights

| Area | What you get |
|---|---|
| Client surfaces | `OAuthCodexClient`, `AsyncOAuthCodexClient`, and module-level lazy proxies (`oauth_codex.responses.create(...)`) |
| Runtime-supported resources | `responses`, `responses.input_tokens`, `files`, `vector_stores` (+ `files`, `file_batches`), `models` |
| Request controls | `extra_headers`, `extra_query`, `extra_body`, `validation_mode`, retry and timeout settings |
| Streaming | SSE event mapping with normalized events (`text_delta`, `tool_call_*`, `usage`, `response_completed`) |
| Compatibility behavior | Codex profile local persistence for unsupported backend features |
| Structure parity | OpenAI 2.17-style resource tree exposed; unsupported calls fail with `NotSupportedError(code="not_supported")` |

## Install

```bash
pip install oauth-codex
```

Development install:

```bash
python3 -m pip install -e ".[dev]"
```

## Quick Start

### Sync Client

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()

response = client.responses.create(
    model="gpt-5.3-codex",
    input="Return JSON with keys: ok, source",
    response_format={"type": "json_object"},
)

print(response.id)
print(response.output_text)
```

### Async Client

```python
import asyncio
from oauth_codex import AsyncOAuthCodexClient


async def main() -> None:
    client = AsyncOAuthCodexClient()
    response = await client.responses.create(
        model="gpt-5.3-codex",
        input="Summarize OAuth PKCE in 2 bullets",
    )
    print(response.output_text)


asyncio.run(main())
```

### Module-level Lazy Client

```python
import oauth_codex

oauth_codex.timeout = 90.0
oauth_codex.max_retries = 3

response = oauth_codex.responses.create(
    model="gpt-5.3-codex",
    input="hello",
)

print(response.output_text)
```

## Request Options at a Glance

Primary request options are currently wired through `responses.create(...)` / `responses.stream(...)`:

- `extra_headers`: merged into request headers, except protected headers.
- `extra_query`: merged into request query parameters.
- `extra_body`: merged last into JSON body (can override earlier fields).
- `validation_mode`: `"warn"` (default), `"error"`, `"ignore"`.
- `store`: on Codex profile, behavior depends on `store_behavior` (`auto_disable`, `error`, `passthrough`).

Detailed rules and edge cases: [`docs/en/methods/request_options.md`](docs/en/methods/request_options.md)

## Supported Runtime Matrix

| Resource | Status | Notes |
|---|---|---|
| `responses` | Supported | `create`, `stream` |
| `responses.input_tokens` | Supported | `count` |
| `files` | Supported | Create/retrieve/list/delete/content |
| `vector_stores` | Supported | Root CRUD + search |
| `vector_stores.files` | Supported | Attach/list/delete/content/upload helpers |
| `vector_stores.file_batches` | Supported | Create/retrieve/cancel/poll/list_files/upload_and_poll |
| `models` | Partially supported | `capabilities`, `retrieve`, `list`; `delete` unsupported |
| Other OpenAI-style resources | Structure only | Raise `NotSupportedError(code="not_supported")` |

Full matrix: [`docs/en/unsupported-matrix.md`](docs/en/unsupported-matrix.md)

## Local Compatibility Behavior (Codex Profile)

When `base_url` targets the Codex profile (`https://chatgpt.com/backend-api/codex`), backend gaps are handled locally:

- `files.*` operations use local compatibility storage.
- `vector_stores.*` operations are locally emulated.
- `previous_response_id` continuity is restored using local response continuity records.

Compatibility storage path precedence:

1. `compat_storage_dir` constructor argument
2. `CODEX_COMPAT_STORAGE_DIR` environment variable
3. `~/.oauth_codex/compat`

## Errors and Validation Modes

Common SDK errors:

- `AuthRequiredError`
- `SDKRequestError`
- `NotSupportedError`
- `ParameterValidationError`
- `ContinuityError`
- `TokenStoreReadError` / `TokenStoreWriteError` / `TokenStoreDeleteError`

Validation behavior:

- `validation_mode="warn"` (default): keep request running and emit warnings.
- `validation_mode="error"`: raise `ParameterValidationError` on invalid/unsupported params.
- `validation_mode="ignore"`: skip warnings/errors for validation-only checks.

## Documentation Index

- English docs: [`docs/en/index.md`](docs/en/index.md)
- Korean docs: [`docs/ko/index.md`](docs/ko/index.md)

Method references:

- [`docs/en/methods/responses.md`](docs/en/methods/responses.md)
- [`docs/en/methods/files.md`](docs/en/methods/files.md)
- [`docs/en/methods/vector_stores.md`](docs/en/methods/vector_stores.md)
- [`docs/en/methods/models.md`](docs/en/methods/models.md)
- [`docs/en/methods/module_level.md`](docs/en/methods/module_level.md)
- [`docs/en/methods/request_options.md`](docs/en/methods/request_options.md)

Supplemental docs:

- [`docs/migration_openai_to_oauth_codex.md`](docs/migration_openai_to_oauth_codex.md)
- [`docs/stream_event_schema_v1.md`](docs/stream_event_schema_v1.md)

## Examples

- `examples/login_smoke_test.py`
- `examples/request_options_smoke_test.py`
- `examples/module_level_smoke_test.py`
- `examples/async_smoke_test.py`

## Development

```bash
pytest -q
```

## Changelog

- [`CHANGELOG.md`](CHANGELOG.md)
