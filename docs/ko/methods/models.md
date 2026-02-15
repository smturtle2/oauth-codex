[English](../../en/methods/models.md) | [한국어](models.md)

# Models 메서드

## 지원 메서드

- `models.capabilities(model)`
- `models.retrieve(model)`
- `models.list()`

## 예시

```python
caps = client.models.capabilities("gpt-5.3-codex")
print(caps.supports_tools)

model = client.models.retrieve("gpt-5.3-codex")
print(model["id"])

models = client.models.list()
print(models["object"])
```
