[English](client.md) | [한국어](../../ko/methods/client.md)

# Client Methods

`oauth-codex` exposes two first-class clients:

| Class | Import | Use when |
|---|---|---|
| `Client` | `from oauth_codex import Client` | Synchronous / blocking code |
| `AsyncClient` | `from oauth_codex import AsyncClient` | `async`/`await` code, event loops |

Both clients expose the same namespaces. The async client uses native async methods; the sync client uses blocking methods.

## Construction

```python
from oauth_codex import Client

client = Client()
```

```python
from oauth_codex import AsyncClient

client = AsyncClient()
```

## Authentication

Call `authenticate()` once before the first request to trigger interactive OAuth login when needed.

```python
client.authenticate()
await client.authenticate()
```

Tokens are stored locally and refreshed automatically on later requests.

## Chat Completions

```python
response = client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

```python
response = await client.chat.completions.create(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "Hello async!"}],
)
print(response.choices[0].message.content)
```

### Structured parsing

```python
from pydantic import BaseModel


class Summary(BaseModel):
    title: str
    score: int


completion = client.chat.completions.parse(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "Return JSON with title and score"}],
    response_format=Summary,
)
print(completion.parsed)
```

## Responses Resource

`responses` gives lower-level access to the backend payload shape.

```python
response = client.responses.create(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "Analyze this code."}],
)
print(response.output_text)
```

### Parse structured output

```python
response = client.responses.parse(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "Return JSON with title and score"}],
    response_format=Summary,
)
print(response.parsed)
```

### Stream events

```python
for event in client.responses.stream(
    model="gpt-5.3-codex",
    input=[{"role": "user", "content": "Say hello"}],
):
    if event.type == "text_delta" and event.delta:
        print(event.delta, end="", flush=True)
```

### Input token counting

```python
tokens = client.responses.input_tokens.count(
    model="gpt-5.3-codex",
    input="hello",
)
print(tokens.input_tokens)
```

## Beta Tool Loop

Use `beta.chat.completions.run_tools(...)` to let the SDK execute callable tools across multiple rounds.

```python
def add(a: int, b: int) -> int:
    return a + b


completion = client.beta.chat.completions.run_tools(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "What is 1 + 2?"}],
    tools=[add],
)
print(completion.choices[0].message.content)
```

`AsyncClient` exposes `await client.beta.chat.completions.arun_tools(...)` for async callables.

## Files, Vector Stores, and Models

```python
uploaded = client.files.create(file=b"hello", purpose="assistants")
vector_store = client.vector_stores.create(name="docs", file_ids=[uploaded.id])
linked = client.vector_stores.files.create(vector_store.id, file_id=uploaded.id)
batch = client.vector_stores.file_batches.create(vector_store.id, file_ids=[uploaded.id])
models = client.models.list()
print(uploaded.id, vector_store.id, linked.id, batch.id, models.object)
```

## Removed In 4.0

- `authenticate_on_init`
- `generate`, `agenerate`, `stream`, `astream`
- `OAuthCodexClient`, `AsyncOAuthCodexClient`
- module-level proxy calls such as `oauth_codex.responses.create(...)`

## See also

- [Removed APIs Guide](removed_apis.md)
- [Migration Guide](../../migration_openai_to_oauth_codex.md)
