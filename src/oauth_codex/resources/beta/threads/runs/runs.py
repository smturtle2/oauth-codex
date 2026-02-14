from __future__ import annotations

from typing import Any

from ....._resource import AsyncAPIResource, SyncAPIResource
from ...._unsupported import raise_unsupported

class Runs(SyncAPIResource):
    def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.cancel')

    def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.create')

    def create_and_poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.create_and_poll')

    def create_and_stream(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.create_and_stream')

    def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.list')

    def poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.poll')

    def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.retrieve')

    def stream(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.stream')

    def submit_tool_outputs(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.submit_tool_outputs')

    def submit_tool_outputs_and_poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.submit_tool_outputs_and_poll')

    def submit_tool_outputs_stream(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.submit_tool_outputs_stream')

    def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.Runs.update')

class AsyncRuns(AsyncAPIResource):
    async def cancel(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.cancel')

    async def create(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.create')

    async def create_and_poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.create_and_poll')

    async def create_and_stream(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.create_and_stream')

    async def list(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.list')

    async def poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.poll')

    async def retrieve(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.retrieve')

    async def stream(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.stream')

    async def submit_tool_outputs(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.submit_tool_outputs')

    async def submit_tool_outputs_and_poll(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.submit_tool_outputs_and_poll')

    async def submit_tool_outputs_stream(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.submit_tool_outputs_stream')

    async def update(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('beta.threads.runs.runs.AsyncRuns.update')
