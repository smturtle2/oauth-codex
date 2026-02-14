from __future__ import annotations

from typing import Any

from ...._resource import AsyncAPIResource, SyncAPIResource
from ..._unsupported import raise_unsupported

class Completions(SyncAPIResource):
    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.Completions.create')

    def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.Completions.delete')

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.Completions.list')

    def parse(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.Completions.parse')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.Completions.retrieve')

    def stream(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.Completions.stream')

    def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.Completions.update')

class AsyncCompletions(AsyncAPIResource):
    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.AsyncCompletions.create')

    async def delete(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.AsyncCompletions.delete')

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.AsyncCompletions.list')

    async def parse(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.AsyncCompletions.parse')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.AsyncCompletions.retrieve')

    async def stream(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.AsyncCompletions.stream')

    async def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('chat.completions.completions.AsyncCompletions.update')
