[English](../../en/methods/models.md) | [한국어](models.md)

# Models 메서드

이 문서는 `oauth-codex`의 `models` 런타임 메서드를 설명합니다.

## Method Summary

| 메서드 | 지원 여부 | 비고 |
|---|---|---|
| `models.capabilities(model)` | 지원 | capability flag 반환 |
| `models.retrieve(model)` | 지원 | capability 포함 model-like object 반환 |
| `models.list()` | 지원 | 현재 대표 엔트리 기반 list 반환 |
| `models.delete(...)` | 미지원 | `NotSupportedError(code="not_supported")` |

## `models.capabilities`

### Sync / Async / Module-level Signatures

```python
client.models.capabilities(model: str) -> ModelCapabilities
await client.models.capabilities(model: str) -> ModelCapabilities
oauth_codex.models.capabilities(model)
```

### Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 검증/동작 |
|---|---|---|---|---|
| `model` | `str` | 예 | - | 모델 ID |

### Return Shape

`ModelCapabilities` 반환:

- `supports_reasoning: bool`
- `supports_tools: bool`
- `supports_store: bool`
- `supports_response_format: bool`

### Error Cases

| 예외 | 발생 조건 |
|---|---|
| `SDKRequestError` | 내부 엔진 경로에서 예외 상황 발생 시 |

### Behavior Notes

- `supports_store`는 profile에 따라 달라집니다.
  - Codex profile: `False`
  - non-Codex profile: `True`

### Runnable Usage Snippets

```python
caps = client.models.capabilities("gpt-5.3-codex")
print(caps.supports_tools, caps.supports_store)
```

### Pitfalls / Troubleshooting

- capability 값은 SDK 매핑 값이며, 실시간 `/models` 원격 계약 자체를 의미하지는 않습니다.

## `models.retrieve`

### Sync / Async / Module-level Signatures

```python
client.models.retrieve(model: str) -> dict
await client.models.retrieve(model: str) -> dict
oauth_codex.models.retrieve(model)
```

### Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 검증/동작 |
|---|---|---|---|---|
| `model` | `str` | 예 | - | 모델 ID |

### Return Shape

model-like dict 반환:

- `id`
- `object` (`"model"`)
- `owned_by` (`"oauth-codex"`)
- `capabilities` (`models.capabilities` dict)

### Error Cases

- 실질적으로 `models.capabilities`와 동일한 실패 조건을 가집니다.

### Behavior Notes

- 이 메서드는 실시간 `/models/{id}` 조회가 아니라 capability 매핑으로 구성됩니다.

### Runnable Usage Snippets

```python
model_obj = client.models.retrieve("gpt-5.3-codex")
print(model_obj["id"], model_obj["capabilities"])
```

### Pitfalls / Troubleshooting

- `owned_by` 값을 업스트림 실제 소유 메타데이터로 가정하지 마세요.

## `models.list`

### Sync / Async / Module-level Signatures

```python
client.models.list() -> dict
await client.models.list() -> dict
oauth_codex.models.list()
```

### Parameters

- 없음.

### Return Shape

- `object="list"`와 `data`를 포함하는 dict.

### Error Cases

- 실질적으로 `models.retrieve`와 동일.

### Behavior Notes

- 현재 구현은 `gpt-5.3-codex` 중심 대표 엔트리를 반환합니다.

### Runnable Usage Snippets

```python
models_out = client.models.list()
print(models_out["object"], len(models_out["data"]))
```

### Pitfalls / Troubleshooting

- 업스트림 전체 모델 카탈로그를 모두 제공한다고 가정하면 안 됩니다.

## `models.delete` (미지원)

### Sync / Async / Module-level Signatures

```python
client.models.delete(...)
await client.models.delete(...)
oauth_codex.models.delete(...)
```

### Error Cases

항상 아래 예외를 발생시킵니다.

```python
NotSupportedError(code="not_supported")
```

### Behavior Notes

- OpenAI 스타일 표면 호환성을 위해 메서드가 노출되어 있습니다.
