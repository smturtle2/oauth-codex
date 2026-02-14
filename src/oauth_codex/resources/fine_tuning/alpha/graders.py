from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class Graders(SyncAPIResource):
    def run(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.alpha.graders.Graders.run')

    def validate(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.alpha.graders.Graders.validate')

class AsyncGraders(AsyncAPIResource):
    async def run(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.alpha.graders.AsyncGraders.run')

    async def validate(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.alpha.graders.AsyncGraders.validate')
