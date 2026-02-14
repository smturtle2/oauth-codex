from __future__ import annotations

from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._unsupported import raise_unsupported
from .files.files import AsyncFiles, Files


class Containers(SyncAPIResource):
    @property
    def files(self) -> Files:
        return Files(self._client)

    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("containers.containers.Containers.create")

    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("containers.containers.Containers.delete")

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("containers.containers.Containers.list")

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("containers.containers.Containers.retrieve")


class AsyncContainers(AsyncAPIResource):
    @property
    def files(self) -> AsyncFiles:
        return AsyncFiles(self._client)

    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("containers.containers.AsyncContainers.create")

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("containers.containers.AsyncContainers.delete")

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("containers.containers.AsyncContainers.list")

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("containers.containers.AsyncContainers.retrieve")
