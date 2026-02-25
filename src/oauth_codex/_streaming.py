from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterator
from typing import Generic, TypeVar, cast

import httpx

T = TypeVar("T")


def _identity(value: str) -> str:
    return value


def _extract_event_data(raw_event: str) -> str | None:
    data_lines: list[str] = []
    for line in raw_event.split("\n"):
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())

    if not data_lines:
        return None
    return "\n".join(data_lines)


class Stream(Generic[T]):
    def __init__(
        self, response: httpx.Response, cast_event: Callable[[str], T] | None = None
    ) -> None:
        self._response = response
        self._cast_event = cast_event or cast(Callable[[str], T], _identity)

    def __iter__(self) -> Iterator[T]:
        try:
            buffer = ""
            for chunk in self._response.iter_text():
                if not chunk:
                    continue

                buffer += chunk.replace("\r\n", "\n").replace("\r", "\n")
                while "\n\n" in buffer:
                    raw_event, buffer = buffer.split("\n\n", 1)
                    data = _extract_event_data(raw_event)
                    if data is None:
                        continue
                    yield self._cast_event(data)

            if buffer:
                data = _extract_event_data(buffer)
                if data is not None:
                    yield self._cast_event(data)
        finally:
            self._response.close()


class AsyncStream(Generic[T]):
    def __init__(
        self, response: httpx.Response, cast_event: Callable[[str], T] | None = None
    ) -> None:
        self._response = response
        self._cast_event = cast_event or cast(Callable[[str], T], _identity)

    async def __aiter__(self) -> AsyncIterator[T]:
        try:
            buffer = ""
            async for chunk in self._response.aiter_text():
                if not chunk:
                    continue

                buffer += chunk.replace("\r\n", "\n").replace("\r", "\n")
                while "\n\n" in buffer:
                    raw_event, buffer = buffer.split("\n\n", 1)
                    data = _extract_event_data(raw_event)
                    if data is None:
                        continue
                    yield self._cast_event(data)

            if buffer:
                data = _extract_event_data(buffer)
                if data is not None:
                    yield self._cast_event(data)
        finally:
            await self._response.aclose()
