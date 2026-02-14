from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class Messages(SyncAPIResource):
    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.messages.Messages.create')

    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.messages.Messages.delete')

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.messages.Messages.list')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.messages.Messages.retrieve')

    def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.messages.Messages.update')

class AsyncMessages(AsyncAPIResource):
    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.messages.AsyncMessages.create')

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.messages.AsyncMessages.delete')

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.messages.AsyncMessages.list')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.messages.AsyncMessages.retrieve')

    async def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.messages.AsyncMessages.update')
