from __future__ import annotations

from typing import Any

from oauth_codex._models import BaseModel

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

    @property
    def files(self) -> Files:
        return Files(self._client)

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

    @property
    def files(self) -> AsyncFiles:
        return AsyncFiles(self._client)

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
