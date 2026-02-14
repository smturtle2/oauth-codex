from __future__ import annotations

from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._wrappers import (
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
)
from ...types.vector_stores import VectorStore, VectorStoreDeleted
from .file_batches import (
    AsyncFileBatches,
    AsyncFileBatchesWithRawResponse,
    AsyncFileBatchesWithStreamingResponse,
    FileBatches,
    FileBatchesWithRawResponse,
    FileBatchesWithStreamingResponse,
)
from .files import (
    AsyncFiles,
    AsyncFilesWithRawResponse,
    AsyncFilesWithStreamingResponse,
    Files,
    FilesWithRawResponse,
    FilesWithStreamingResponse,
)


def _to_vector_store(payload: dict[str, Any]) -> VectorStore:
    return VectorStore(
        id=str(payload.get("id", "")),
        object=str(payload.get("object", "vector_store")),
        created_at=payload.get("created_at") if isinstance(payload.get("created_at"), int) else None,
        name=payload.get("name") if isinstance(payload.get("name"), str) else None,
        metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
        file_ids=[item for item in payload.get("file_ids", []) if isinstance(item, str)],
        status=payload.get("status") if isinstance(payload.get("status"), str) else None,
        usage_bytes=payload.get("usage_bytes") if isinstance(payload.get("usage_bytes"), int) else None,
        file_counts=payload.get("file_counts") if isinstance(payload.get("file_counts"), dict) else None,
        expires_after=payload.get("expires_after") if isinstance(payload.get("expires_after"), dict) else None,
    )


class VectorStores(SyncAPIResource):
    @property
    def files(self) -> Files:
        return Files(self._client)

    @property
    def file_batches(self) -> FileBatches:
        return FileBatches(self._client)

    def create(self, **payload: Any) -> VectorStore:
        out = self._client._engine.vector_store_request(method="POST", path="/vector_stores", payload=payload)
        return _to_vector_store(out)

    def retrieve(self, vector_store_id: str, **_: Any) -> VectorStore:
        out = self._client._engine.vector_store_request(
            method="GET",
            path=f"/vector_stores/{vector_store_id}",
            payload={},
        )
        return _to_vector_store(out)

    def update(self, vector_store_id: str, **payload: Any) -> VectorStore:
        out = self._client._engine.vector_store_request(
            method="POST",
            path=f"/vector_stores/{vector_store_id}",
            payload=payload,
        )
        return _to_vector_store(out)

    def list(self, **params: Any) -> dict[str, Any]:
        out = self._client._engine.vector_store_request(
            method="GET",
            path="/vector_stores",
            payload=params,
        )
        data = out.get("data")
        if isinstance(data, list):
            out = {
                **out,
                "data": [_to_vector_store(item).to_dict() for item in data if isinstance(item, dict)],
            }
        return out

    def delete(self, vector_store_id: str, **_: Any) -> VectorStoreDeleted:
        out = self._client._engine.vector_store_request(
            method="DELETE",
            path=f"/vector_stores/{vector_store_id}",
            payload={},
        )
        return VectorStoreDeleted(
            id=str(out.get("id", vector_store_id)),
            object=str(out.get("object", "vector_store.deleted")),
            deleted=bool(out.get("deleted", True)),
        )

    def search(self, vector_store_id: str, *, query: str, **payload: Any) -> dict[str, Any]:
        return self._client._engine.vector_store_request(
            method="POST",
            path=f"/vector_stores/{vector_store_id}/search",
            payload={"query": query, **payload},
        )

    @property
    def with_raw_response(self) -> VectorStoresWithRawResponse:
        return VectorStoresWithRawResponse(self)

    @property
    def with_streaming_response(self) -> VectorStoresWithStreamingResponse:
        return VectorStoresWithStreamingResponse(self)


