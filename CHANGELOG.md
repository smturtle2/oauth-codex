# Changelog

## 4.0.0

### Breaking

- Removed the legacy generate-first surface: `generate`, `agenerate`, `stream`, `astream`
- Removed `authenticate_on_init`
- Removed internal legacy modules and compatibility storage implementation from the package
- Removed module-level proxy usage such as `oauth_codex.responses.create(...)`

### Added

- Added `Client.authenticate()` and `AsyncClient.authenticate()` as the supported public OAuth entrypoints
- Exposed `client.vector_stores.file_batches`
- Standardized the package around the resource-style `Client` / `AsyncClient` surface

### Changed

- Updated README, docs, examples, and migration guides to match the 4.0 API
- Version metadata is now single-sourced from `src/oauth_codex/_version.py`
- Added CI for test, build, and wheel smoke validation on push and pull request
- Hardened tag-driven PyPI publish validation with changelog, version, test, build, and wheel smoke gates

## 3.2.3

### Fixed

- Updated `client.beta.chat.completions.run_tools`/`arun_tools` to follow modern Responses API tool loop semantics
- Tool execution rounds now submit `function_call_output` items with `call_id` and carry `previous_response_id` across rounds
