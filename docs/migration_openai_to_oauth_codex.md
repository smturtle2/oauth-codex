# Migration: OpenAI SDK -> oauth-codex

## 1) Client

Before:

```python
from openai import OpenAI
client = OpenAI()
```

After:

```python
from oauth_codex import OAuthCodexClient
client = OAuthCodexClient()
```

Async:

```python
from oauth_codex import AsyncOAuthCodexClient
client = AsyncOAuthCodexClient()
```

## 2) API Mapping

| OpenAI-style | oauth-codex |
|---|---|
| `client.responses.create(...)` | `client.responses.create(...)` |
| `client.responses.input_tokens.count(...)` | `client.responses.input_tokens.count(...)` |
| `client.files.create(...)` | `client.files.create(...)` |
| `client.vector_stores.*` | `client.vector_stores.*` |

## 3) Response Object Mapping

| Field | oauth-codex ResponseCompat |
|---|---|
| `id` | `response.id` |
| `output` | `response.output` |
| `output_text` | `response.output_text` |
| `usage` | `response.usage` |
| `error` | `response.error` |
| reasoning summary | `response.reasoning_summary` |
| reasoning items | `response.reasoning_items` |
| encrypted reasoning | `response.encrypted_reasoning_content` |

## 4) Error Mapping

| Category | Exception |
|---|---|
| request/provider error | `SDKRequestError` |
| unsupported profile action | `NotSupportedError` |
| parameter validation | `ParameterValidationError` |
| continuity mismatch | `ContinuityError` |
| token store read/write/delete | `TokenStoreReadError` / `TokenStoreWriteError` / `TokenStoreDeleteError` |

## 5) Parameter Behavior Notes

- `store=True` + Codex OAuth profile: 기본 `auto_disable` 정책으로 `store=False` 전환
- `service_tier`: 기본 ignore+warn
- `validation_mode`: `warn`(기본), `error`, `ignore`

## 6) Streaming Event Mapping

Recommended parser targets:

- `response_started`
- `text_delta`
- `reasoning_delta`
- `reasoning_done`
- `tool_call_started`
- `tool_call_arguments_delta`
- `tool_call_done`
- `usage`
- `response_completed`
- `error`

See also: `docs/stream_event_schema_v1.md`
