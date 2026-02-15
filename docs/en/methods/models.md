[English](models.md) | [한국어](../../ko/methods/models.md)

# Models Methods

This page documents `models` runtime methods in `oauth-codex`.

## Method Summary

| Method | Support | Notes |
|---|---|---|
| `models.capabilities(model)` | Supported | Returns capability flags |
| `models.retrieve(model)` | Supported | Returns model-like object with capabilities |
| `models.list()` | Supported | Returns list payload (currently static representative entry) |
| `models.delete(...)` | Unsupported | Raises `NotSupportedError(code="not_supported")` |

## `models.capabilities`

### Sync / Async / Module-level Signatures

```python
client.models.capabilities(model: str) -> ModelCapabilities
await client.models.capabilities(model: str) -> ModelCapabilities
oauth_codex.models.capabilities(model)
```

### Parameters

| Parameter | Type | Required | Default | Validation / Behavior |
|---|---|---|---|---|
| `model` | `str` | Yes | - | Model id input |

### Return Shape

Returns `ModelCapabilities`:

- `supports_reasoning: bool`
- `supports_tools: bool`
- `supports_store: bool`
- `supports_response_format: bool`

### Error Cases

| Exception | Trigger |
|---|---|
| `SDKRequestError` | Rare, if underlying engine path fails unexpectedly |

### Behavior Notes

- `supports_store` depends on profile:
  - Codex profile: `False`
  - non-Codex profile: `True`

### Runnable Usage Snippets

```python
caps = client.models.capabilities("gpt-5.3-codex")
print(caps.supports_tools, caps.supports_store)
```

### Pitfalls / Troubleshooting

- Capability values are SDK capability mapping, not a live `/models` backend contract.

## `models.retrieve`

### Sync / Async / Module-level Signatures

```python
client.models.retrieve(model: str) -> dict
await client.models.retrieve(model: str) -> dict
oauth_codex.models.retrieve(model)
```

### Parameters

| Parameter | Type | Required | Default | Validation / Behavior |
|---|---|---|---|---|
| `model` | `str` | Yes | - | Model id input |

### Return Shape

Returns a model-like dict:

- `id`
- `object` (`"model"`)
- `owned_by` (`"oauth-codex"`)
- `capabilities` (dict from `models.capabilities`)

### Error Cases

- Same practical behavior as `models.capabilities`.

### Behavior Notes

- This method is synthesized from capability mapping, not fetched from live `/models/{id}` endpoint.

### Runnable Usage Snippets

```python
model_obj = client.models.retrieve("gpt-5.3-codex")
print(model_obj["id"], model_obj["capabilities"])
```

### Pitfalls / Troubleshooting

- Do not assume `owned_by` reflects upstream ownership metadata.

## `models.list`

### Sync / Async / Module-level Signatures

```python
client.models.list() -> dict
await client.models.list() -> dict
oauth_codex.models.list()
```

### Parameters

- No parameters.

### Return Shape

- Dict with `object="list"` and `data` containing model-like entries.

### Error Cases

- Same practical behavior as `models.retrieve`.

### Behavior Notes

- Current implementation returns a representative list containing `gpt-5.3-codex`-style entry.

### Runnable Usage Snippets

```python
models_out = client.models.list()
print(models_out["object"], len(models_out["data"]))
```

### Pitfalls / Troubleshooting

- Do not treat this as a complete catalog of all upstream models.

## `models.delete` (Unsupported)

### Sync / Async / Module-level Signatures

```python
client.models.delete(...)
await client.models.delete(...)
oauth_codex.models.delete(...)
```

### Error Cases

- Always raises:

```python
NotSupportedError(code="not_supported")
```

### Behavior Notes

- Method exists for OpenAI-style surface parity.
