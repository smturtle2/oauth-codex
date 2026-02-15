[English](responses.md) | [한국어](../../ko/methods/responses.md)

# Responses Methods

This page documents `responses` runtime methods in `oauth-codex`.

## Method Summary

| Method | Support | Notes |
|---|---|---|
| `responses.create(...)` | Supported | Main generation entrypoint; non-stream and stream modes |
| `responses.stream(...)` | Supported | Convenience wrapper for `create(stream=True, ...)` |
| `responses.input_tokens.count(...)` | Supported | Input token counting endpoint |
| `responses.retrieve(...)` | Unsupported | Raises `NotSupportedError(code="not_supported")` |
| `responses.cancel(...)` | Unsupported | Raises `NotSupportedError(code="not_supported")` |
| `responses.delete(...)` | Unsupported | Raises `NotSupportedError(code="not_supported")` |
| `responses.compact(...)` | Unsupported | Raises `NotSupportedError(code="not_supported")` |
| `responses.parse(...)` | Unsupported | Raises `NotSupportedError(code="not_supported")` |
| `responses.input_items.list(...)` | Unsupported | Raises `NotSupportedError(code="not_supported")` |

## `responses.create`

### Sync / Async / Module-level Signatures

```python
# sync client
client.responses.create(*, stream: bool = False, **kwargs) -> Response | Iterator[StreamEvent]

# async client
await client.responses.create(*, stream: bool = False, **kwargs) -> Response | AsyncIterator[StreamEvent]

# module-level
oauth_codex.responses.create(*, stream: bool = False, **kwargs)
```

### Parameters

| Parameter | Type | Required | Default | Validation / Behavior |
|---|---|---|---|---|
| `model` | `str` | Yes | - | Required model id |
| `input` | `str | dict | list[dict]` | Yes (or `messages`) | `None` | Cannot be used with `messages`; non-empty list required for list input |
| `messages` | `list[dict]` | Yes (or `input`) | `None` | Alias input path; non-empty list required |
| `tools` | `list` | No | `None` | Normalized to Responses tool schema |
| `tool_results` | `list[ToolResult|dict]` | No | `None` | Converted to continuation items |
| `response_format` | `dict` | No | `None` | Mapped to payload `text.format` |
| `tool_choice` | `str | dict` | No | `None` | Passed to backend |
| `strict_output` | `bool` | No | `False` | Influences tool schema conversion |
| `store` | `bool` | No | `False` | On Codex profile: controlled by `store_behavior` |
| `reasoning` | `dict` | No | `None` | `effort` must be string; `summary` must be string or bool |
| `previous_response_id` | `str` | No | `None` | Local continuity emulation on Codex profile |
| `instructions` | `str` | No | auto-derived | Uses first system message or default fallback |
| `temperature` | `float` | No | `None` | Must be within `[0, 2]` |
| `top_p` | `float` | No | `None` | Must be within `(0, 1]` |
| `max_output_tokens` | `int` | No | `None` | Must be positive integer |
| `metadata` | `dict` | No | `None` | Must be dict |
| `include` | `list[str]` | No | `None` | Must be list of strings |
| `max_tool_calls` | `int` | No | `None` | Must be positive integer |
| `parallel_tool_calls` | `bool` | No | `None` | Must be bool |
| `truncation` | `"auto" | "disabled"` | No | `None` | Validated enum |
| `extra_headers` | `dict[str, str]` | No | `None` | Protected headers cannot be overridden |
| `extra_query` | `dict` | No | `None` | Merged into request query params |
| `extra_body` | `dict` | No | `None` | Merge-last into JSON body (overrides prior keys) |
| `service_tier` | `str` | No | `None` | Currently ignored with warning/error by validation mode |
| `stream` | `bool` | No | `False` | `True` returns iterator of stream events |
| `validation_mode` | `"warn" | "error" | "ignore"` | No | client default | Controls validation warning/error policy |

### Return Shape

#### Non-stream mode (`stream=False`)

Returns `oauth_codex.types.responses.Response` with key fields:

- `id: str`
- `output: list[dict]`
- `output_text: str`
- `usage: TokenUsage | None`
- `error: dict | None`
- `reasoning_summary: str | None`
- `reasoning_items: list[dict]`
- `encrypted_reasoning_content: str | None`
- `finish_reason: str | None`
- `previous_response_id: str | None`
- `raw_response: dict | None`

#### Stream mode (`stream=True`)

Returns iterator of normalized stream events, including:

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
- `done`

### Error Cases

| Exception | Trigger |
|---|---|
| `AuthRequiredError` | Missing or non-refreshable OAuth credentials |
| `SDKRequestError` | HTTP/provider failure, stream error, invalid JSON shape |
| `ParameterValidationError` | Invalid param under `validation_mode="error"` |
| `ContinuityError` | `previous_response_id` continuity mismatch in response payload |
| `ValueError` | Invalid `input/messages` combination or empty list inputs |
| `TypeError` | Unsupported input/tool_results value type |

