from __future__ import annotations

from typing import Any

from oauth_codex._models import BaseModel


class VectorStoreFile(BaseModel):
    id: str
    object: str = "vector_store.file"
    vector_store_id: str | None = None
    created_at: int | None = None
    status: str | None = None


class VectorStoreFileList(BaseModel):
    object: str = "list"
    data: list[VectorStoreFile]


class Files:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, vector_store_id: str, *, file_id: str) -> VectorStoreFile:
        response = self._client.request(
            "POST",
            f"/vector_stores/{vector_store_id}/files",
            json_data={"file_id": file_id},
        )
        return VectorStoreFile.from_dict(response.json())

    def list(self, vector_store_id: str) -> VectorStoreFileList:
        response = self._client.request(
            "GET", f"/vector_stores/{vector_store_id}/files"
        )
        return VectorStoreFileList.from_dict(response.json())


class AsyncFiles:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(self, vector_store_id: str, *, file_id: str) -> VectorStoreFile:
        response = await self._client.request(
            "POST",
            f"/vector_stores/{vector_store_id}/files",
            json_data={"file_id": file_id},
        )
        return VectorStoreFile.from_dict(response.json())

    async def list(self, vector_store_id: str) -> VectorStoreFileList:
        response = await self._client.request(
            "GET", f"/vector_stores/{vector_store_id}/files"
        )
        return VectorStoreFileList.from_dict(response.json())
