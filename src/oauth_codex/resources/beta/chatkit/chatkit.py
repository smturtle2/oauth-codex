from __future__ import annotations

from ...._resource import AsyncAPIResource, SyncAPIResource
from .sessions import AsyncSessions, Sessions
from .threads import AsyncThreads, Threads


class ChatKit(SyncAPIResource):
    @property
    def sessions(self) -> Sessions:
        return Sessions(self._client)

    @property
    def threads(self) -> Threads:
        return Threads(self._client)


class AsyncChatKit(AsyncAPIResource):
    @property
    def sessions(self) -> AsyncSessions:
        return AsyncSessions(self._client)

    @property
    def threads(self) -> AsyncThreads:
        return AsyncThreads(self._client)
