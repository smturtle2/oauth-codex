from __future__ import annotations

from typing import Any

from oauth_codex._models import BaseModel

from .file_batches import AsyncFileBatches, FileBatches
from .files import AsyncFiles, Files


class VectorStore(BaseModel):
    id: str
    object: str = "vector_store"
    created_at: int | None = None
    name: str | None = None
    status: str | None = None


class VectorStoreList(BaseModel):
    object: str = "list"
    data: list[VectorStore]


class VectorStores:
    def __init__(self, client: Any) -> None:
        self._client = client
        self._files: Files | None = None
        self._file_batches: FileBatches | None = None

    @property
    def files(self) -> Files:
        if self._files is None:
            self._files = Files(self._client)
        return self._files

    @property
    def file_batches(self) -> FileBatches:
        if self._file_batches is None:
            self._file_batches = FileBatches(self._client)
        return self._file_batches

    def create(
        self, *, name: str | None = None, file_ids: list[str] | None = None
    ) -> VectorStore:
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if file_ids is not None:
            payload["file_ids"] = file_ids

        response = self._client.request(
            "POST", "/vector_stores", json_data=payload or None
        )
        return VectorStore.from_dict(response.json())

    def retrieve(self, vector_store_id: str) -> VectorStore:
        response = self._client.request("GET", f"/vector_stores/{vector_store_id}")
        return VectorStore.from_dict(response.json())

    def list(self, *, limit: int | None = None) -> VectorStoreList:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit

        response = self._client.request("GET", "/vector_stores", params=params or None)
        return VectorStoreList.from_dict(response.json())


class AsyncVectorStores:
    def __init__(self, client: Any) -> None:
        self._client = client
        self._files: AsyncFiles | None = None
        self._file_batches: AsyncFileBatches | None = None

    @property
    def files(self) -> AsyncFiles:
        if self._files is None:
            self._files = AsyncFiles(self._client)
        return self._files

    @property
    def file_batches(self) -> AsyncFileBatches:
        if self._file_batches is None:
            self._file_batches = AsyncFileBatches(self._client)
        return self._file_batches

    async def create(
        self, *, name: str | None = None, file_ids: list[str] | None = None
    ) -> VectorStore:
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if file_ids is not None:
            payload["file_ids"] = file_ids

        response = await self._client.request(
            "POST", "/vector_stores", json_data=payload or None
        )
        return VectorStore.from_dict(response.json())

    async def retrieve(self, vector_store_id: str) -> VectorStore:
        response = await self._client.request(
            "GET", f"/vector_stores/{vector_store_id}"
        )
        return VectorStore.from_dict(response.json())

    async def list(self, *, limit: int | None = None) -> VectorStoreList:
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit

        response = await self._client.request(
            "GET", "/vector_stores", params=params or None
        )
        return VectorStoreList.from_dict(response.json())
