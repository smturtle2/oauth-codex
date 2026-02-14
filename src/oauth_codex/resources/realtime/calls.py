from __future__ import annotations

from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._unsupported import raise_unsupported

class Calls(SyncAPIResource):
    def accept(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('realtime.calls.Calls.accept')

    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('realtime.calls.Calls.create')

    def hangup(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('realtime.calls.Calls.hangup')

    def refer(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('realtime.calls.Calls.refer')

    def reject(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('realtime.calls.Calls.reject')

class AsyncCalls(AsyncAPIResource):
    async def accept(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('realtime.calls.AsyncCalls.accept')

    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('realtime.calls.AsyncCalls.create')

    async def hangup(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('realtime.calls.AsyncCalls.hangup')

    async def refer(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('realtime.calls.AsyncCalls.refer')

    async def reject(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('realtime.calls.AsyncCalls.reject')
