from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class Checkpoints(SyncAPIResource):
    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.jobs.checkpoints.Checkpoints.list')

class AsyncCheckpoints(AsyncAPIResource):
    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.jobs.checkpoints.AsyncCheckpoints.list')
