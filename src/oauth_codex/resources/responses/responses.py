from __future__ import annotations

from typing import Any, AsyncIterator, Iterator, Literal, overload

from ...legacy_types import (
    Message,
    ToolInput,
    ToolResult,
    TruncationMode,
    ValidationMode,
)
from ..._resource import AsyncAPIResource, SyncAPIResource
from .._unsupported import raise_unsupported
from .._wrappers import (
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
)
from ...types.responses import Response, ResponseStreamEvent
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

    @overload
    def create(
        self,
        *,
        model: str,
        input: str | Message | list[Message] | None = None,
        messages: list[Message] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        stream: Literal[False] = False,
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> Response:
        ...

    @overload
    def create(
        self,
        *,
        model: str,
        input: str | Message | list[Message] | None = None,
        messages: list[Message] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        stream: Literal[True],
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> Iterator[ResponseStreamEvent]:
        ...

    def create(
        self,
        *,
        model: str,
        input: str | Message | list[Message] | None = None,
        messages: list[Message] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        stream: bool = False,
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> Response | Iterator[ResponseStreamEvent]:
        out = self._client._engine.responses_create(
            model=model,
            input=input,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            stream=stream,
            validation_mode=validation_mode,
            **extra,
        )
        if stream:
            return iter_events(out)
        return response_from_legacy(out)

    def stream(
        self,
        *,
        model: str,
        input: str | Message | list[Message] | None = None,
        messages: list[Message] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> Iterator[ResponseStreamEvent]:
        return self.create(
            model=model,
            input=input,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            stream=True,
            validation_mode=validation_mode,
            **extra,
        )

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

    @overload
    async def create(
        self,
        *,
        model: str,
        input: str | Message | list[Message] | None = None,
        messages: list[Message] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        stream: Literal[False] = False,
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> Response:
        ...

    @overload
    async def create(
        self,
        *,
        model: str,
        input: str | Message | list[Message] | None = None,
        messages: list[Message] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        stream: Literal[True],
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> AsyncIterator[ResponseStreamEvent]:
        ...

    async def create(
        self,
        *,
        model: str,
        input: str | Message | list[Message] | None = None,
        messages: list[Message] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        stream: bool = False,
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> Response | AsyncIterator[ResponseStreamEvent]:
        out = await self._client._engine.aresponses_create(
            model=model,
            input=input,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            stream=stream,
            validation_mode=validation_mode,
            **extra,
        )
        if stream:
            return aiter_events(out)
        return response_from_legacy(out)

    async def stream(
        self,
        *,
        model: str,
        input: str | Message | list[Message] | None = None,
        messages: list[Message] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> AsyncIterator[ResponseStreamEvent]:
        return await self.create(
            model=model,
            input=input,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            stream=True,
            validation_mode=validation_mode,
            **extra,
        )

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
