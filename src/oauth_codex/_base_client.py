from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ._types import Body, Query


@dataclass
class FinalRequestOptions:
    extra_headers: Mapping[str, str] | None = None
    extra_query: Query | None = None
    extra_body: Body | None = None
    timeout: float | None = None


def make_request_options(
    *,
    extra_headers: Mapping[str, str] | None = None,
    extra_query: Query | None = None,
    extra_body: Body | None = None,
    timeout: float | None = None,
) -> FinalRequestOptions:
    return FinalRequestOptions(
        extra_headers=extra_headers,
        extra_query=extra_query,
        extra_body=extra_body,
        timeout=timeout,
    )


class SyncAPIClient:
    def __init__(self, **_: Any) -> None:
        pass


class AsyncAPIClient:
    def __init__(self, **_: Any) -> None:
        pass
