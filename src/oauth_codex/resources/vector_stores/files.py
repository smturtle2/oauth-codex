from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._unsupported import raise_unsupported
from .._wrappers import (
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
)
from ...types.vector_stores import VectorStoreFile


def _to_vs_file(*, vector_store_id: str, file_id: str, status: str = "completed") -> VectorStoreFile:
    return VectorStoreFile(
        id=file_id,
        vector_store_id=vector_store_id,
        status=status,
        created_at=int(time.time()),
    )


class Files(SyncAPIResource):
    def create(self, vector_store_id: str, *, file_id: str, **_: Any) -> VectorStoreFile:
        if self._client._engine._is_codex_profile():
            current = self._client._engine.vector_store_request(
                method="GET",
                path=f"/vector_stores/{vector_store_id}",
                payload={},
            )
            file_ids = [item for item in current.get("file_ids", []) if isinstance(item, str)]
            if file_id not in file_ids:
                file_ids.append(file_id)
                self._client._engine.vector_store_request(
                    method="POST",
                    path=f"/vector_stores/{vector_store_id}",
                    payload={"file_ids": file_ids},
                )
            return _to_vs_file(vector_store_id=vector_store_id, file_id=file_id)

        out = self._client._engine._request_json_sync(
            path=f"/vector_stores/{vector_store_id}/files",
            payload={"file_id": file_id},
            method="POST",
        )
        return _to_vs_file(
            vector_store_id=vector_store_id,
            file_id=str(out.get("id", file_id)),
            status=str(out.get("status", "completed")),
        )

    def create_and_poll(self, vector_store_id: str, *, file_id: str, **kwargs: Any) -> VectorStoreFile:
        return self.create(vector_store_id, file_id=file_id, **kwargs)

    def retrieve(self, vector_store_id: str, file_id: str, **_: Any) -> VectorStoreFile:
        if self._client._engine._is_codex_profile():
            store = self._client._engine.vector_store_request(
                method="GET",
                path=f"/vector_stores/{vector_store_id}",
                payload={},
            )
            ids = [item for item in store.get("file_ids", []) if isinstance(item, str)]
            if file_id not in ids:
                raise KeyError(f"file {file_id} not in vector store {vector_store_id}")
            return _to_vs_file(vector_store_id=vector_store_id, file_id=file_id)

        out = self._client._engine._request_json_sync(
            path=f"/vector_stores/{vector_store_id}/files/{file_id}",
            payload={},
            method="GET",
        )
        return _to_vs_file(
            vector_store_id=vector_store_id,
            file_id=str(out.get("id", file_id)),
            status=str(out.get("status", "completed")),
        )

    def list(self, vector_store_id: str, **_: Any) -> dict[str, Any]:
        if self._client._engine._is_codex_profile():
            store = self._client._engine.vector_store_request(
                method="GET",
                path=f"/vector_stores/{vector_store_id}",
                payload={},
            )
            ids = [item for item in store.get("file_ids", []) if isinstance(item, str)]
            return {
                "object": "list",
                "data": [_to_vs_file(vector_store_id=vector_store_id, file_id=file_id).to_dict() for file_id in ids],
                "has_more": False,
            }

        out = self._client._engine._request_json_sync(
            path=f"/vector_stores/{vector_store_id}/files",
            payload={},
            method="GET",
        )
        data = out.get("data")
        if isinstance(data, list):
            out = {
                **out,
                "data": [
                    _to_vs_file(
                        vector_store_id=vector_store_id,
                        file_id=str(item.get("id", "")),
                        status=str(item.get("status", "completed")),
                    ).to_dict()
                    for item in data
                    if isinstance(item, dict)
                ],
            }
        return out

    def delete(self, vector_store_id: str, file_id: str, **_: Any) -> dict[str, Any]:
        if self._client._engine._is_codex_profile():
            current = self._client._engine.vector_store_request(
                method="GET",
                path=f"/vector_stores/{vector_store_id}",
                payload={},
            )
            file_ids = [item for item in current.get("file_ids", []) if isinstance(item, str) and item != file_id]
            self._client._engine.vector_store_request(
                method="POST",
                path=f"/vector_stores/{vector_store_id}",
                payload={"file_ids": file_ids},
            )
            return {"id": file_id, "object": "vector_store.file.deleted", "deleted": True}

        out = self._client._engine._request_json_sync(
            path=f"/vector_stores/{vector_store_id}/files/{file_id}",
            payload={},
            method="DELETE",
        )
        return {
            "id": str(out.get("id", file_id)),
            "object": str(out.get("object", "vector_store.file.deleted")),
            "deleted": bool(out.get("deleted", True)),
        }

    def content(self, vector_store_id: str, file_id: str, **kwargs: Any) -> bytes:
        _ = vector_store_id
        return self._client.files.content(file_id, **kwargs)

    def update(self, *_: Any, **__: Any) -> VectorStoreFile:
        raise_unsupported("vector_stores.files.update")

    def poll(self, vector_store_id: str, file_id: str, **kwargs: Any) -> VectorStoreFile:
        return self.retrieve(vector_store_id, file_id, **kwargs)

    def upload(self, vector_store_id: str, *, file: Any, purpose: str = "assistants", **kwargs: Any) -> VectorStoreFile:
        uploaded = self._client.files.create(file=file, purpose=purpose)
        return self.create(vector_store_id, file_id=uploaded.id, **kwargs)

    def upload_and_poll(
        self,
        vector_store_id: str,
        *,
        file: Any,
        purpose: str = "assistants",
        **kwargs: Any,
    ) -> VectorStoreFile:
        return self.upload(vector_store_id, file=file, purpose=purpose, **kwargs)

    @property
    def with_raw_response(self) -> FilesWithRawResponse:
        return FilesWithRawResponse(self)

    @property
    def with_streaming_response(self) -> FilesWithStreamingResponse:
        return FilesWithStreamingResponse(self)


