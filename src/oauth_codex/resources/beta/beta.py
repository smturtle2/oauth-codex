from __future__ import annotations

from ..._resource import AsyncAPIResource, SyncAPIResource
from .assistants import AsyncAssistants, Assistants
from .chatkit.chatkit import AsyncChatKit, ChatKit
from .realtime.realtime import AsyncRealtime, Realtime
from .threads.threads import AsyncThreads, Threads


class Beta(SyncAPIResource):
    @property
    def assistants(self) -> Assistants:
        return Assistants(self._client)

    @property
    def chatkit(self) -> ChatKit:
        return ChatKit(self._client)

    @property
    def realtime(self) -> Realtime:
        return Realtime(self._client)

    @property
    def threads(self) -> Threads:
        return Threads(self._client)


class AsyncBeta(AsyncAPIResource):
    @property
    def assistants(self) -> AsyncAssistants:
        return AsyncAssistants(self._client)

    @property
    def chatkit(self) -> AsyncChatKit:
        return AsyncChatKit(self._client)

    @property
    def realtime(self) -> AsyncRealtime:
        return AsyncRealtime(self._client)

    @property
    def threads(self) -> AsyncThreads:
        return AsyncThreads(self._client)
