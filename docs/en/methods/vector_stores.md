[English](vector_stores.md) | [한국어](../../ko/methods/vector_stores.md)

# Vector Stores Methods

## Supported root methods

- `vector_stores.create`
- `vector_stores.retrieve`
- `vector_stores.update`
- `vector_stores.list`
- `vector_stores.delete`
- `vector_stores.search`

## Supported subresources

- `vector_stores.files`: `create`, `create_and_poll`, `retrieve`, `list`, `delete`, `content`, `poll`, `upload`, `upload_and_poll`
- `vector_stores.file_batches`: `create`, `create_and_poll`, `retrieve`, `list_files`, `cancel`, `poll`, `upload_and_poll`

## Example

```python
vs = client.vector_stores.create(name="docs", file_ids=[])
results = client.vector_stores.search(vs.id, query="oauth")
print(results["object"])
```
