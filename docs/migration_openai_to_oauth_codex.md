# Migration: OpenAI SDK -> oauth-codex

`oauth-codex` keeps the familiar OpenAI-style resource layout while authenticating with OAuth PKCE instead of static API keys.

## Client Mapping

| Concept | OpenAI SDK | oauth-codex |
|---|---|---|
| Sync client | `openai.OpenAI()` | `oauth_codex.Client()` |
| Async client | `openai.AsyncOpenAI()` | `oauth_codex.AsyncClient()` |
| Chat completions | `client.chat.completions.create(...)` | `client.chat.completions.create(...)` |
| Responses API | `client.responses.create(...)` | `client.responses.create(...)` |
| Authentication | `api_key=` | `client.authenticate()` |

Both `Client` and `AsyncClient` are public and supported:

```python
from oauth_codex import AsyncClient, Client
```

## Authentication

Unlike the OpenAI SDK, there is no `api_key=`. The SDK uses OAuth PKCE:

```python
client = Client()
client.authenticate()
```

At the first login, the SDK prints a browser URL, asks you to complete the sign-in flow, and then prompts for the localhost callback URL. Tokens are stored locally and refreshed automatically.

## Basic Migration Steps

### 1. Replace imports

```python
from openai import OpenAI, AsyncOpenAI

# becomes
from oauth_codex import Client, AsyncClient
```

### 2. Replace API-key configuration

```python
client = OpenAI(api_key="sk-...")

# becomes
client = Client()
client.authenticate()
```

### 3. Keep resource-style method calls

```python
response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "Write a Python function to sort a list."}],
)
print(response.choices[0].message.content)
```

## Lower-Level Responses Access

```python
response = client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "Analyze this code."}],
)
print(response.output_text)
```

## Structured Output And Tool Calls

```python
from pydantic import BaseModel


class Summary(BaseModel):
    title: str
    score: int


parsed = client.responses.parse(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "Return JSON"}],
    response_format=Summary,
)
print(parsed.parsed)


def add(a: int, b: int) -> int:
    return a + b


tool_completion = client.beta.chat.completions.run_tools(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "What is 2 + 3?"}],
    tools=[add],
)
print(tool_completion.choices[0].message.content)
```

## If You Used Older oauth-codex APIs

4.0 removes the older generate-first surface:

- `authenticate_on_init`
- `generate`, `agenerate`, `stream`, `astream`
- module-level proxies such as `oauth_codex.responses.create(...)`

Use `client.authenticate()`, `client.chat.completions.create(...)`, `client.responses.stream(...)`, and `client.beta.chat.completions.run_tools(...)` instead.
