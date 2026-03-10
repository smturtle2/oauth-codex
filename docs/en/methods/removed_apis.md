[English](removed_apis.md) | [한국어](../../ko/methods/removed_apis.md)

# Removed APIs Guide (v4.0)

Version 4.0 removes the remaining generate-first and legacy compatibility surface. The supported public API is the resource-style `Client` / `AsyncClient` interface.

## Removed APIs

- `authenticate_on_init`
- `generate`, `agenerate`, `stream`, `astream`
- `OAuthCodexClient`
- `AsyncOAuthCodexClient`
- Module-level resource proxies: `oauth_codex.responses`, `oauth_codex.files`, `oauth_codex.vector_stores`, `oauth_codex.models`
- local compatibility storage / legacy continuation internals
- `oauth_codex.compat`

## Replacement mapping

| Old / removed | Replacement |
|---|---|
| `Client(authenticate_on_init=True)` | `client = Client(); client.authenticate()` |
| `AsyncOAuthCodexClient(...)` | `AsyncClient(...)` |
| `client.generate(...)` | `client.chat.completions.create(...)` or `client.responses.create(...)` |
| `client.stream(...)` | `client.responses.stream(...)` |
| `client.generate(..., tools=[...])` | `client.beta.chat.completions.run_tools(...)` |
| `oauth_codex.responses.create(...)` | `client.responses.create(...)` |
| Module-level proxies | Instantiate `Client` or `AsyncClient` first |

## See also

- [Client Methods](client.md)
- [Migration Guide](../../migration_openai_to_oauth_codex.md)
