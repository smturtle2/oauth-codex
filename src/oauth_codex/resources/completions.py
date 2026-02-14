from __future__ import annotations

from typing import Any

from .._resource import AsyncAPIResource, SyncAPIResource
from ._unsupported import raise_unsupported

class Completions(SyncAPIResource):
    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('completions.Completions.create')

class AsyncCompletions(AsyncAPIResource):
    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('completions.AsyncCompletions.create')
