from __future__ import annotations

from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._unsupported import raise_unsupported
from .runs.runs import AsyncRuns, Runs


class Evals(SyncAPIResource):
    @property
    def runs(self) -> Runs:
        return Runs(self._client)

    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("evals.evals.Evals.create")

    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("evals.evals.Evals.delete")

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("evals.evals.Evals.list")

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("evals.evals.Evals.retrieve")

    def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("evals.evals.Evals.update")


class AsyncEvals(AsyncAPIResource):
    @property
    def runs(self) -> AsyncRuns:
        return AsyncRuns(self._client)

    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("evals.evals.AsyncEvals.create")

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("evals.evals.AsyncEvals.delete")

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("evals.evals.AsyncEvals.list")

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("evals.evals.AsyncEvals.retrieve")

    async def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported("evals.evals.AsyncEvals.update")
