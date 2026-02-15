[English](unsupported-matrix.md) | [한국어](../ko/unsupported-matrix.md)

# Unsupported Resource Matrix

This page separates runtime-supported resources from structure-only resources.

## Runtime-supported Resources

| Resource | Runtime status | Method docs |
|---|---|---|
| `responses` | Supported (partial) | [Responses Methods](methods/responses.md) |
| `responses.input_tokens` | Supported | [Responses Methods](methods/responses.md) |
| `files` | Supported | [Files Methods](methods/files.md) |
| `vector_stores` | Supported | [Vector Stores Methods](methods/vector_stores.md) |
| `vector_stores.files` | Supported (partial) | [Vector Stores Methods](methods/vector_stores.md) |
| `vector_stores.file_batches` | Supported | [Vector Stores Methods](methods/vector_stores.md) |
| `models` | Supported (partial) | [Models Methods](methods/models.md) |

## Known unsupported methods inside otherwise supported resources

| Method | Behavior |
|---|---|
| `responses.retrieve` | `NotSupportedError(code="not_supported")` |
| `responses.cancel` | `NotSupportedError(code="not_supported")` |
| `responses.delete` | `NotSupportedError(code="not_supported")` |
| `responses.compact` | `NotSupportedError(code="not_supported")` |
| `responses.parse` | `NotSupportedError(code="not_supported")` |
| `responses.input_items.list` | `NotSupportedError(code="not_supported")` |
| `models.delete` | `NotSupportedError(code="not_supported")` |
| `vector_stores.files.update` | `NotSupportedError(code="not_supported")` |

## Structure-only Resources (OpenAI-style surface parity)

The following resource groups are exposed for surface parity, but runtime calls currently raise `NotSupportedError(code="not_supported")`:

- `completions`
- `chat` and `chat.completions.*`
- `embeddings`
- `images`
- `audio.*`
- `moderations`
- `fine_tuning.*`
- `beta.*` (assistants, threads, runs, realtime/chatkit groups)
- `batches`
- `uploads.*`
- `realtime.*`
- `conversations.*`
- `evals.*`
- `containers.*`
- `videos`
- `webhooks`

## Codex profile path restrictions (`not_supported_on_codex_oauth`)

When using Codex profile base URL (`https://chatgpt.com/backend-api/codex`):

- Only `/responses` and `/responses/input_tokens` are allowed as direct upstream paths.
- Other direct paths are blocked and raise:

```python
NotSupportedError(code="not_supported_on_codex_oauth")
```

Vector store and files behavior on Codex profile is supported through local compatibility emulation, not direct backend parity.
