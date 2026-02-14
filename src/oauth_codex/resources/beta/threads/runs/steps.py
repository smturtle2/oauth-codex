from __future__ import annotations

from typing import Any

from ....._resource import AsyncAPIResource, SyncAPIResource
from ...._unsupported import raise_unsupported

class Steps(SyncAPIResource):
    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.steps.Steps.list')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.steps.Steps.retrieve')

class AsyncSteps(AsyncAPIResource):
    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.steps.AsyncSteps.list')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.steps.AsyncSteps.retrieve')
