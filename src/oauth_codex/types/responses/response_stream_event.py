from __future__ import annotations

from typing import Any

from ..._models import BaseModel
from ..shared.usage import TokenUsage


class ResponseStreamEvent(BaseModel):
    type: str
    delta: str | None = None
    usage: TokenUsage | None = None
    raw: dict[str, Any] | None = None
    error: str | None = None
    call_id: str | None = None
    response_id: str | None = None
    finish_reason: str | None = None
    schema_version: str = "v1"
