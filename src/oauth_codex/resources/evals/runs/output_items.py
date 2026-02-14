from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class OutputItems(SyncAPIResource):
    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.output_items.OutputItems.list')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.output_items.OutputItems.retrieve')

class AsyncOutputItems(AsyncAPIResource):
    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.output_items.AsyncOutputItems.list')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('evals.runs.output_items.AsyncOutputItems.retrieve')
