from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class Sessions(SyncAPIResource):
    def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.sessions.Sessions.cancel')

    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.sessions.Sessions.create')

class AsyncSessions(AsyncAPIResource):
    async def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.sessions.AsyncSessions.cancel')

    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.chatkit.sessions.AsyncSessions.create')
