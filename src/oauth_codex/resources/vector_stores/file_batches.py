from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._wrappers import (
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
)
from ...types.vector_stores import VectorStoreFileBatch


def _make_batch(vector_store_id: str, batch_id: str | None = None, status: str = "completed") -> VectorStoreFileBatch:
    return VectorStoreFileBatch(
        id=batch_id or f"vsfb_{uuid.uuid4().hex}",
        vector_store_id=vector_store_id,
        status=status,
        created_at=int(time.time()),
        file_counts={"in_progress": 0, "completed": 0, "failed": 0, "cancelled": 0, "total": 0},
    )


class FileBatches(SyncAPIResource):
    def create(self, vector_store_id: str, *, file_ids: list[str], **_: Any) -> VectorStoreFileBatch:
        batch = _make_batch(vector_store_id)
        self._client._vector_file_batches[batch.id] = {
            "vector_store_id": vector_store_id,
            "status": "completed",
            "file_ids": list(file_ids),
        }
        vs = self._client.vector_stores.files
        for file_id in file_ids:
            vs.create(vector_store_id, file_id=file_id)
        return batch

    def create_and_poll(self, vector_store_id: str, *, file_ids: list[str], **kwargs: Any) -> VectorStoreFileBatch:
        return self.create(vector_store_id, file_ids=file_ids, **kwargs)

    def retrieve(self, vector_store_id: str, batch_id: str, **_: Any) -> VectorStoreFileBatch:
        info = self._client._vector_file_batches.get(batch_id)
        if not info:
            return _make_batch(vector_store_id, batch_id=batch_id, status="completed")
        return _make_batch(vector_store_id, batch_id=batch_id, status=str(info.get("status", "completed")))

    def list_files(self, vector_store_id: str, batch_id: str, **_: Any) -> dict[str, Any]:
        _ = batch_id
        return self._client.vector_stores.files.list(vector_store_id)

    def cancel(self, vector_store_id: str, batch_id: str, **_: Any) -> VectorStoreFileBatch:
        _ = vector_store_id
        info = self._client._vector_file_batches.get(batch_id)
        if info:
            info["status"] = "cancelled"
        return _make_batch(vector_store_id, batch_id=batch_id, status="cancelled")

    def poll(self, vector_store_id: str, batch_id: str, **kwargs: Any) -> VectorStoreFileBatch:
        return self.retrieve(vector_store_id, batch_id, **kwargs)

    def upload_and_poll(self, vector_store_id: str, *, files: list[Any], purpose: str = "assistants", **_: Any) -> VectorStoreFileBatch:
        uploaded_ids: list[str] = []
        for file in files:
            item = self._client.files.create(file=file, purpose=purpose)
            uploaded_ids.append(item.id)
        return self.create(vector_store_id, file_ids=uploaded_ids)

    @property
    def with_raw_response(self) -> FileBatchesWithRawResponse:
        return FileBatchesWithRawResponse(self)

    @property
    def with_streaming_response(self) -> FileBatchesWithStreamingResponse:
        return FileBatchesWithStreamingResponse(self)


