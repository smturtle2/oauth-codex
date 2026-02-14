from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class Threads(SyncAPIResource):
    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.threads.Threads.delete')

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.threads.Threads.list')

    def list_items(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.threads.Threads.list_items')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.threads.Threads.retrieve')

class AsyncThreads(AsyncAPIResource):
    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.threads.AsyncThreads.delete')

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.threads.AsyncThreads.list')

    async def list_items(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.threads.AsyncThreads.list_items')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.threads.AsyncThreads.retrieve')
