[English](removed_apis.md) | [한국어](../../ko/methods/removed_apis.md)

# Removed APIs Guide (v2)

From v2, the public surface is reduced to a single `Client` class.

## Removed public surfaces

- `AsyncOAuthCodexClient`, `AsyncClient`
- module-level proxies (`oauth_codex.responses`, `oauth_codex.files`, `oauth_codex.vector_stores`, `oauth_codex.models`)
- resource-style API (`client.responses.*`, `client.files.*`, `client.vector_stores.*`, `client.models.*`)
- public `oauth_codex.compat` module
- advanced request option public interface

## Replacement

- text generation: `client.generate(...)`
- text streaming: `client.stream(...)`
- async generation: `await client.agenerate(...)`
- async streaming: `async for d in client.astream(...): ...`
- image input analysis: `messages=[{"role":"user","content":[{"type":"input_image",...}]}]`
- function calling: `tools=[callable, ...]` (automatic)

## See also

- [Client Methods](client.md)
- [Migration Guide](../../migration_openai_to_oauth_codex.md)
