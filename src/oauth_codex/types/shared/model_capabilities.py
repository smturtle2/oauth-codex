from __future__ import annotations

from ..._models import BaseModel


class ModelCapabilities(BaseModel):
    supports_reasoning: bool = True
    supports_tools: bool = True
    supports_store: bool = False
    supports_response_format: bool = True
