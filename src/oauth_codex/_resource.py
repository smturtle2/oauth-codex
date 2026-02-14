from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._client import OAuthCodexClient, AsyncOAuthCodexClient


class SyncAPIResource:
    _client: OAuthCodexClient

    def __init__(self, client: OAuthCodexClient) -> None:
        self._client = client

    @property
    def with_raw_response(self) -> SyncAPIResource:
        return self

    @property
    def with_streaming_response(self) -> SyncAPIResource:
        return self


class AsyncAPIResource:
    _client: AsyncOAuthCodexClient

    def __init__(self, client: AsyncOAuthCodexClient) -> None:
        self._client = client

    @property
    def with_raw_response(self) -> AsyncAPIResource:
        return self

    @property
    def with_streaming_response(self) -> AsyncAPIResource:
        return self
