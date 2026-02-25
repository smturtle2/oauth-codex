# Migration: OpenAI SDK → oauth-codex

`oauth-codex` mirrors the OpenAI Python SDK architecture while targeting the Codex backend via OAuth PKCE — no static API keys required.

---

## Modern SDK Architecture

| Concept | OpenAI SDK | oauth-codex |
|---|---|---|
| Sync client | `openai.OpenAI()` | `oauth_codex.Client()` |
| Async client | `openai.AsyncOpenAI()` | `oauth_codex.AsyncClient()` |
| Chat completions | `client.chat.completions.create(...)` | `client.chat.completions.create(...)` ✓ identical |
| Authentication | `api_key=` | OAuth PKCE (interactive, token-refreshed automatically) |

Both `Client` and `AsyncClient` are **first-class, fully supported** exports:

```python
from oauth_codex import Client       # sync
from oauth_codex import AsyncClient  # async (NOT removed — fully supported)
```

---

## Authentication

Unlike the OpenAI SDK, there is **no API key**. The SDK uses OAuth PKCE:

1. On first run, an authorization URL is printed.
2. Sign in via the browser and paste the localhost callback URL back into the terminal.
3. Tokens are stored locally and refreshed automatically on subsequent calls.

```python
# Authenticate eagerly at construction
client = Client(authenticate_on_init=True)

# Or lazily on first use (default)
client = Client()
client.authenticate()  # trigger interactive login if no stored token
```

---

## Migration Steps

### 1. Update imports

```python
# Before (OpenAI)
from openai import OpenAI, AsyncOpenAI

# After (oauth-codex)
from oauth_codex import Client, AsyncClient
```

### 2. Update client initialization

```python
# Before
client = OpenAI(api_key="sk-...")

# After — no API key, uses OAuth PKCE
client = Client(authenticate_on_init=True)
```

### 3. Method calls — identical interface

`client.chat.completions.create(...)` works exactly as in the OpenAI SDK:

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

## Full Examples

### Sync Client (`oauth_codex.Client`)

```python
from oauth_codex import Client

client = Client(authenticate_on_init=True)

response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

### Async Client (`oauth_codex.AsyncClient`)

```python
import asyncio
from oauth_codex import AsyncClient

async def main():
    client = AsyncClient()
    await client.authenticate()  # interactive login if no stored token

    response = await client.chat.completions.create(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "Hello async!"}],
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

---

## Codex-Specific Extras

Beyond the OpenAI-compatible surface, `oauth-codex` adds higher-level helpers:

### Automatic tool execution (`generate` / `stream`)

The `generate` method handles multi-round function calling automatically:

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

### Streaming

```python
# Sync streaming
for chunk in client.stream([{"role": "user", "content": "Tell me a story"}]):
    print(chunk, end="", flush=True)

# Async streaming
async for chunk in async_client.stream([{"role": "user", "content": "Tell me a story"}]):
    print(chunk, end="", flush=True)
```

### Structured output

```python
from pydantic import BaseModel

class UserInfo(BaseModel):
    name: str
    age: int

result = client.generate(
    [{"role": "user", "content": "My name is Alice and I am 28."}],
    output_schema=UserInfo,
)
print(result)  # {"name": "Alice", "age": 28}
```

---

## Summary of API Surface

### `oauth_codex.Client` (sync)

| Method | Description |
|---|---|
| `client.chat.completions.create(...)` | OpenAI-compatible chat completion |
| `client.responses.create(...)` | Lower-level Codex responses API |
| `client.generate(messages, ...)` | Generate with automatic tool rounds |
| `client.stream(messages, ...)` | Sync streaming iterator |
| `client.agenerate(messages, ...)` | Async generation (available on sync client) |
| `client.astream(messages, ...)` | Async streaming (available on sync client) |
| `client.authenticate()` | Trigger interactive OAuth login |

### `oauth_codex.AsyncClient` (async)

| Method | Description |
|---|---|
| `await client.chat.completions.create(...)` | OpenAI-compatible async chat completion |
| `await client.responses.create(...)` | Lower-level Codex responses API |
| `await client.generate(messages, ...)` | Generate with automatic tool rounds |
| `async for chunk in client.stream(...)` | Async streaming iterator |
| `await client.authenticate()` | Trigger interactive OAuth login |
