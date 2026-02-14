from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported
from .checkpoints import AsyncCheckpoints, Checkpoints


class Jobs(SyncAPIResource):
    @property
    def checkpoints(self) -> Checkpoints:
        return Checkpoints(self._client)

    def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.Jobs.cancel")

    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.Jobs.create")

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.Jobs.list")

    def list_events(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.Jobs.list_events")

    def pause(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.Jobs.pause")

    def resume(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.Jobs.resume")

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.Jobs.retrieve")


class AsyncJobs(AsyncAPIResource):
    @property
    def checkpoints(self) -> AsyncCheckpoints:
        return AsyncCheckpoints(self._client)

    async def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.AsyncJobs.cancel")

    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.AsyncJobs.create")

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.AsyncJobs.list")

    async def list_events(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.AsyncJobs.list_events")

    async def pause(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.AsyncJobs.pause")

    async def resume(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.AsyncJobs.resume")

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("fine_tuning.jobs.jobs.AsyncJobs.retrieve")
