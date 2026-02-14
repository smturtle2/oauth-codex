from __future__ import annotations

from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._unsupported import raise_unsupported
from .items import AsyncItems, Items


class Conversations(SyncAPIResource):
    @property
    def items(self) -> Items:
        return Items(self._client)

    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("conversations.conversations.Conversations.create")

    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("conversations.conversations.Conversations.delete")

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("conversations.conversations.Conversations.retrieve")

    def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("conversations.conversations.Conversations.update")


class AsyncConversations(AsyncAPIResource):
    @property
    def items(self) -> AsyncItems:
        return AsyncItems(self._client)

    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("conversations.conversations.AsyncConversations.create")

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("conversations.conversations.AsyncConversations.delete")

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("conversations.conversations.AsyncConversations.retrieve")

    async def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("conversations.conversations.AsyncConversations.update")
