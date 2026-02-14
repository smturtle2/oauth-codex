from __future__ import annotations

from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._unsupported import raise_unsupported

class Speech(SyncAPIResource):
    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('audio.speech.Speech.create')

class AsyncSpeech(AsyncAPIResource):
    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('audio.speech.AsyncSpeech.create')