class AsyncFileBatches(AsyncAPIResource):
    async def create(self, vector_store_id: str, *, file_ids: list[str], **_: Any) -> VectorStoreFileBatch:
        batch = _make_batch(vector_store_id)
        self._client._vector_file_batches[batch.id] = {
            "vector_store_id": vector_store_id,
            "status": "completed",
            "file_ids": list(file_ids),
        }
        vs = self._client.vector_stores.files
        for file_id in file_ids:
            await vs.create(vector_store_id, file_id=file_id)
        return batch

    async def create_and_poll(self, vector_store_id: str, *, file_ids: list[str], **kwargs: Any) -> VectorStoreFileBatch:
        return await self.create(vector_store_id, file_ids=file_ids, **kwargs)

    async def retrieve(self, vector_store_id: str, batch_id: str, **_: Any) -> VectorStoreFileBatch:
        info = self._client._vector_file_batches.get(batch_id)
        if not info:
            return _make_batch(vector_store_id, batch_id=batch_id, status="completed")
        return _make_batch(vector_store_id, batch_id=batch_id, status=str(info.get("status", "completed")))

    async def list_files(self, vector_store_id: str, batch_id: str, **_: Any) -> dict[str, Any]:
        _ = batch_id
        return await self._client.vector_stores.files.list(vector_store_id)

    async def cancel(self, vector_store_id: str, batch_id: str, **_: Any) -> VectorStoreFileBatch:
        _ = vector_store_id
        info = self._client._vector_file_batches.get(batch_id)
        if info:
            info["status"] = "cancelled"
        return _make_batch(vector_store_id, batch_id=batch_id, status="cancelled")

    async def poll(self, vector_store_id: str, batch_id: str, **kwargs: Any) -> VectorStoreFileBatch:
        return await self.retrieve(vector_store_id, batch_id, **kwargs)

    async def upload_and_poll(
        self,
        vector_store_id: str,
        *,
        files: list[Any],
        purpose: str = "assistants",
        **_: Any,
    ) -> VectorStoreFileBatch:
        uploaded_ids: list[str] = []
        for file in files:
            item = await self._client.files.create(file=file, purpose=purpose)
            uploaded_ids.append(item.id)
        return await self.create(vector_store_id, file_ids=uploaded_ids)

    @property
    def with_raw_response(self) -> AsyncFileBatchesWithRawResponse:
        return AsyncFileBatchesWithRawResponse(self)

    @property
    def with_streaming_response(self) -> AsyncFileBatchesWithStreamingResponse:
        return AsyncFileBatchesWithStreamingResponse(self)


class FileBatchesWithRawResponse:
    def __init__(self, file_batches: FileBatches) -> None:
        self.create = to_raw_response_wrapper(file_batches.create)
        self.create_and_poll = to_raw_response_wrapper(file_batches.create_and_poll)
        self.retrieve = to_raw_response_wrapper(file_batches.retrieve)
        self.list_files = to_raw_response_wrapper(file_batches.list_files)
        self.cancel = to_raw_response_wrapper(file_batches.cancel)
        self.poll = to_raw_response_wrapper(file_batches.poll)
        self.upload_and_poll = to_raw_response_wrapper(file_batches.upload_and_poll)


class AsyncFileBatchesWithRawResponse:
    def __init__(self, file_batches: AsyncFileBatches) -> None:
        self.create = async_to_raw_response_wrapper(file_batches.create)
        self.create_and_poll = async_to_raw_response_wrapper(file_batches.create_and_poll)
        self.retrieve = async_to_raw_response_wrapper(file_batches.retrieve)
        self.list_files = async_to_raw_response_wrapper(file_batches.list_files)
        self.cancel = async_to_raw_response_wrapper(file_batches.cancel)
        self.poll = async_to_raw_response_wrapper(file_batches.poll)
        self.upload_and_poll = async_to_raw_response_wrapper(file_batches.upload_and_poll)


class FileBatchesWithStreamingResponse:
    def __init__(self, file_batches: FileBatches) -> None:
        self.create = to_streamed_response_wrapper(file_batches.create)
        self.create_and_poll = to_streamed_response_wrapper(file_batches.create_and_poll)
        self.retrieve = to_streamed_response_wrapper(file_batches.retrieve)
        self.list_files = to_streamed_response_wrapper(file_batches.list_files)
        self.cancel = to_streamed_response_wrapper(file_batches.cancel)
        self.poll = to_streamed_response_wrapper(file_batches.poll)
        self.upload_and_poll = to_streamed_response_wrapper(file_batches.upload_and_poll)


class AsyncFileBatchesWithStreamingResponse:
    def __init__(self, file_batches: AsyncFileBatches) -> None:
        self.create = async_to_streamed_response_wrapper(file_batches.create)
        self.create_and_poll = async_to_streamed_response_wrapper(file_batches.create_and_poll)
        self.retrieve = async_to_streamed_response_wrapper(file_batches.retrieve)
        self.list_files = async_to_streamed_response_wrapper(file_batches.list_files)
        self.cancel = async_to_streamed_response_wrapper(file_batches.cancel)
        self.poll = async_to_streamed_response_wrapper(file_batches.poll)
        self.upload_and_poll = async_to_streamed_response_wrapper(file_batches.upload_and_poll)
