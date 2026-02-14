from __future__ import annotations

from typing import Any

from ..._models import BaseModel
from ..shared.usage import TokenUsage


class Response(BaseModel):
    id: str
    output: list[dict[str, Any]] = []
    output_text: str = ""
    usage: TokenUsage | None = None
    error: dict[str, Any] | None = None
    reasoning_summary: str | None = None
    reasoning_items: list[dict[str, Any]] = []
    encrypted_reasoning_content: str | None = None
    finish_reason: str | None = None
    previous_response_id: str | None = None
    raw_response: dict[str, Any] | None = None
