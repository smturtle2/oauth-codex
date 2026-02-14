from __future__ import annotations

from .._models import BaseModel


class FileDeleted(BaseModel):
    id: str
    object: str = "file.deleted"
    deleted: bool = True
