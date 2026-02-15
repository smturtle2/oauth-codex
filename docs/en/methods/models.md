[English](models.md) | [한국어](../../ko/methods/models.md)

# Models Methods

## Supported methods

- `models.capabilities(model)`
- `models.retrieve(model)`
- `models.list()`

## Example

```python
caps = client.models.capabilities("gpt-5.3-codex")
print(caps.supports_tools)

model = client.models.retrieve("gpt-5.3-codex")
print(model["id"])

models = client.models.list()
print(models["object"])
```
