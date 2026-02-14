from __future__ import annotations

from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._unsupported import raise_unsupported
from .parts import AsyncParts, Parts


class Uploads(SyncAPIResource):
    @property
    def parts(self) -> Parts:
        return Parts(self._client)

    def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("uploads.uploads.Uploads.cancel")

    def complete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("uploads.uploads.Uploads.complete")

    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("uploads.uploads.Uploads.create")

    def upload_file_chunked(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("uploads.uploads.Uploads.upload_file_chunked")


class AsyncUploads(AsyncAPIResource):
    @property
    def parts(self) -> AsyncParts:
        return AsyncParts(self._client)

    async def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("uploads.uploads.AsyncUploads.cancel")

    async def complete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("uploads.uploads.AsyncUploads.complete")

    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("uploads.uploads.AsyncUploads.create")

    async def upload_file_chunked(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("uploads.uploads.AsyncUploads.upload_file_chunked")
