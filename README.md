[English](README.md) | [한국어](README.ko.md)

# oauth-codex

OAuth PKCE-based Python SDK for the Codex backend — version 3.x.

## Key Features

- **OpenAI-style API**: Familiar `client.chat.completions.create` and `client.responses.create` interfaces.
- **Strict Sync/Async Separation**: `oauth_codex.Client` for synchronous code; `oauth_codex.AsyncClient` for async code. Never mix them.
- **OAuth PKCE Only**: Authentication is exclusively via OAuth PKCE. No API keys are supported or required.
- **Automatic Tool Execution**: Built-in function-calling loop with configurable continuation rounds.
- **Structured Output**: Native Pydantic model and JSON Schema validation for model responses.
- **Legacy Compatibility**: `.generate()` and `.stream()` methods preserved for backward compatibility.

## Installation

```bash
pip install oauth-codex
```

Requires Python 3.11+.

## Quick Start

### Synchronous

```python
from oauth_codex import Client

client = Client(authenticate_on_init=True)

completion = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "Hello, how are you?"}],
)
print(completion.choices[0].message.content)
```

### Asynchronous

```python
import asyncio
from oauth_codex import AsyncClient

async def main():
    client = AsyncClient()
    await client.authenticate()

    completion = await client.chat.completions.create(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "Hello async!"}],
    )
    print(completion.choices[0].message.content)

asyncio.run(main())
```

## Authentication

This SDK exclusively uses **OAuth PKCE**. No API keys are accepted.

Authentication is interactive the first time:

1. Call `client.authenticate()` (sync) or `await client.authenticate()` (async), or pass `authenticate_on_init=True` to `Client`.
2. The SDK checks for stored tokens. If none exist or they are expired, it prints an authorization URL.
3. Open the URL in a browser, sign in, then paste the localhost callback URL back into the terminal to complete the flow.

Tokens are persisted locally and refreshed automatically before each request.

```python
# Sync: authenticate eagerly at construction time
client = Client(authenticate_on_init=True)

# Sync: authenticate lazily before first use
client = Client()
client.authenticate()

# Async: authenticate before first use
client = AsyncClient()
await client.authenticate()
```

### Token Utilities

```python
client.is_authenticated()          # bool — tokens are present
client.is_expired(leeway_seconds=60)  # bool — token is expired or near-expiry
client.refresh_if_needed()         # bool — refreshed if needed, returns True on refresh
client.login()                     # force interactive login flow (sync)
await client.alogin()              # force interactive login flow (async, from AsyncClient or OAuthCodexClient)
```

## Modern API

### Chat Completions

`client.chat.completions.create` follows the OpenAI Chat Completions specification.

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

Async equivalent:

```python
response = await client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "Write a Python function to sort a list."}],
)
```

### Responses Resource

`client.responses.create` provides lower-level access to the Codex backend using the Responses API shape.

```python
response = client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "Analyze this code snippet."}],
)
```

Async equivalent:

```python
response = await client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "Analyze this code snippet."}],
)
```

## Sync/Async Separation

`oauth_codex.Client` and `oauth_codex.AsyncClient` are **strictly separate** classes. Do not use `Client` inside an async event loop or `AsyncClient` in synchronous code.

| Class | Import | Authentication |
|---|---|---|
| `Client` | `from oauth_codex import Client` | `client.authenticate()` |
| `AsyncClient` | `from oauth_codex import AsyncClient` | `await client.authenticate()` |

Both classes expose identical resource namespaces: `chat`, `responses`, `files`, `vector_stores`, `models`.

## Legacy API

The `.generate()` / `.stream()` methods (and their async counterparts) are preserved for backward compatibility. They provide a generate-first workflow with automatic multi-round tool execution built in.

### generate / agenerate

```python
# Sync
text = client.generate(
    messages=[{"role": "user", "content": "Summarize the Rust ownership model."}],
    model="gpt-5.3-codex",           # optional, uses default_model otherwise
    reasoning_effort="medium",        # "low" | "medium" | "high"
)
print(text)

# Async (on Client)
text = await client.agenerate(
    messages=[{"role": "user", "content": "Summarize the Rust ownership model."}],
)

# Async (on AsyncClient — method is named generate)
text = await async_client.generate(
    messages=[{"role": "user", "content": "Summarize the Rust ownership model."}],
)
```

### stream / astream

```python
# Sync
for chunk in client.stream(
    messages=[{"role": "user", "content": "Tell me a story."}],
):
    print(chunk, end="", flush=True)

# Async (on Client)
async for chunk in client.astream(
    messages=[{"role": "user", "content": "Tell me a story."}],
):
    print(chunk, end="", flush=True)

# Async (on AsyncClient — method is named stream)
async for chunk in async_client.stream(
    messages=[{"role": "user", "content": "Tell me a story."}],
):
    print(chunk, end="", flush=True)
```

### Automatic Tool Execution

Pass Python callables as `tools`. The SDK calls them automatically and feeds results back until the model produces a final answer or `max_tool_rounds` is reached.

```python
def get_weather(location: str) -> str:
    return f"The weather in {location} is sunny, 22 °C."

text = client.generate(
    messages=[{"role": "user", "content": "What is the weather in Seoul?"}],
    tools=[get_weather],
)
print(text)
```

Async tools are supported in `agenerate` / `AsyncClient.generate`:

```python
async def fetch_price(symbol: str) -> str:
    ...  # async I/O
    return "105.3"

text = await client.agenerate(
    messages=[{"role": "user", "content": "What is the price of AAPL?"}],
    tools=[fetch_price],
)
```

### Structured Output

Pass a Pydantic model or a JSON Schema dict as `output_schema`. `generate` / `agenerate` parse and validate the response and return a plain dict.

```python
from pydantic import BaseModel

class UserInfo(BaseModel):
    name: str
    age: int

user = client.generate(
    messages=[{"role": "user", "content": "My name is John and I am 30."}],
    output_schema=UserInfo,
)
print(user["name"])   # "John"
print(user["age"])    # 30
```

## Client Configuration

```python
from oauth_codex import Client

client = Client(
    base_url="https://chatgpt.com/backend-api/codex",  # optional override
    timeout=60.0,                # request timeout in seconds
    max_retries=2,               # retry count for retryable errors
    compat_storage_dir="/tmp/codex",  # optional local compatibility storage
    authenticate_on_init=True,   # trigger auth during __init__
)
```

`AsyncClient` accepts the same constructor arguments.

## Error Handling

```python
from oauth_codex import (
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    BadRequestError,
    NotFoundError,
    InternalServerError,
)

try:
    response = client.chat.completions.create(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "Hello"}],
    )
except AuthenticationError:
    print("OAuth token missing or invalid — call client.authenticate()")
except RateLimitError:
    print("Rate limit hit — back off and retry")
except APIStatusError as e:
    print(f"HTTP {e.status_code}: {e.message}")
```

## Documentation

- English: [`docs/en/index.md`](docs/en/index.md)
- Korean: [`docs/ko/index.md`](docs/ko/index.md)

## Development

```bash
pytest -q
```

## Changelog

[`CHANGELOG.md`](CHANGELOG.md)
