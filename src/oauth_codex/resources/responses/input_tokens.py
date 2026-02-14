from __future__ import annotations

from typing import Any

from ..._resource import AsyncAPIResource, SyncAPIResource
from .._wrappers import (
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
)
from ...types.responses import InputTokenCountResponse


class InputTokens(SyncAPIResource):
    def count(
        self,
        *,
        input: Any,
        model: str | None = None,
        tools: list[Any] | None = None,
        **_: Any,
    ) -> InputTokenCountResponse:
        result = self._client._engine.responses_input_tokens_count(
            model=model or "",
            input=input,
            tools=tools,
        )
        return InputTokenCountResponse(
            input_tokens=result.input_tokens,
            cached_tokens=result.cached_tokens,
            total_tokens=result.total_tokens,
        )

    @property
    def with_raw_response(self) -> InputTokensWithRawResponse:
        return InputTokensWithRawResponse(self)

    @property
    def with_streaming_response(self) -> InputTokensWithStreamingResponse:
        return InputTokensWithStreamingResponse(self)


class AsyncInputTokens(AsyncAPIResource):
    async def count(
        self,
        *,
        input: Any,
        model: str | None = None,
        tools: list[Any] | None = None,
        **_: Any,
    ) -> InputTokenCountResponse:
        result = await self._client._engine.aresponses_input_tokens_count(
            model=model or "",
            input=input,
            tools=tools,
        )
        return InputTokenCountResponse(
            input_tokens=result.input_tokens,
            cached_tokens=result.cached_tokens,
            total_tokens=result.total_tokens,
        )

    @property
    def with_raw_response(self) -> AsyncInputTokensWithRawResponse:
        return AsyncInputTokensWithRawResponse(self)

    @property
    def with_streaming_response(self) -> AsyncInputTokensWithStreamingResponse:
        return AsyncInputTokensWithStreamingResponse(self)


class InputTokensWithRawResponse:
    def __init__(self, input_tokens: InputTokens) -> None:
        self.count = to_raw_response_wrapper(input_tokens.count)


class AsyncInputTokensWithRawResponse:
    def __init__(self, input_tokens: AsyncInputTokens) -> None:
        self.count = async_to_raw_response_wrapper(input_tokens.count)


class InputTokensWithStreamingResponse:
    def __init__(self, input_tokens: InputTokens) -> None:
        self.count = to_streamed_response_wrapper(input_tokens.count)


class AsyncInputTokensWithStreamingResponse:
    def __init__(self, input_tokens: AsyncInputTokens) -> None:
        self.count = async_to_streamed_response_wrapper(input_tokens.count)
