from __future__ import annotations

from typing import Any, Mapping, TypeAlias, TypedDict


class NotGiven:
    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "NOT_GIVEN"


class Omit:
    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "omit"


not_given = NotGiven()
NOT_GIVEN = not_given
omit = Omit()

Headers: TypeAlias = Mapping[str, str]
Query: TypeAlias = Mapping[str, object]
Body: TypeAlias = object


class RequestOptions(TypedDict, total=False):
    headers: Headers
    max_retries: int
    timeout: float | None
    params: Query
    extra_json: Mapping[str, object]
    idempotency_key: str


Timeout: TypeAlias = float
