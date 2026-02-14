from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class Permissions(SyncAPIResource):
    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.checkpoints.permissions.Permissions.create')

    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.checkpoints.permissions.Permissions.delete')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.checkpoints.permissions.Permissions.retrieve')

class AsyncPermissions(AsyncAPIResource):
    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.checkpoints.permissions.AsyncPermissions.create')

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.checkpoints.permissions.AsyncPermissions.delete')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('fine_tuning.checkpoints.permissions.AsyncPermissions.retrieve')
