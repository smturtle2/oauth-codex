# Migration: OpenAI SDK -> oauth-codex

This guide focuses on the currently supported runtime surface.

## Supported mappings

- `responses.*` -> `responses.*`
- `files.*` -> `files.*`
- `vector_stores.*` -> `vector_stores.*`
- `models.capabilities/retrieve/list` -> same names

## Removed legacy modules/types

- `oauth_codex.legacy_types` removed
- `oauth_codex.legacy_auth` removed

Use:

- `oauth_codex.core_types`

## Notes

- Module-level calls are supported for `responses`, `files`, `vector_stores`, `models` only.
- Removed resources/methods now fail by missing attribute/import (`AttributeError` / `ImportError`).
