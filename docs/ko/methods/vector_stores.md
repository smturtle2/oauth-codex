[English](../../en/methods/vector_stores.md) | [한국어](vector_stores.md)

# Vector Stores 메서드

## 루트 리소스 지원 메서드

- `vector_stores.create`
- `vector_stores.retrieve`
- `vector_stores.update`
- `vector_stores.list`
- `vector_stores.delete`
- `vector_stores.search`

## 하위 리소스 지원 메서드

- `vector_stores.files`: `create`, `create_and_poll`, `retrieve`, `list`, `delete`, `content`, `poll`, `upload`, `upload_and_poll`
- `vector_stores.file_batches`: `create`, `create_and_poll`, `retrieve`, `list_files`, `cancel`, `poll`, `upload_and_poll`

## 예시

```python
vs = client.vector_stores.create(name="docs", file_ids=[])
results = client.vector_stores.search(vs.id, query="oauth")
print(results["object"])
```
