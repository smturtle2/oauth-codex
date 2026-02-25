[English](client.md) | [한국어](../../ko/methods/client.md)

# Client Methods

`oauth-codex` provides two symmetric client classes:

| Class | Import | Use when |
|---|---|---|
| `Client` | `from oauth_codex import Client` | Synchronous / blocking code |
| `AsyncClient` | `from oauth_codex import AsyncClient` | `async`/`await` code, event loops |

Both classes expose the **same** `chat.completions.create`, `generate`, `stream`, and `responses` interfaces. `AsyncClient` methods are async-native (`await` / `async for`), while `Client` methods are synchronous — plus `agenerate`/`astream` bridge methods for calling async from the sync client.

---

## Construction

### Sync Client

```python
from oauth_codex import Client

client = Client()
```

### Async Client

```python
from oauth_codex import AsyncClient

client = AsyncClient()
```

Authenticate immediately at construction time (sync only):

```python
client = Client(authenticate_on_init=True)
```

---

## Authentication

Tokens are stored locally and refreshed automatically. On first use (or when the stored token is missing/expired) interactive OAuth login is triggered.

```python
# Sync: block until login is complete
client.authenticate()

# Async: non-blocking
await client.authenticate()
```

`Client` constructor option:

```python
client = Client(authenticate_on_init=True)  # login immediately in __init__
```

---

## Chat Completions

The primary interface — identical to the OpenAI Python SDK.

### Sync

```python
response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

### Async

```python
response = await client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "Hello async!"}],
)
print(response.choices[0].message.content)
```

### Full example with system prompt

```python
response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a Python function to sort a list."},
    ],
    temperature=0.7,
    max_tokens=500,
)
print(response.choices[0].message.content)
```

---

## `generate` — Text Generation with Automatic Tool Execution

`generate` returns the final text (or a structured dict when `output_schema` is set). It handles multi-round function calling automatically.

### Sync (`Client`)

```python
text = client.generate([{"role": "user", "content": "hello"}])
print(text)
```

### Async (`AsyncClient`)

```python
text = await client.generate([{"role": "user", "content": "hello"}])
print(text)
```

> **Note:** The sync `Client` also exposes `agenerate` as a convenience async alias:
> `text = await sync_client.agenerate([...])`

---

## `stream` — Streaming Text Deltas

### Sync streaming (`Client`)

```python
for chunk in client.stream([{"role": "user", "content": "Tell me a story"}]):
    print(chunk, end="", flush=True)
```

### Async streaming (`AsyncClient`)

```python
async for chunk in client.stream([{"role": "user", "content": "Tell me a story"}]):
    print(chunk, end="", flush=True)
```

> The sync `Client` also exposes `astream` as a convenience async alias.

---

## Image Input Analysis

Pass multimodal content via `client.chat.completions.create`:

```python
response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Describe this image"},
                {"type": "input_image", "image_url": "https://example.com/photo.png"},
            ],
        }
    ],
)
```

---

## Function Calling (Automatic)

Pass Python callables directly. The SDK serializes their signatures, sends tool definitions to the model, and executes the returned calls automatically.

```python
def get_weather(city: str) -> dict:
    return {"city": city, "weather": "sunny"}

# Sync
text = client.generate(
    [{"role": "user", "content": "What's the weather in Seoul?"}],
    tools=[get_weather],
)

# Async
text = await async_client.generate(
    [{"role": "user", "content": "What's the weather in Seoul?"}],
    tools=[get_weather],
)
```

Async tools are supported in `AsyncClient.generate` (and `Client.agenerate`):

```python
async def fetch_data(url: str) -> dict:
    ...  # async I/O

text = await async_client.generate([...], tools=[fetch_data])
```

---

## Structured Output

Pass a Pydantic model or a JSON Schema dict. The response is validated and returned as a dict.

```python
from pydantic import BaseModel

class Summary(BaseModel):
    title: str
    score: int

out = client.generate(
    [{"role": "user", "content": "Return JSON"}],
    output_schema=Summary,
)
print(out)  # {"title": "...", "score": 1}
```

---

## Responses Resource (Low-level)

For direct access to the Codex backend responses API:

```python
# Sync
response = client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "Analyze this code."}],
)

# Async
response = await client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "Analyze this code."}],
)
```

---

## API Surface at a Glance

### `oauth_codex.Client` (sync)

| Method | Returns |
|---|---|
| `client.chat.completions.create(...)` | `ChatCompletion` |
| `client.responses.create(...)` | raw response |
| `client.generate(messages, ...)` | `str \| dict` |
| `client.stream(messages, ...)` | `Iterator[str]` |
| `client.agenerate(messages, ...)` | `Awaitable[str \| dict]` |
| `client.astream(messages, ...)` | `AsyncIterator[str]` |
| `client.authenticate()` | `None` |

### `oauth_codex.AsyncClient` (async)

| Method | Returns |
|---|---|
| `await client.chat.completions.create(...)` | `ChatCompletion` |
| `await client.responses.create(...)` | raw response |
| `await client.generate(messages, ...)` | `str \| dict` |
| `async for chunk in client.stream(...)` | `AsyncIterator[str]` |
| `await client.authenticate()` | `None` |

---

## See also

- [Removed APIs Guide](removed_apis.md)
- [Migration Guide](../../migration_openai_to_oauth_codex.md)
