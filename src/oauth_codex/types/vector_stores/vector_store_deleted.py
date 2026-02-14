from __future__ import annotations

from ..._models import BaseModel


class VectorStoreDeleted(BaseModel):
    id: str
    object: str = "vector_store.deleted"
    deleted: bool = True