class AsyncVectorStores(AsyncAPIResource):
    @property
    def files(self) -> AsyncFiles:
        return AsyncFiles(self._client)

    @property
    def file_batches(self) -> AsyncFileBatches:
        return AsyncFileBatches(self._client)

    async def create(self, **payload: Any) -> VectorStore:
        out = await self._client._engine.avector_store_request(method="POST", path="/vector_stores", payload=payload)
        return _to_vector_store(out)

    async def retrieve(self, vector_store_id: str, **_: Any) -> VectorStore:
        out = await self._client._engine.avector_store_request(
            method="GET",
            path=f"/vector_stores/{vector_store_id}",
            payload={},
        )
        return _to_vector_store(out)

    async def update(self, vector_store_id: str, **payload: Any) -> VectorStore:
        out = await self._client._engine.avector_store_request(
            method="POST",
            path=f"/vector_stores/{vector_store_id}",
            payload=payload,
        )
        return _to_vector_store(out)

    async def list(self, **params: Any) -> dict[str, Any]:
        out = await self._client._engine.avector_store_request(
            method="GET",
            path="/vector_stores",
            payload=params,
        )
        data = out.get("data")
        if isinstance(data, list):
            out = {
                **out,
                "data": [_to_vector_store(item).to_dict() for item in data if isinstance(item, dict)],
            }
        return out

    async def delete(self, vector_store_id: str, **_: Any) -> VectorStoreDeleted:
        out = await self._client._engine.avector_store_request(
            method="DELETE",
            path=f"/vector_stores/{vector_store_id}",
            payload={},
        )
        return VectorStoreDeleted(
            id=str(out.get("id", vector_store_id)),
            object=str(out.get("object", "vector_store.deleted")),
            deleted=bool(out.get("deleted", True)),
        )

    async def search(self, vector_store_id: str, *, query: str, **payload: Any) -> dict[str, Any]:
        return await self._client._engine.avector_store_request(
            method="POST",
            path=f"/vector_stores/{vector_store_id}/search",
            payload={"query": query, **payload},
        )

    @property
    def with_raw_response(self) -> AsyncVectorStoresWithRawResponse:
        return AsyncVectorStoresWithRawResponse(self)

    @property
    def with_streaming_response(self) -> AsyncVectorStoresWithStreamingResponse:
        return AsyncVectorStoresWithStreamingResponse(self)


class VectorStoresWithRawResponse:
    def __init__(self, vector_stores: VectorStores) -> None:
        self.create = to_raw_response_wrapper(vector_stores.create)
        self.retrieve = to_raw_response_wrapper(vector_stores.retrieve)
        self.update = to_raw_response_wrapper(vector_stores.update)
        self.list = to_raw_response_wrapper(vector_stores.list)
        self.delete = to_raw_response_wrapper(vector_stores.delete)
        self.search = to_raw_response_wrapper(vector_stores.search)
        self.files = FilesWithRawResponse(vector_stores.files)
        self.file_batches = FileBatchesWithRawResponse(vector_stores.file_batches)


class AsyncVectorStoresWithRawResponse:
    def __init__(self, vector_stores: AsyncVectorStores) -> None:
        self.create = async_to_raw_response_wrapper(vector_stores.create)
        self.retrieve = async_to_raw_response_wrapper(vector_stores.retrieve)
        self.update = async_to_raw_response_wrapper(vector_stores.update)
        self.list = async_to_raw_response_wrapper(vector_stores.list)
        self.delete = async_to_raw_response_wrapper(vector_stores.delete)
        self.search = async_to_raw_response_wrapper(vector_stores.search)
        self.files = AsyncFilesWithRawResponse(vector_stores.files)
        self.file_batches = AsyncFileBatchesWithRawResponse(vector_stores.file_batches)


class VectorStoresWithStreamingResponse:
    def __init__(self, vector_stores: VectorStores) -> None:
        self.create = to_streamed_response_wrapper(vector_stores.create)
        self.retrieve = to_streamed_response_wrapper(vector_stores.retrieve)
        self.update = to_streamed_response_wrapper(vector_stores.update)
        self.list = to_streamed_response_wrapper(vector_stores.list)
        self.delete = to_streamed_response_wrapper(vector_stores.delete)
        self.search = to_streamed_response_wrapper(vector_stores.search)
        self.files = FilesWithStreamingResponse(vector_stores.files)
        self.file_batches = FileBatchesWithStreamingResponse(vector_stores.file_batches)


class AsyncVectorStoresWithStreamingResponse:
    def __init__(self, vector_stores: AsyncVectorStores) -> None:
        self.create = async_to_streamed_response_wrapper(vector_stores.create)
        self.retrieve = async_to_streamed_response_wrapper(vector_stores.retrieve)
        self.update = async_to_streamed_response_wrapper(vector_stores.update)
        self.list = async_to_streamed_response_wrapper(vector_stores.list)
        self.delete = async_to_streamed_response_wrapper(vector_stores.delete)
        self.search = async_to_streamed_response_wrapper(vector_stores.search)
        self.files = AsyncFilesWithStreamingResponse(vector_stores.files)
        self.file_batches = AsyncFileBatchesWithStreamingResponse(vector_stores.file_batches)
