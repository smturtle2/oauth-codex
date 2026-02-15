[English](responses.md) | [한국어](../../ko/methods/responses.md)

# Responses Methods

## Supported methods

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

## Streaming

```python
for event in client.responses.stream(model="gpt-5.3-codex", input="hello"):
    if event.type == "text_delta" and event.delta:
        print(event.delta, end="")
```

## Input token count

```python
count = client.responses.input_tokens.count(model="gpt-5.3-codex", input="hello")
print(count.input_tokens)
```
