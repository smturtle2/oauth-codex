[English](../../en/methods/responses.md) | [한국어](responses.md)

# Responses 메서드

## 지원 메서드

- `responses.create(...)`
- `responses.stream(...)`
- `responses.input_tokens.count(...)`

## `responses.create`

```python
resp = client.responses.create(
    model="gpt-5.3-codex",
    input="hello",
)
print(resp.id)
print(resp.output_text)
```

## 스트리밍

```python
for event in client.responses.stream(model="gpt-5.3-codex", input="hello"):
    if event.type == "text_delta" and event.delta:
        print(event.delta, end="")
```

## 입력 토큰 수 계산

```python
count = client.responses.input_tokens.count(model="gpt-5.3-codex", input="hello")
print(count.input_tokens)
```
