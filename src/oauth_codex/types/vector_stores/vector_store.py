from __future__ import annotations

from typing import Any

from ..._models import BaseModel


class VectorStore(BaseModel):
    id: str
    object: str = "vector_store"
    created_at: int | None = None
    name: str | None = None
    metadata: dict[str, Any] | None = None
    file_ids: list[str] = []
    status: str | None = None
    usage_bytes: int | None = None
    file_counts: dict[str, int] | None = None
    expires_after: dict[str, Any] | None = None
