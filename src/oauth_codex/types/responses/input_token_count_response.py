from __future__ import annotations

from ..._models import BaseModel


class InputTokenCountResponse(BaseModel):
    input_tokens: int
    cached_tokens: int | None = None
    total_tokens: int | None = None