### Behavior Notes

- Codex profile (`/backend-api/codex`) stores response continuity locally.
- With Codex profile and `store=True`:
  - `store_behavior="auto_disable"` -> `store` becomes `False` (default)
  - `store_behavior="error"` -> raise validation error
  - `store_behavior="passthrough"` -> send `store=True`
- `extra_body` is merged last and can intentionally override earlier payload fields.

### Runnable Usage Snippets

#### Sync

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()
resp = client.responses.create(
    model="gpt-5.3-codex",
    input="Return JSON with ok=true",
    response_format={"type": "json_object"},
    reasoning={"effort": "low"},
)
print(resp.output_text)
```

#### Async

```python
import asyncio
from oauth_codex import AsyncOAuthCodexClient


async def main() -> None:
    client = AsyncOAuthCodexClient()
    resp = await client.responses.create(model="gpt-5.3-codex", input="hello")
    print(resp.output_text)


asyncio.run(main())
```

#### Module-level

```python
import oauth_codex

resp = oauth_codex.responses.create(model="gpt-5.3-codex", input="hello")
print(resp.output_text)
```

#### Streaming

```python
from oauth_codex import OAuthCodexClient

client = OAuthCodexClient()
for event in client.responses.stream(model="gpt-5.3-codex", input="stream this"):
    if event.type == "text_delta" and event.delta:
        print(event.delta, end="", flush=True)
```

### Pitfalls / Troubleshooting

- Do not pass both `input` and `messages` in the same call.
- If you rely on strict validation, set `validation_mode="error"`.
- Avoid overriding protected headers (`Authorization`, `ChatGPT-Account-ID`, `Content-Type`) via `extra_headers`.

## `responses.stream`

### Sync / Async / Module-level Signatures

```python
# sync client
client.responses.stream(**kwargs) -> Iterator[StreamEvent]

# async client
await client.responses.stream(**kwargs) -> AsyncIterator[StreamEvent]

# module-level
oauth_codex.responses.stream(**kwargs)
```

### Parameters

- Same as `responses.create(...)` except `stream` is implicitly `True`.

### Return Shape

- Stream events iterator identical to `responses.create(stream=True, ...)`.

### Error Cases

- Same as `responses.create(stream=True, ...)`.

### Behavior Notes

- This is a convenience wrapper around `create(stream=True, ...)`.

### Runnable Usage Snippets

```python
for event in client.responses.stream(model="gpt-5.3-codex", input="hello"):
    if event.type == "text_delta":
        print(event.delta)
```

### Pitfalls / Troubleshooting

- If you need final aggregated text, collect `text_delta` chunks yourself or call non-stream `create`.

## `responses.input_tokens.count`

### Sync / Async / Module-level Signatures

```python
# sync client
client.responses.input_tokens.count(*, input, model: str | None = None, tools: list | None = None)

# async client
await client.responses.input_tokens.count(*, input, model: str | None = None, tools: list | None = None)

# module-level
oauth_codex.responses.input_tokens.count(...)
```

### Parameters

| Parameter | Type | Required | Default | Validation / Behavior |
|---|---|---|---|---|
| `input` | `str | dict | list[dict]` | Yes | - | Normalized to responses input items |
| `model` | `str | None` | No | `None` | Wrapper sends empty string if omitted |
| `tools` | `list | None` | No | `None` | Tool schema normalization applies |

### Return Shape

Returns `InputTokenCountResponse`:

- `input_tokens: int`
- `cached_tokens: int | None`
- `total_tokens: int | None`

### Error Cases

| Exception | Trigger |
|---|---|
| `SDKRequestError` | Endpoint error or malformed token-count response |
| `ValueError` | Invalid input shape |

### Behavior Notes

- Uses endpoint path `/responses/input_tokens`.
- On malformed response missing `input_tokens`, raises `SDKRequestError` with provider code `invalid_input_tokens_response`.

### Runnable Usage Snippets

```python
out = client.responses.input_tokens.count(
    model="gpt-5.3-codex",
    input="Count my tokens",
)
print(out.input_tokens, out.cached_tokens, out.total_tokens)
```

### Pitfalls / Troubleshooting

- Treat `cached_tokens` and `total_tokens` as optional fields.

## Unsupported Methods in `responses`

The following methods exist for structure parity but are not runtime-supported:

- `responses.retrieve`
- `responses.cancel`
- `responses.delete`
- `responses.compact`
- `responses.parse`
- `responses.input_items.list`

All raise:

```python
NotSupportedError(code="not_supported")
```
