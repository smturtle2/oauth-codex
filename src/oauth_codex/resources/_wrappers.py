from __future__ import annotations

from functools import wraps
from typing import Any, Callable


class RawResponse:
    def __init__(self, data: Any) -> None:
        self.data = data

    def parse(self) -> Any:
        return self.data


def to_raw_response_wrapper(func: Callable[..., Any]) -> Callable[..., RawResponse]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> RawResponse:
        return RawResponse(func(*args, **kwargs))

    return wrapper


def async_to_raw_response_wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> RawResponse:
        return RawResponse(await func(*args, **kwargs))

    return wrapper


def to_streamed_response_wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


def async_to_streamed_response_wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await func(*args, **kwargs)

    return wrapper
