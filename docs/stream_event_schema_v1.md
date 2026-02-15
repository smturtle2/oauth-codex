# Stream Event Schema v1

All stream events carry `schema_version="v1"`.

## Common fields

- `type: str`
- `schema_version: str` (`v1`)
- `response_id: str | None`
- `raw: dict | None`

## Event types

- `response_started`
- `text_delta`
- `reasoning_delta`
- `tool_call_started`
- `tool_call_arguments_delta`
- `tool_call_done`
- `usage`
- `response_completed`
- `done`
- `error`

`tool_call_arguments_delta` is the canonical event for tool-call argument streaming.
