from __future__ import annotations

from typing import Any

from .._resource import AsyncAPIResource, SyncAPIResource
from ._unsupported import raise_unsupported

class Batches(SyncAPIResource):
    def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('batches.Batches.cancel')

    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('batches.Batches.create')

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('batches.Batches.list')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('batches.Batches.retrieve')

class AsyncBatches(AsyncAPIResource):
    async def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('batches.AsyncBatches.cancel')

    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('batches.AsyncBatches.create')

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('batches.AsyncBatches.list')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('batches.AsyncBatches.retrieve')
