[English](removed_apis.md) | [한국어](../../ko/methods/removed_apis.md)

# Removed APIs Guide (v2)

From v2, the module-level proxy surface and the legacy `AsyncOAuthCodexClient` class name
were removed from the **public** API. The modern `AsyncClient` alias is **fully supported**
and is the recommended async entry point.

## Removed public surfaces

- `AsyncOAuthCodexClient` (internal class name — use `AsyncClient` instead)
- Module-level resource proxies: `oauth_codex.responses`, `oauth_codex.files`, `oauth_codex.vector_stores`, `oauth_codex.models`
- Resource-style shorthand: `client.files.*`, `client.vector_stores.*`, `client.models.*`
- `oauth_codex.compat` public module
- Advanced request option public interface

> **`AsyncClient` is NOT removed.** It is exported from `oauth_codex` and is the canonical async client class.

## Current public API

```python
from oauth_codex import Client       # sync client
from oauth_codex import AsyncClient  # async client (fully supported)
```

## Replacement mapping

| Old / removed | Replacement |
|---|---|
| `AsyncOAuthCodexClient(...)` | `AsyncClient(...)` |
| `oauth_codex.responses.create(...)` | `client.responses.create(...)` |
| Module-level proxies | Instantiate a `Client` or `AsyncClient` first |

### Text generation

```python
# Sync
text = client.generate(messages)

# Async (AsyncClient)
text = await async_client.generate(messages)

# Async bridge on sync Client
text = await client.agenerate(messages)
```

### Streaming

```python
# Sync
for chunk in client.stream(messages):
    print(chunk, end="")

# Async (AsyncClient)
async for chunk in async_client.stream(messages):
    print(chunk, end="")

# Async bridge on sync Client
async for chunk in client.astream(messages):
    print(chunk, end="")
```

### Image input

```python
messages = [{"role": "user", "content": [{"type": "input_image", "image_url": "..."}]}]
response = client.chat.completions.create(model="gpt-5.3-codex", messages=messages)
```

### Function calling

```python
tools = [my_callable]  # list of Python callables — automatic execution
text = client.generate(messages, tools=tools)
```

## See also

- [Client Methods](client.md)
- [Migration Guide](../../migration_openai_to_oauth_codex.md)
