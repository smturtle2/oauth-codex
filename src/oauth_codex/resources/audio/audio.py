from __future__ import annotations

from ..._resource import AsyncAPIResource, SyncAPIResource
from .speech import AsyncSpeech, Speech
from .transcriptions import AsyncTranscriptions, Transcriptions
from .translations import AsyncTranslations, Translations


class Audio(SyncAPIResource):
    @property
    def speech(self) -> Speech:
        return Speech(self._client)

    @property
    def transcriptions(self) -> Transcriptions:
        return Transcriptions(self._client)

    @property
    def translations(self) -> Translations:
        return Translations(self._client)


class AsyncAudio(AsyncAPIResource):
    @property
    def speech(self) -> AsyncSpeech:
        return AsyncSpeech(self._client)

    @property
    def transcriptions(self) -> AsyncTranscriptions:
        return AsyncTranscriptions(self._client)

    @property
    def translations(self) -> AsyncTranslations:
        return AsyncTranslations(self._client)
