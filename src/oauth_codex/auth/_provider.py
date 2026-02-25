from __future__ import annotations

from typing import Mapping, Protocol, runtime_checkable


Headers = Mapping[str, str]


@runtime_checkable
class SyncAuthProvider(Protocol):
    def ensure_valid(self, *, interactive: bool = True) -> None: ...

    def get_headers(self) -> Headers: ...


@runtime_checkable
class AsyncAuthProvider(Protocol):
    async def aensure_valid(self, *, interactive: bool = True) -> None: ...

    async def aget_headers(self) -> Headers: ...
