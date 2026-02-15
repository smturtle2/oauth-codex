[English](client.md) | [한국어](../../ko/methods/client.md)

# Client Methods

`oauth-codex` v2 exposes a single public class: `Client`.

## Constructor

```python
from oauth_codex import Client

client = Client()
```

## Core Methods

- `generate(...)`: returns final text output.
- `stream(...)`: yields text deltas (sync iterator).
- `agenerate(...)`: async text generation.
- `astream(...)`: async text streaming.

## Common Options

- `prompt`: text prompt
- `images`: image input (URL string or local file path)
- `tools`: list of Python callables (automatic function-calling loop)
- `model`: defaults to `gpt-5.3-codex`
- `reasoning_effort`: `low | medium | high` (default `medium`)
- `temperature`, `top_p`, `max_output_tokens`

## Text Generation

```python
text = client.generate("hello")
print(text)
```

## Image Input Analysis

```python
text = client.generate(
    "Describe this image",
    images=["https://example.com/photo.png", "./photo.jpg"],
)
print(text)
```

Local file paths are converted to data URLs internally.

## Function Calling (Automatic)

```python
def get_weather(city: str) -> dict:
    return {"city": city, "weather": "sunny"}

text = client.generate("What's weather in Seoul?", tools=[get_weather])
```

Single-parameter Pydantic tool inputs are also supported.

```python
from pydantic import BaseModel


class ToolInput(BaseModel):
    query: str


def tool(input: ToolInput) -> str:
    return f"Tool received query: {input.query}"


text = client.generate("Use the tool", tools=[tool])
```

Tool exceptions are forwarded to the model as `{ "error": "..." }` and the loop continues.

## Streaming

```python
for delta in client.stream("hello"):
    print(delta, end="")
```

## Async

```python
text = await client.agenerate("hello")

async for delta in client.astream("hello"):
    print(delta, end="")
```

## See also

- [Removed APIs Guide](removed_apis.md)
- [Migration Guide](../../migration_openai_to_oauth_codex.md)
