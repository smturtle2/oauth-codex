from __future__ import annotations

from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._unsupported import raise_unsupported

class Items(SyncAPIResource):
    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('conversations.items.Items.create')

    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('conversations.items.Items.delete')

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('conversations.items.Items.list')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('conversations.items.Items.retrieve')

class AsyncItems(AsyncAPIResource):
    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('conversations.items.AsyncItems.create')

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('conversations.items.AsyncItems.delete')

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('conversations.items.AsyncItems.list')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('conversations.items.AsyncItems.retrieve')
