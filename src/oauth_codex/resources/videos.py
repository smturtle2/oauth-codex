from __future__ import annotations

from typing import Any

from .._resource import AsyncAPIResource, SyncAPIResource
from ._unsupported import raise_unsupported

class Videos(SyncAPIResource):
    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.Videos.create')

    def create_and_poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.Videos.create_and_poll')

    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.Videos.delete')

    def download_content(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.Videos.download_content')

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.Videos.list')

    def poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.Videos.poll')

    def remix(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.Videos.remix')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.Videos.retrieve')

class AsyncVideos(AsyncAPIResource):
    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.AsyncVideos.create')

    async def create_and_poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.AsyncVideos.create_and_poll')

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.AsyncVideos.delete')

    async def download_content(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.AsyncVideos.download_content')

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.AsyncVideos.list')

    async def poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.AsyncVideos.poll')

    async def remix(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.AsyncVideos.remix')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('videos.AsyncVideos.retrieve')
