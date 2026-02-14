from __future__ import annotations

from typing import Any

from .._models import BaseModel


class FileObject(BaseModel):
    id: str
    object: str = "file"
    bytes: int | None = None
    created_at: int | None = None
    filename: str | None = None
    purpose: str | None = None
    metadata: dict[str, Any] | None = None
