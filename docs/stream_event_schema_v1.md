# Stream Event Schema v1

`client.responses.stream(...)` and `await client.responses.stream(...)` yield `ResponseStreamEvent` objects with `schema_version="v1"`.

## Common fields

- `type: str`
- `schema_version: str` (`v1`)
- `response_id: str | None`
- `raw: dict | None`
- `delta: str | None`
- `call_id: str | None`
- `finish_reason: str | None`
- `error: str | None`

## Event types

- `response_started`
- `text_delta`
- `reasoning_delta`
- `reasoning_done`
- `tool_call_started`
- `tool_call_arguments_delta`
- `tool_call_done`
- `usage`
- `response_completed`
- `done`
- `error`

`tool_call_arguments_delta` is the canonical event for tool-call argument streaming.
