from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class Messages(SyncAPIResource):
    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.messages.Messages.list')

class AsyncMessages(AsyncAPIResource):
    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.messages.AsyncMessages.list')
