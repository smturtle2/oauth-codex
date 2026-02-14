# Changelog

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