class AsyncFiles(AsyncAPIResource):
    async def create(self, vector_store_id: str, *, file_id: str, **_: Any) -> VectorStoreFile:
        if self._client._engine._is_codex_profile():
            current = await self._client._engine.avector_store_request(
                method="GET",
                path=f"/vector_stores/{vector_store_id}",
                payload={},
            )
            file_ids = [item for item in current.get("file_ids", []) if isinstance(item, str)]
            if file_id not in file_ids:
                file_ids.append(file_id)
                await self._client._engine.avector_store_request(
                    method="POST",
                    path=f"/vector_stores/{vector_store_id}",
                    payload={"file_ids": file_ids},
                )
            return _to_vs_file(vector_store_id=vector_store_id, file_id=file_id)

        out = await self._client._engine._request_json_async(
            path=f"/vector_stores/{vector_store_id}/files",
            payload={"file_id": file_id},
            method="POST",
        )
        return _to_vs_file(
            vector_store_id=vector_store_id,
            file_id=str(out.get("id", file_id)),
            status=str(out.get("status", "completed")),
        )

    async def create_and_poll(self, vector_store_id: str, *, file_id: str, **kwargs: Any) -> VectorStoreFile:
        return await self.create(vector_store_id, file_id=file_id, **kwargs)

    async def retrieve(self, vector_store_id: str, file_id: str, **_: Any) -> VectorStoreFile:
        if self._client._engine._is_codex_profile():
            store = await self._client._engine.avector_store_request(
                method="GET",
                path=f"/vector_stores/{vector_store_id}",
                payload={},
            )
            ids = [item for item in store.get("file_ids", []) if isinstance(item, str)]
            if file_id not in ids:
                raise KeyError(f"file {file_id} not in vector store {vector_store_id}")
            return _to_vs_file(vector_store_id=vector_store_id, file_id=file_id)

        out = await self._client._engine._request_json_async(
            path=f"/vector_stores/{vector_store_id}/files/{file_id}",
            payload={},
            method="GET",
        )
        return _to_vs_file(
            vector_store_id=vector_store_id,
            file_id=str(out.get("id", file_id)),
            status=str(out.get("status", "completed")),
        )

    async def list(self, vector_store_id: str, **_: Any) -> dict[str, Any]:
        if self._client._engine._is_codex_profile():
            store = await self._client._engine.avector_store_request(
                method="GET",
                path=f"/vector_stores/{vector_store_id}",
                payload={},
            )
            ids = [item for item in store.get("file_ids", []) if isinstance(item, str)]
            return {
                "object": "list",
                "data": [_to_vs_file(vector_store_id=vector_store_id, file_id=file_id).to_dict() for file_id in ids],
                "has_more": False,
            }

        out = await self._client._engine._request_json_async(
            path=f"/vector_stores/{vector_store_id}/files",
            payload={},
            method="GET",
        )
        data = out.get("data")
        if isinstance(data, list):
            out = {
                **out,
                "data": [
                    _to_vs_file(
                        vector_store_id=vector_store_id,
                        file_id=str(item.get("id", "")),
                        status=str(item.get("status", "completed")),
                    ).to_dict()
                    for item in data
                    if isinstance(item, dict)
                ],
            }
        return out

    async def delete(self, vector_store_id: str, file_id: str, **_: Any) -> dict[str, Any]:
        if self._client._engine._is_codex_profile():
            current = await self._client._engine.avector_store_request(
                method="GET",
                path=f"/vector_stores/{vector_store_id}",
                payload={},
            )
            file_ids = [item for item in current.get("file_ids", []) if isinstance(item, str) and item != file_id]
            await self._client._engine.avector_store_request(
                method="POST",
                path=f"/vector_stores/{vector_store_id}",
                payload={"file_ids": file_ids},
            )
            return {"id": file_id, "object": "vector_store.file.deleted", "deleted": True}

        out = await self._client._engine._request_json_async(
            path=f"/vector_stores/{vector_store_id}/files/{file_id}",
            payload={},
            method="DELETE",
        )
        return {
            "id": str(out.get("id", file_id)),
            "object": str(out.get("object", "vector_store.file.deleted")),
            "deleted": bool(out.get("deleted", True)),
        }

    async def content(self, vector_store_id: str, file_id: str, **kwargs: Any) -> bytes:
        _ = vector_store_id
        return await self._client.files.content(file_id, **kwargs)

    async def update(self, *_: Any, **__: Any) -> VectorStoreFile:
        raise_unsupported("vector_stores.files.update")

    async def poll(self, vector_store_id: str, file_id: str, **kwargs: Any) -> VectorStoreFile:
        return await self.retrieve(vector_store_id, file_id, **kwargs)

    async def upload(self, vector_store_id: str, *, file: Any, purpose: str = "assistants", **kwargs: Any) -> VectorStoreFile:
        uploaded = await self._client.files.create(file=file, purpose=purpose)
        return await self.create(vector_store_id, file_id=uploaded.id, **kwargs)

    async def upload_and_poll(
        self,
        vector_store_id: str,
        *,
        file: Any,
        purpose: str = "assistants",
        **kwargs: Any,
    ) -> VectorStoreFile:
        return await self.upload(vector_store_id, file=file, purpose=purpose, **kwargs)

    @property
    def with_raw_response(self) -> AsyncFilesWithRawResponse:
        return AsyncFilesWithRawResponse(self)

    @property
    def with_streaming_response(self) -> AsyncFilesWithStreamingResponse:
        return AsyncFilesWithStreamingResponse(self)


