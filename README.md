[English](README.md) | [한국어](README.ko.md)

# oauth-codex

OAuth PKCE-based Python SDK for the Codex backend.

## Key Changes (v2)

- The public API now exposes a single `Client`.
- The default workflow is centered around `generate`.
- Async support is provided on the same class via `agenerate` and `astream`.
- Supports text generation, image input analysis, automatic function-calling execution, and `reasoning_effort`.

## Installation

```bash
pip install oauth-codex
```

## Quick Start

```python
from oauth_codex import Client

client = Client()
text = client.generate("hello")
print(text)
```

## Image Input

```python
text = client.generate(
    "Describe this image",
    images=["https://example.com/cat.png", "./local-photo.jpg"],
)
print(text)
```

## Function Calling (Automatic Loop)

```python
def add(a: int, b: int) -> dict:
    return {"sum": a + b}

text = client.generate(
    "Calculate 2+3",
    tools=[add],
)
print(text)
```

If a tool raises an exception, the SDK forwards it to the model as `{\"error\": ...}` and continues the loop.

## Async

```python
import asyncio
from oauth_codex import Client


async def main() -> None:
    client = Client()
    text = await client.agenerate("hello async")
    print(text)


asyncio.run(main())
```

## Breaking Changes in v2.0

- Removed: `AsyncOAuthCodexClient`, module-level proxies, `client.responses/files/vector_stores/models`, `oauth_codex.compat`
- Single entry points: `Client.generate/stream/agenerate/astream`

## Documentation

- English index: [`docs/en/index.md`](docs/en/index.md)
- Korean index: [`docs/ko/index.md`](docs/ko/index.md)

## Development

```bash
pytest -q
```

## Changelog

- [`CHANGELOG.md`](CHANGELOG.md)
