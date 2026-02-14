from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class Runs(SyncAPIResource):
    def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.runs.Runs.cancel')

    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.runs.Runs.create')

    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.runs.Runs.delete')

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.runs.Runs.list')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.runs.Runs.retrieve')

class AsyncRuns(AsyncAPIResource):
    async def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.runs.AsyncRuns.cancel')

    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.runs.AsyncRuns.create')

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.runs.AsyncRuns.delete')

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.runs.AsyncRuns.list')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.runs.AsyncRuns.retrieve')
