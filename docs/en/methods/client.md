[English](client.md) | [한국어](../../ko/methods/client.md)

# Client Methods

`oauth-codex` v2 exposes a single public class: `Client`.

## Constructor

```python
from oauth_codex import Client

client = Client()
```

## Core Methods

- `generate(...)`: returns final text output, or a JSON object when `output_schema` is set.
- `stream(...)`: yields text deltas (sync iterator).
- `agenerate(...)`: async text generation, or a JSON object when `output_schema` is set.
- `astream(...)`: async text streaming.

## Common Options

- `prompt`: text prompt
- `images`: image input (URL string or local file path)
- `tools`: list of Python callables (automatic function-calling loop)
- `model`: defaults to `gpt-5.3-codex`
- `reasoning_effort`: `low | medium | high` (default `medium`)
- `temperature`, `top_p`, `max_output_tokens`
- `output_schema`: Pydantic model type or JSON schema dict for structured output
- `strict_output`: strict mode for tool and output schemas. Defaults to `True` when `output_schema` is set.

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

## Structured Output

```python
from pydantic import BaseModel


class Summary(BaseModel):
    title: str
    score: int


out = client.generate("Return JSON", output_schema=Summary)
print(out)  # {"title": "...", "score": 1}
```

Raw JSON schema dict is also supported:

```python
out = client.generate(
    "Return JSON",
    output_schema={
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
    },
)
```

`stream` / `astream` keep returning text deltas only. Structured JSON parsing is applied only in `generate` / `agenerate`.

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
