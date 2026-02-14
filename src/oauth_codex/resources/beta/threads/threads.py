from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported
from .messages import AsyncMessages, Messages
from .runs.runs import AsyncRuns, Runs


class Threads(SyncAPIResource):
    @property
    def runs(self) -> Runs:
        return Runs(self._client)

    @property
    def messages(self) -> Messages:
        return Messages(self._client)

    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.Threads.create")

    def create_and_run(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.Threads.create_and_run")

    def create_and_run_poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.Threads.create_and_run_poll")

    def create_and_run_stream(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.Threads.create_and_run_stream")

    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.Threads.delete")

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.Threads.retrieve")

    def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.Threads.update")


class AsyncThreads(AsyncAPIResource):
    @property
    def runs(self) -> AsyncRuns:
        return AsyncRuns(self._client)

    @property
    def messages(self) -> AsyncMessages:
        return AsyncMessages(self._client)

    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.AsyncThreads.create")

    async def create_and_run(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.AsyncThreads.create_and_run")

    async def create_and_run_poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.AsyncThreads.create_and_run_poll")

    async def create_and_run_stream(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.AsyncThreads.create_and_run_stream")

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.AsyncThreads.delete")

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.AsyncThreads.retrieve")

    async def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("beta.threads.threads.AsyncThreads.update")
