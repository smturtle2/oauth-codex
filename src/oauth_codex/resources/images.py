from __future__ import annotations

from typing import Any

from .._resource import AsyncAPIResource, SyncAPIResource
from ._unsupported import raise_unsupported

class Images(SyncAPIResource):
    def create_variation(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('images.Images.create_variation')

    def edit(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('images.Images.edit')

    def generate(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('images.Images.generate')

class AsyncImages(AsyncAPIResource):
    async def create_variation(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('images.AsyncImages.create_variation')

    async def edit(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('images.AsyncImages.edit')

    async def generate(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('images.AsyncImages.generate')
