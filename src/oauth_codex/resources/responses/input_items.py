from __future__ import annotations

from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._unsupported import raise_unsupported
from .._wrappers import (
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
)


class InputItems(SyncAPIResource):
    def list(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.input_items.list")

    @property
    def with_raw_response(self) -> InputItemsWithRawResponse:
        return InputItemsWithRawResponse(self)

    @property
    def with_streaming_response(self) -> InputItemsWithStreamingResponse:
        return InputItemsWithStreamingResponse(self)


class AsyncInputItems(AsyncAPIResource):
    async def list(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.input_items.list")

    @property
    def with_raw_response(self) -> AsyncInputItemsWithRawResponse:
        return AsyncInputItemsWithRawResponse(self)

    @property
    def with_streaming_response(self) -> AsyncInputItemsWithStreamingResponse:
        return AsyncInputItemsWithStreamingResponse(self)


class InputItemsWithRawResponse:
    def __init__(self, input_items: InputItems) -> None:
        self.list = to_raw_response_wrapper(input_items.list)


class AsyncInputItemsWithRawResponse:
    def __init__(self, input_items: AsyncInputItems) -> None:
        self.list = async_to_raw_response_wrapper(input_items.list)


class InputItemsWithStreamingResponse:
    def __init__(self, input_items: InputItems) -> None:
        self.list = to_streamed_response_wrapper(input_items.list)


class AsyncInputItemsWithStreamingResponse:
    def __init__(self, input_items: AsyncInputItems) -> None:
        self.list = async_to_streamed_response_wrapper(input_items.list)
