from __future__ import annotations

import asyncio
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

from .._resource import AsyncAPIResource, SyncAPIResource
from ._wrappers import (
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
)
from ..types.file_deleted import FileDeleted
from ..types.file_object import FileObject


def _to_file_object(payload: dict[str, Any]) -> FileObject:
    return FileObject(
        id=str(payload.get("id", "")),
        object=str(payload.get("object", "file")),
        bytes=payload.get("bytes") if isinstance(payload.get("bytes"), int) else None,
        created_at=payload.get("created_at") if isinstance(payload.get("created_at"), int) else None,
        filename=payload.get("filename") if isinstance(payload.get("filename"), str) else None,
        purpose=payload.get("purpose") if isinstance(payload.get("purpose"), str) else None,
        metadata={
            k: v
            for k, v in payload.items()
            if k not in {"id", "object", "bytes", "created_at", "filename", "purpose"}
        }
        or None,
    )


class Files(SyncAPIResource):
    def create(self, *, file: Any, purpose: str, **metadata: Any) -> FileObject:
        out = self._client._engine.files_create(file=file, purpose=purpose, **metadata)
        return _to_file_object(out)

    def retrieve(self, file_id: str, **_: Any) -> FileObject:
        if self._client._engine._is_codex_profile():
            payload = self._client._engine._compat_store.get_file(file_id)
            return _to_file_object(payload)

        payload = self._client._engine._request_json_sync(path=f"/files/{file_id}", payload={}, method="GET")
        return _to_file_object(payload)

    def list(
        self,
        *,
        after: str | None = None,
        limit: int | None = None,
        order: str | None = None,
        purpose: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        if self._client._engine._is_codex_profile():
            data = self._client._engine._compat_store._load_files_index().get("data", [])
            items = [item for item in data if isinstance(item, dict)]
            if purpose:
                items = [item for item in items if item.get("purpose") == purpose]
            if order == "desc":
                items = list(reversed(items))
            if isinstance(limit, int) and limit > 0:
                items = items[:limit]
            return {
                "object": "list",
                "data": [_to_file_object(item).to_dict() for item in items],
                "after": after,
                "has_more": False,
            }

        query: dict[str, Any] = {}
        if after is not None:
            query["after"] = after
        if limit is not None:
            query["limit"] = limit
        if order is not None:
            query["order"] = order
        if purpose is not None:
            query["purpose"] = purpose
        out = self._client._engine._request_json_sync(
            path="/files",
            payload={},
            method="GET",
            extra_query=query or None,
        )
        data = out.get("data")
        if isinstance(data, list):
            out = {**out, "data": [_to_file_object(item).to_dict() for item in data if isinstance(item, dict)]}
        return out

    def delete(self, file_id: str, **_: Any) -> FileDeleted:
        if self._client._engine._is_codex_profile():
            store = self._client._engine._compat_store
            index = store._load_files_index()
            data = [item for item in index.get("data", []) if isinstance(item, dict)]
            kept = [item for item in data if item.get("id") != file_id]
            found = len(kept) != len(data)
            index["data"] = kept
            store._atomic_write_json(store.files_index_path, index)
            blob = store.files_blobs_dir / f"{file_id}.bin"
            blob.unlink(missing_ok=True)
            return FileDeleted(id=file_id, object="file.deleted", deleted=found)

        out = self._client._engine._request_json_sync(path=f"/files/{file_id}", payload={}, method="DELETE")
        return FileDeleted(
            id=str(out.get("id", file_id)),
            object=str(out.get("object", "file.deleted")),
            deleted=bool(out.get("deleted", True)),
        )

    def content(self, file_id: str, **_: Any) -> bytes:
        if self._client._engine._is_codex_profile():
            blob = self._client._engine._compat_store.files_blobs_dir / f"{file_id}.bin"
            if not blob.exists():
                raise KeyError(f"file {file_id} not found")
            return blob.read_bytes()

        tokens = self._client._engine._ensure_authenticated_sync()
        url = self._client._engine._resolve_request_url(f"/files/{file_id}/content")
        headers = self._client._engine._auth_headers(tokens)
        with httpx.Client(timeout=self._client.timeout) as http:
            response = http.get(url, headers=headers)
        if response.status_code >= 400:
            raise self._client._engine._build_sdk_request_error(response)
        return response.content

    def retrieve_content(self, file_id: str, **kwargs: Any) -> bytes:
        return self.content(file_id, **kwargs)

    def wait_for_processing(
        self,
        file_id: str,
        *,
        timeout: float = 60.0,
        poll_interval: float = 0.5,
        **_: Any,
    ) -> FileObject:
        start = time.time()
        while True:
            file_obj = self.retrieve(file_id)
            status = (file_obj.metadata or {}).get("status") if file_obj.metadata else None
            if status in {None, "processed", "completed"}:
                return file_obj
            if time.time() - start > timeout:
                return file_obj
            time.sleep(poll_interval)

    @property
    def with_raw_response(self) -> FilesWithRawResponse:
        return FilesWithRawResponse(self)

    @property
    def with_streaming_response(self) -> FilesWithStreamingResponse:
        return FilesWithStreamingResponse(self)


class AsyncFiles(AsyncAPIResource):
    async def create(self, *, file: Any, purpose: str, **metadata: Any) -> FileObject:
        out = await self._client._engine.afiles_create(file=file, purpose=purpose, **metadata)
        return _to_file_object(out)

    async def retrieve(self, file_id: str, **_: Any) -> FileObject:
        if self._client._engine._is_codex_profile():
            payload = await asyncio.to_thread(self._client._engine._compat_store.get_file, file_id)
            return _to_file_object(payload)

        payload = await self._client._engine._request_json_async(path=f"/files/{file_id}", payload={}, method="GET")
        return _to_file_object(payload)

    async def list(
        self,
        *,
        after: str | None = None,
        limit: int | None = None,
        order: str | None = None,
        purpose: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        if self._client._engine._is_codex_profile():
            data = await asyncio.to_thread(lambda: self._client._engine._compat_store._load_files_index().get("data", []))
            items = [item for item in data if isinstance(item, dict)]
            if purpose:
                items = [item for item in items if item.get("purpose") == purpose]
            if order == "desc":
                items = list(reversed(items))
            if isinstance(limit, int) and limit > 0:
                items = items[:limit]
            return {
                "object": "list",
                "data": [_to_file_object(item).to_dict() for item in items],
                "after": after,
                "has_more": False,
            }

        query: dict[str, Any] = {}
        if after is not None:
            query["after"] = after
        if limit is not None:
            query["limit"] = limit
        if order is not None:
            query["order"] = order
        if purpose is not None:
            query["purpose"] = purpose
        out = await self._client._engine._request_json_async(
            path="/files",
            payload={},
            method="GET",
            extra_query=query or None,
        )
        data = out.get("data")
        if isinstance(data, list):
            out = {**out, "data": [_to_file_object(item).to_dict() for item in data if isinstance(item, dict)]}
        return out

    async def delete(self, file_id: str, **_: Any) -> FileDeleted:
        if self._client._engine._is_codex_profile():
            store = self._client._engine._compat_store

            def _delete_local() -> FileDeleted:
                index = store._load_files_index()
                data = [item for item in index.get("data", []) if isinstance(item, dict)]
                kept = [item for item in data if item.get("id") != file_id]
                found = len(kept) != len(data)
                index["data"] = kept
                store._atomic_write_json(store.files_index_path, index)
                blob = store.files_blobs_dir / f"{file_id}.bin"
                blob.unlink(missing_ok=True)
                return FileDeleted(id=file_id, object="file.deleted", deleted=found)

            return await asyncio.to_thread(_delete_local)

        out = await self._client._engine._request_json_async(path=f"/files/{file_id}", payload={}, method="DELETE")
        return FileDeleted(
            id=str(out.get("id", file_id)),
            object=str(out.get("object", "file.deleted")),
            deleted=bool(out.get("deleted", True)),
        )

    async def content(self, file_id: str, **_: Any) -> bytes:
        if self._client._engine._is_codex_profile():
            blob = self._client._engine._compat_store.files_blobs_dir / f"{file_id}.bin"
            if not blob.exists():
                raise KeyError(f"file {file_id} not found")
            return await asyncio.to_thread(blob.read_bytes)

        tokens = await self._client._engine._ensure_authenticated_async()
        url = self._client._engine._resolve_request_url(f"/files/{file_id}/content")
        headers = self._client._engine._auth_headers(tokens)
        async with httpx.AsyncClient(timeout=self._client.timeout) as http:
            response = await http.get(url, headers=headers)
        if response.status_code >= 400:
            raise self._client._engine._build_sdk_request_error(response)
        return response.content

    async def retrieve_content(self, file_id: str, **kwargs: Any) -> bytes:
        return await self.content(file_id, **kwargs)

    async def wait_for_processing(
        self,
        file_id: str,
        *,
        timeout: float = 60.0,
        poll_interval: float = 0.5,
        **_: Any,
    ) -> FileObject:
        start = time.time()
        while True:
            file_obj = await self.retrieve(file_id)
            status = (file_obj.metadata or {}).get("status") if file_obj.metadata else None
            if status in {None, "processed", "completed"}:
                return file_obj
            if time.time() - start > timeout:
                return file_obj
            await asyncio.sleep(poll_interval)

    @property
    def with_raw_response(self) -> AsyncFilesWithRawResponse:
        return AsyncFilesWithRawResponse(self)

    @property
    def with_streaming_response(self) -> AsyncFilesWithStreamingResponse:
        return AsyncFilesWithStreamingResponse(self)


class FilesWithRawResponse:
    def __init__(self, files: Files) -> None:
        self.create = to_raw_response_wrapper(files.create)
        self.retrieve = to_raw_response_wrapper(files.retrieve)
        self.list = to_raw_response_wrapper(files.list)
        self.delete = to_raw_response_wrapper(files.delete)
        self.content = to_raw_response_wrapper(files.content)
        self.retrieve_content = to_raw_response_wrapper(files.retrieve_content)
        self.wait_for_processing = to_raw_response_wrapper(files.wait_for_processing)


class AsyncFilesWithRawResponse:
    def __init__(self, files: AsyncFiles) -> None:
        self.create = async_to_raw_response_wrapper(files.create)
        self.retrieve = async_to_raw_response_wrapper(files.retrieve)
        self.list = async_to_raw_response_wrapper(files.list)
        self.delete = async_to_raw_response_wrapper(files.delete)
        self.content = async_to_raw_response_wrapper(files.content)
        self.retrieve_content = async_to_raw_response_wrapper(files.retrieve_content)
        self.wait_for_processing = async_to_raw_response_wrapper(files.wait_for_processing)


class FilesWithStreamingResponse:
    def __init__(self, files: Files) -> None:
        self.create = to_streamed_response_wrapper(files.create)
        self.retrieve = to_streamed_response_wrapper(files.retrieve)
        self.list = to_streamed_response_wrapper(files.list)
        self.delete = to_streamed_response_wrapper(files.delete)
        self.content = to_streamed_response_wrapper(files.content)
        self.retrieve_content = to_streamed_response_wrapper(files.retrieve_content)
        self.wait_for_processing = to_streamed_response_wrapper(files.wait_for_processing)


class AsyncFilesWithStreamingResponse:
    def __init__(self, files: AsyncFiles) -> None:
        self.create = async_to_streamed_response_wrapper(files.create)
        self.retrieve = async_to_streamed_response_wrapper(files.retrieve)
        self.list = async_to_streamed_response_wrapper(files.list)
        self.delete = async_to_streamed_response_wrapper(files.delete)
        self.content = async_to_streamed_response_wrapper(files.content)
        self.retrieve_content = async_to_streamed_response_wrapper(files.retrieve_content)
        self.wait_for_processing = async_to_streamed_response_wrapper(files.wait_for_processing)
