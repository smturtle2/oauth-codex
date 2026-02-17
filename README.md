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
text = client.generate([{"role": "user", "content": "hello"}])
print(text)
```

## Image Input

```python
text = client.generate(
    [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Describe this image"},
                {"type": "input_image", "image_url": "https://example.com/cat.png"},
                {"type": "input_image", "image_url": "data:image/jpeg;base64,..."},
            ],
        }
    ],
)
print(text)
```

## Function Calling (Automatic Loop)

```python
def add(a: int, b: int) -> dict:
    return {"sum": a + b}

text = client.generate(
    [{"role": "user", "content": "Calculate 2+3"}],
    tools=[add],
)
print(text)
```

Single-parameter Pydantic tool inputs are also supported.

```python
from pydantic import BaseModel


class ToolInput(BaseModel):
    query: str


def tool(input: ToolInput) -> str:
    return f"Tool received query: {input.query}"


text = client.generate([{"role": "user", "content": "Use the tool"}], tools=[tool])
print(text)
```

If a tool raises an exception, the SDK forwards it to the model as `{\"error\": ...}` and continues the loop.

## Structured Output (Strict JSON Schema / Pydantic)

`generate` / `agenerate` can produce validated JSON object output via `output_schema`.

```python
from pydantic import BaseModel
from oauth_codex import Client


class Summary(BaseModel):
    title: str
    score: int


client = Client()
out = client.generate(
    [{"role": "user", "content": "Return JSON with title and score"}],
    output_schema=Summary,
)
print(out)  # {"title": "...", "score": 1}
```

You can also pass a raw JSON schema object.

```python
out = client.generate(
    [{"role": "user", "content": "Return {\"ok\": true}"}],
    output_schema={
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
    },
)
print(out)  # {"ok": True}
```

When `output_schema` is set, strict mode is enabled by default unless `strict_output` is explicitly provided.
`stream` / `astream` still yield text deltas only; they do not parse final JSON objects.

## Async

```python
import asyncio
from oauth_codex import Client


async def main() -> None:
    client = Client()
    text = await client.agenerate([{"role": "user", "content": "hello async"}])
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
