from __future__ import annotations

from typing import Any

from ..._models import BaseModel


class VectorStoreSearchResponse(BaseModel):
    id: str
    object: str = "vector_store.search_result"
    score: float | None = None
    file_id: str | None = None
    filename: str | None = None
    content: list[dict[str, Any]] = []
