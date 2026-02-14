# Changelog

## 0.5.0

### Added

- Codex profile local compatibility backend
  - `files.create` now auto-falls back to local persistent storage
  - `vector_stores.create/retrieve/list/update/delete/search` now auto-fall back to local persistent storage
- Local compatibility storage path configuration
  - constructor arg: `compat_storage_dir`
  - env var: `CODEX_COMPAT_STORAGE_DIR`

### Changed

- `validate_model=True` on codex profile now performs local validation (model must be non-empty string) instead of raising unsupported error.

## 0.4.0

### Added

- OpenAI-compatible client surface
  - `OAuthCodexClient` / `AsyncOAuthCodexClient`
  - `responses.create`
  - `responses.input_tokens.count`
  - `files.create`
  - `vector_stores.*`
  - `models.capabilities`
- Response compatibility type (`ResponseCompat`) with
  - `id`, `output`, `output_text`, `usage`, `error`
  - `reasoning_summary`, `reasoning_items`, `encrypted_reasoning_content`
- Validation modes: `warn` / `error` / `ignore`
- Store behavior modes: `auto_disable` / `error` / `passthrough`
- Standardized request error model: `SDKRequestError`
- Token store failure exceptions
  - `TokenStoreReadError`, `TokenStoreWriteError`, `TokenStoreDeleteError`
- `NotSupportedError`, `ContinuityError`, `ParameterValidationError`
- Streaming event schema v1 with reasoning/tool lifecycle events
- Observability hooks
  - `on_request_start`, `on_request_end`, `on_auth_refresh`, `on_error`
- Retry policy defaults
  - 401 refresh retry
  - 429/5xx exponential backoff with jitter

### Changed

- `store=True` on codex OAuth profile is auto-disabled by default.
- Usage model now exposes unified metrics fields (`cached_tokens`, `reasoning_tokens`) while keeping backward-compatible aliases.

### Docs

- Added `docs/migration_openai_to_oauth_codex.md`
- Added `docs/stream_event_schema_v1.md`
- Updated `README.md` with compatibility, policy, and retry sections.
