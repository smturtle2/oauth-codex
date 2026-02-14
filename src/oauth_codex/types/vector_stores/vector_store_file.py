from __future__ import annotations

from ..._models import BaseModel


class VectorStoreFile(BaseModel):
    id: str
    object: str = "vector_store.file"
    vector_store_id: str
    status: str = "completed"
    created_at: int | None = None
