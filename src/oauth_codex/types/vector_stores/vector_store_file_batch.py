from __future__ import annotations

from ..._models import BaseModel


class VectorStoreFileBatch(BaseModel):
    id: str
    object: str = "vector_store.file_batch"
    vector_store_id: str
    status: str = "completed"
    created_at: int | None = None
    file_counts: dict[str, int] | None = None
