from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from ...types.responses import Response, ResponseStreamEvent
from ...types.shared import TokenUsage


def usage_from_engine(usage: Any) -> TokenUsage | None:
    if usage is None:
        return None
    return TokenUsage(
        input_tokens=getattr(usage, "input_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None),
        total_tokens=getattr(usage, "total_tokens", None),
        cached_tokens=getattr(usage, "cached_tokens", None),
        reasoning_tokens=getattr(usage, "reasoning_tokens", None),
        cached_input_tokens=getattr(usage, "cached_input_tokens", None),
        reasoning_output_tokens=getattr(usage, "reasoning_output_tokens", None),
    )


def response_from_engine(resp: Any) -> Response:
    return Response(
        id=getattr(resp, "id", ""),
        output=list(getattr(resp, "output", []) or []),
        output_text=getattr(resp, "output_text", "") or "",
        usage=usage_from_engine(getattr(resp, "usage", None)),
        error=getattr(resp, "error", None),
        reasoning_summary=getattr(resp, "reasoning_summary", None),
        reasoning_items=list(getattr(resp, "reasoning_items", []) or []),
        encrypted_reasoning_content=getattr(resp, "encrypted_reasoning_content", None),
        finish_reason=getattr(resp, "finish_reason", None),
        previous_response_id=getattr(resp, "previous_response_id", None),
        raw_response=getattr(resp, "raw_response", None),
    )


def event_from_engine(event: Any) -> ResponseStreamEvent:
    return ResponseStreamEvent(
        type=getattr(event, "type", "event"),
        delta=getattr(event, "delta", None),
        usage=usage_from_engine(getattr(event, "usage", None)),
        raw=getattr(event, "raw", None),
        error=getattr(event, "error", None),
        call_id=getattr(event, "call_id", None),
        response_id=getattr(event, "response_id", None),
        finish_reason=getattr(event, "finish_reason", None),
        schema_version=getattr(event, "schema_version", "v1"),
    )


def iter_engine_events(events: Iterator[Any]) -> Iterator[ResponseStreamEvent]:
    for event in events:
        yield event_from_engine(event)


async def aiter_engine_events(events: AsyncIterator[Any]) -> AsyncIterator[ResponseStreamEvent]:
    async for event in events:
        yield event_from_engine(event)