class FilesWithRawResponse:
    def __init__(self, files: Files) -> None:
        self.create = to_raw_response_wrapper(files.create)
        self.create_and_poll = to_raw_response_wrapper(files.create_and_poll)
        self.retrieve = to_raw_response_wrapper(files.retrieve)
        self.list = to_raw_response_wrapper(files.list)
        self.delete = to_raw_response_wrapper(files.delete)
        self.content = to_raw_response_wrapper(files.content)
        self.update = to_raw_response_wrapper(files.update)
        self.poll = to_raw_response_wrapper(files.poll)
        self.upload = to_raw_response_wrapper(files.upload)
        self.upload_and_poll = to_raw_response_wrapper(files.upload_and_poll)


class AsyncFilesWithRawResponse:
    def __init__(self, files: AsyncFiles) -> None:
        self.create = async_to_raw_response_wrapper(files.create)
        self.create_and_poll = async_to_raw_response_wrapper(files.create_and_poll)
        self.retrieve = async_to_raw_response_wrapper(files.retrieve)
        self.list = async_to_raw_response_wrapper(files.list)
        self.delete = async_to_raw_response_wrapper(files.delete)
        self.content = async_to_raw_response_wrapper(files.content)
        self.update = async_to_raw_response_wrapper(files.update)
        self.poll = async_to_raw_response_wrapper(files.poll)
        self.upload = async_to_raw_response_wrapper(files.upload)
        self.upload_and_poll = async_to_raw_response_wrapper(files.upload_and_poll)


class FilesWithStreamingResponse:
    def __init__(self, files: Files) -> None:
        self.create = to_streamed_response_wrapper(files.create)
        self.create_and_poll = to_streamed_response_wrapper(files.create_and_poll)
        self.retrieve = to_streamed_response_wrapper(files.retrieve)
        self.list = to_streamed_response_wrapper(files.list)
        self.delete = to_streamed_response_wrapper(files.delete)
        self.content = to_streamed_response_wrapper(files.content)
        self.update = to_streamed_response_wrapper(files.update)
        self.poll = to_streamed_response_wrapper(files.poll)
        self.upload = to_streamed_response_wrapper(files.upload)
        self.upload_and_poll = to_streamed_response_wrapper(files.upload_and_poll)


class AsyncFilesWithStreamingResponse:
    def __init__(self, files: AsyncFiles) -> None:
        self.create = async_to_streamed_response_wrapper(files.create)
        self.create_and_poll = async_to_streamed_response_wrapper(files.create_and_poll)
        self.retrieve = async_to_streamed_response_wrapper(files.retrieve)
        self.list = async_to_streamed_response_wrapper(files.list)
        self.delete = async_to_streamed_response_wrapper(files.delete)
        self.content = async_to_streamed_response_wrapper(files.content)
        self.update = async_to_streamed_response_wrapper(files.update)
        self.poll = async_to_streamed_response_wrapper(files.poll)
        self.upload = async_to_streamed_response_wrapper(files.upload)
        self.upload_and_poll = async_to_streamed_response_wrapper(files.upload_and_poll)
