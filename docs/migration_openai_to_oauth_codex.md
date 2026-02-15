# Migration: OpenAI SDK -> oauth-codex

This guide focuses on the v2 runtime surface.

## v2 Public Surface

- `oauth_codex.Client` (single public client)
- `Client.generate(...)`
- `Client.stream(...)`
- `Client.agenerate(...)`
- `Client.astream(...)`

## Removed in v2

- `AsyncOAuthCodexClient`, `AsyncClient`
- module-level proxies (`oauth_codex.responses/files/vector_stores/models`)
- resource-style public API (`client.responses.*`, `client.files.*`, `client.vector_stores.*`, `client.models.*`)
- `oauth_codex.compat` public module
- advanced request options public API

## Notes

- Function calling is automatic in `generate/stream/agenerate/astream`.
- Image input analysis is supported via `images=` (URL or local file path).
