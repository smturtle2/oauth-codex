# Stream Event Schema v1

All events carry `schema_version="v1"`.

## Common Fields

- `type: str`
- `schema_version: str` (fixed `v1`)
- `response_id: str | None`
- `raw: dict | None`

## Event Types

### `response_started`

- emitted at stream start
- key field: `response_id`

### `text_delta`

- assistant text token/chunk
- key field: `delta`

### `reasoning_delta`

- reasoning-only text chunk
- key field: `delta`

### `reasoning_done`

- emitted when reasoning section is closed

### `tool_call_started`

- emitted once per tool call id
- key field: `call_id`

### `tool_call_arguments_delta`

- incremental tool argument JSON chunk
- key fields: `call_id`, `delta`

### `tool_call_done`

- final tool call snapshot
- key fields: `call_id`, `tool_call`

### `usage`

- usage metrics update
- key field: `usage`

### `response_completed`

- stream completion with finish metadata
- key field: `finish_reason`

### `error`

- stream-level error event
- key field: `error`

## Compatibility Notes

- `tool_call_delta` is still emitted as backward-compatible alias for legacy parsers.
- For old consumers, `done` event is still emitted after `response_completed`.
