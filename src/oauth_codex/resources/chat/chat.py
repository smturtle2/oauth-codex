from __future__ import annotations

from ..._resource import AsyncAPIResource, SyncAPIResource
from .completions.completions import AsyncCompletions, Completions


class Chat(SyncAPIResource):
    @property
    def completions(self) -> Completions:
        return Completions(self._client)


class AsyncChat(AsyncAPIResource):
    @property
    def completions(self) -> AsyncCompletions:
        return AsyncCompletions(self._client)
