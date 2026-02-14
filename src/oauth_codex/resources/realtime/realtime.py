from __future__ import annotations

from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._unsupported import raise_unsupported
from .calls import AsyncCalls, Calls
from .client_secrets import AsyncClientSecrets, ClientSecrets


class Realtime(SyncAPIResource):
    @property
    def calls(self) -> Calls:
        return Calls(self._client)

    @property
    def client_secrets(self) -> ClientSecrets:
        return ClientSecrets(self._client)

    def connect(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("realtime.realtime.Realtime.connect")


class AsyncRealtime(AsyncAPIResource):
    @property
    def calls(self) -> AsyncCalls:
        return AsyncCalls(self._client)

    @property
    def client_secrets(self) -> AsyncClientSecrets:
        return AsyncClientSecrets(self._client)

    async def connect(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("realtime.realtime.AsyncRealtime.connect")
