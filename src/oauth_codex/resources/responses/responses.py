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
from ...types.responses import Response
from ._helpers import aiter_events, iter_events, response_from_legacy
from .input_items import (
    AsyncInputItems,
    AsyncInputItemsWithRawResponse,
    AsyncInputItemsWithStreamingResponse,
    InputItems,
    InputItemsWithRawResponse,
    InputItemsWithStreamingResponse,
)
from .input_tokens import (
    AsyncInputTokens,
    AsyncInputTokensWithRawResponse,
    AsyncInputTokensWithStreamingResponse,
    InputTokens,
    InputTokensWithRawResponse,
    InputTokensWithStreamingResponse,
)


class Responses(SyncAPIResource):
    @property
    def input_items(self) -> InputItems:
        return InputItems(self._client)

    @property
    def input_tokens(self) -> InputTokens:
        return InputTokens(self._client)

    def create(self, *, stream: bool = False, **kwargs: Any) -> Response | Any:
        out = self._client._engine.responses_create(stream=stream, **kwargs)
        if stream:
            return iter_events(out)
        return response_from_legacy(out)

    def stream(self, **kwargs: Any) -> Any:
        return self.create(stream=True, **kwargs)

    def retrieve(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.retrieve")

    def cancel(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.cancel")

    def delete(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.delete")

    def compact(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.compact")

    def parse(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.parse")

    @property
    def with_raw_response(self) -> ResponsesWithRawResponse:
        return ResponsesWithRawResponse(self)

    @property
    def with_streaming_response(self) -> ResponsesWithStreamingResponse:
        return ResponsesWithStreamingResponse(self)


class AsyncResponses(AsyncAPIResource):
    @property
    def input_items(self) -> AsyncInputItems:
        return AsyncInputItems(self._client)

    @property
    def input_tokens(self) -> AsyncInputTokens:
        return AsyncInputTokens(self._client)

    async def create(self, *, stream: bool = False, **kwargs: Any) -> Response | Any:
        out = await self._client._engine.aresponses_create(stream=stream, **kwargs)
        if stream:
            return aiter_events(out)
        return response_from_legacy(out)

    async def stream(self, **kwargs: Any) -> Any:
        return await self.create(stream=True, **kwargs)

    async def retrieve(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.retrieve")

    async def cancel(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.cancel")

    async def delete(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.delete")

    async def compact(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.compact")

    async def parse(self, *_: Any, **__: Any) -> None:
        raise_unsupported("responses.parse")

    @property
    def with_raw_response(self) -> AsyncResponsesWithRawResponse:
        return AsyncResponsesWithRawResponse(self)

    @property
    def with_streaming_response(self) -> AsyncResponsesWithStreamingResponse:
        return AsyncResponsesWithStreamingResponse(self)


class ResponsesWithRawResponse:
    def __init__(self, responses: Responses) -> None:
        self.create = to_raw_response_wrapper(responses.create)
        self.stream = to_raw_response_wrapper(responses.stream)
        self.retrieve = to_raw_response_wrapper(responses.retrieve)
        self.cancel = to_raw_response_wrapper(responses.cancel)
        self.delete = to_raw_response_wrapper(responses.delete)
        self.compact = to_raw_response_wrapper(responses.compact)
        self.parse = to_raw_response_wrapper(responses.parse)
        self.input_items = InputItemsWithRawResponse(responses.input_items)
        self.input_tokens = InputTokensWithRawResponse(responses.input_tokens)


class AsyncResponsesWithRawResponse:
    def __init__(self, responses: AsyncResponses) -> None:
        self.create = async_to_raw_response_wrapper(responses.create)
        self.stream = async_to_raw_response_wrapper(responses.stream)
        self.retrieve = async_to_raw_response_wrapper(responses.retrieve)
        self.cancel = async_to_raw_response_wrapper(responses.cancel)
        self.delete = async_to_raw_response_wrapper(responses.delete)
        self.compact = async_to_raw_response_wrapper(responses.compact)
        self.parse = async_to_raw_response_wrapper(responses.parse)
        self.input_items = AsyncInputItemsWithRawResponse(responses.input_items)
        self.input_tokens = AsyncInputTokensWithRawResponse(responses.input_tokens)


class ResponsesWithStreamingResponse:
    def __init__(self, responses: Responses) -> None:
        self.create = to_streamed_response_wrapper(responses.create)
        self.stream = to_streamed_response_wrapper(responses.stream)
        self.retrieve = to_streamed_response_wrapper(responses.retrieve)
        self.cancel = to_streamed_response_wrapper(responses.cancel)
        self.delete = to_streamed_response_wrapper(responses.delete)
        self.compact = to_streamed_response_wrapper(responses.compact)
        self.parse = to_streamed_response_wrapper(responses.parse)
        self.input_items = InputItemsWithStreamingResponse(responses.input_items)
        self.input_tokens = InputTokensWithStreamingResponse(responses.input_tokens)


class AsyncResponsesWithStreamingResponse:
    def __init__(self, responses: AsyncResponses) -> None:
        self.create = async_to_streamed_response_wrapper(responses.create)
        self.stream = async_to_streamed_response_wrapper(responses.stream)
        self.retrieve = async_to_streamed_response_wrapper(responses.retrieve)
        self.cancel = async_to_streamed_response_wrapper(responses.cancel)
        self.delete = async_to_streamed_response_wrapper(responses.delete)
        self.compact = async_to_streamed_response_wrapper(responses.compact)
        self.parse = async_to_streamed_response_wrapper(responses.parse)
        self.input_items = AsyncInputItemsWithStreamingResponse(responses.input_items)
        self.input_tokens = AsyncInputTokensWithStreamingResponse(responses.input_tokens)
