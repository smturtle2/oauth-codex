[English](request_options.md) | [한국어](../../ko/methods/request_options.md)

# Request Options Deep Guide

This page describes request option precedence and validation behavior in `oauth-codex`.

## Scope

The options below are primarily applied through `responses.create(...)` and `responses.stream(...)`.

## Method Summary

| Option | Purpose |
|---|---|
| `extra_headers` | Add request headers safely |
| `extra_query` | Add query string parameters |
| `extra_body` | Merge additional JSON body fields |
| `validation_mode` | Choose warning/error/ignore behavior for validation checks |
| `store` + `store_behavior` | Control persistence behavior on Codex profile |
| `service_tier` | Currently ignored with validation warning/error policy |
| `previous_response_id` | Continuation semantics with local compatibility on Codex profile |

## Request Option Processing Order

For Responses requests, processing is effectively:

1. Validate/normalize core parameters (`temperature`, `top_p`, `max_output_tokens`, etc.).
2. Normalize `store` based on profile and `store_behavior`.
3. Normalize `extra_headers`, `extra_query`, `extra_body` under `validation_mode`.
4. Build base payload.
5. Merge `extra_body` last (`payload.update(extra_body)`).
6. Apply `extra_headers` / `extra_query` at HTTP request stage.

## `validation_mode`

### Values

- `"warn"` (default): emit warnings and continue.
- `"error"`: raise `ParameterValidationError` for validation failures.
- `"ignore"`: suppress warnings/errors for validation-only checks.

### Affected checks (examples)

- Type/range checks for `temperature`, `top_p`, `max_output_tokens`, `metadata`, `include`.
- Enum checks for `truncation`.
- Header protection checks in `extra_headers`.
- Unsupported extra kwargs (reported as unsupported parameters).
- `service_tier` ignored notice.

## `extra_headers`

### Signature usage

```python
client.responses.create(..., extra_headers={"x-trace-id": "abc123"})
```

### Validation and merge behavior

- Must be `dict[str, str]`.
- Keys are checked case-insensitively against protected headers.
- Protected headers are blocked:
  - `Authorization`
  - `ChatGPT-Account-ID`
  - `Content-Type`
- Non-protected headers are merged into request headers.

### Error / warning policy

- `warn`: warns and drops invalid/protected entries.
- `error`: raises `ParameterValidationError`.
- `ignore`: skips validation messaging (invalid values may be dropped by normalization).

## `extra_query`

### Signature usage

```python
client.responses.create(..., extra_query={"trace": "1", "debug": "true"})
```

### Validation and merge behavior

- Must be a dictionary.
- Merged into HTTP query params for the request.

### Error / warning policy

- Invalid non-dict values follow `validation_mode` behavior.

## `extra_body`

### Signature usage

```python
client.responses.create(..., extra_body={"custom_flag": True})
```

### Validation and merge behavior

- Must be a dictionary.
- Merged last into JSON payload, so overlapping keys override previously assembled payload values.

### Precedence rule

If both standard params and `extra_body` set same key, `extra_body` wins.

## `store` and `store_behavior` on Codex profile

### Relevant client setting

- `store_behavior` is a client-level constructor option:
  - `"auto_disable"` (default)
  - `"error"`
  - `"passthrough"`

### Behavior when request sets `store=True`

| `store_behavior` | Result |
|---|---|
| `auto_disable` | Request payload uses `store=False` |
| `error` | Raises validation error |
| `passthrough` | Leaves `store=True` |

## `service_tier`

- Accepted as input but currently ignored on Codex backend.
- Emits warning or error depending on `validation_mode`.

## `previous_response_id`

### Behavior

- Included as upstream payload when applicable.
- On Codex profile, local continuity compatibility may rewrite effective input and persist continuation state.

### Continuity checks

- If response `previous_response_id` conflicts with requested value, raises `ContinuityError`.

## Sync / Async / Module-level Usage Snippets

### Sync

```python
resp = client.responses.create(
    model="gpt-5.3-codex",
    input="hello",
    extra_headers={"x-trace-id": "abc123"},
    extra_query={"trace": "1"},
    extra_body={"custom_flag": True},
    validation_mode="warn",
)
```

### Async

```python
resp = await async_client.responses.create(
    model="gpt-5.3-codex",
    input="hello",
    extra_body={"custom_flag": True},
)
```

### Module-level

```python
import oauth_codex

resp = oauth_codex.responses.create(
    model="gpt-5.3-codex",
    input="hello",
    extra_query={"trace": "1"},
)
```

## Pitfalls / Troubleshooting

- Do not rely on `service_tier` today; it is intentionally ignored.
- Be careful with `extra_body` key collisions because merge-last can override core fields.
- If behavior seems too permissive, switch to `validation_mode="error"`.
