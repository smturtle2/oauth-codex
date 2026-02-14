from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class Files(SyncAPIResource):
    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('containers.files.files.Files.create')

    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('containers.files.files.Files.delete')

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('containers.files.files.Files.list')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('containers.files.files.Files.retrieve')

class AsyncFiles(AsyncAPIResource):
    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('containers.files.files.AsyncFiles.create')

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('containers.files.files.AsyncFiles.delete')

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('containers.files.files.AsyncFiles.list')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('containers.files.files.AsyncFiles.retrieve')
