from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported
from .sessions import AsyncSessions, Sessions
from .transcription_sessions import AsyncTranscriptionSessions, TranscriptionSessions


class Realtime(SyncAPIResource):
    @property
    def sessions(self) -> Sessions:
        return Sessions(self._client)

    @property
    def transcription_sessions(self) -> TranscriptionSessions:
        return TranscriptionSessions(self._client)

    def connect(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.realtime.realtime.Realtime.connect")


class AsyncRealtime(AsyncAPIResource):
    @property
    def sessions(self) -> AsyncSessions:
        return AsyncSessions(self._client)

    @property
    def transcription_sessions(self) -> AsyncTranscriptionSessions:
        return AsyncTranscriptionSessions(self._client)

    async def connect(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.realtime.realtime.AsyncRealtime.connect")
