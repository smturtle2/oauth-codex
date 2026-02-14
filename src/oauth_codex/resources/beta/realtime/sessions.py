from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class Sessions(SyncAPIResource):
    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.realtime.sessions.Sessions.create')

class AsyncSessions(AsyncAPIResource):
    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.realtime.sessions.AsyncSessions.create')
