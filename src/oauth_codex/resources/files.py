from __future__ import annotations

from pathlib import Path
from typing import Any

from oauth_codex._models import BaseModel


class FileObject(BaseModel):
    id: str
    object: str = "file"
    bytes: int | None = None
    created_at: int | None = None
    filename: str | None = None
    purpose: str | None = None


class FileDeleted(BaseModel):
    id: str
    object: str = "file.deleted"
    deleted: bool


class FileList(BaseModel):
    object: str = "list"
    data: list[FileObject]


class Files:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, *, file: Any, purpose: str, **metadata: Any) -> FileObject:
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            with file_path.open("rb") as f:
                response = self._client.request(
                    "POST",
                    "/files",
                    data={"purpose": purpose, **metadata},
                    files={"file": (file_path.name, f)},
                )
        else:
            response = self._client.request(
                "POST",
                "/files",
                data={"purpose": purpose, **metadata},
                files={"file": file},
            )
        return FileObject.from_dict(response.json())

    def retrieve(self, file_id: str) -> FileObject:
        response = self._client.request("GET", f"/files/{file_id}")
        return FileObject.from_dict(response.json())

    def list(self, *, purpose: str | None = None, limit: int | None = None) -> FileList:
        params: dict[str, Any] = {}
        if purpose is not None:
            params["purpose"] = purpose
        if limit is not None:
            params["limit"] = limit
        response = self._client.request("GET", "/files", params=params or None)
        return FileList.from_dict(response.json())

    def delete(self, file_id: str) -> FileDeleted:
        response = self._client.request("DELETE", f"/files/{file_id}")
        return FileDeleted.from_dict(response.json())


class AsyncFiles:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(self, *, file: Any, purpose: str, **metadata: Any) -> FileObject:
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            with file_path.open("rb") as f:
                response = await self._client.request(
                    "POST",
                    "/files",
                    data={"purpose": purpose, **metadata},
                    files={"file": (file_path.name, f)},
                )
        else:
            response = await self._client.request(
                "POST",
                "/files",
                data={"purpose": purpose, **metadata},
                files={"file": file},
            )
        return FileObject.from_dict(response.json())

    async def retrieve(self, file_id: str) -> FileObject:
        response = await self._client.request("GET", f"/files/{file_id}")
        return FileObject.from_dict(response.json())

    async def list(
        self, *, purpose: str | None = None, limit: int | None = None
    ) -> FileList:
        params: dict[str, Any] = {}
        if purpose is not None:
            params["purpose"] = purpose
        if limit is not None:
            params["limit"] = limit
        response = await self._client.request("GET", "/files", params=params or None)
        return FileList.from_dict(response.json())

    async def delete(self, file_id: str) -> FileDeleted:
        response = await self._client.request("DELETE", f"/files/{file_id}")
        return FileDeleted.from_dict(response.json())
