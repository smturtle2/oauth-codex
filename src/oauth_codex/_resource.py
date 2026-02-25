from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._sdk_client import AsyncClient, Client


class SyncAPIResource:
    _client: Client

    def __init__(self, client: Client) -> None:
        self._client = client

    @property
    def with_raw_response(self) -> SyncAPIResource:
        return self

    @property
    def with_streaming_response(self) -> SyncAPIResource:
        return self


class AsyncAPIResource:
    _client: AsyncClient

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    @property
    def with_raw_response(self) -> AsyncAPIResource:
        return self

    @property
    def with_streaming_response(self) -> AsyncAPIResource:
        return self
