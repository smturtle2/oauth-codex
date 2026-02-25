from __future__ import annotations

from typing import Any

from oauth_codex._models import BaseModel


class Model(BaseModel):
    id: str
    object: str = "model"
    owned_by: str | None = None


class ModelList(BaseModel):
    object: str = "list"
    data: list[Model]


class Models:
    def __init__(self, client: Any) -> None:
        self._client = client

    def retrieve(self, model: str) -> Model:
        response = self._client.request("GET", f"/models/{model}")
        return Model.from_dict(response.json())

    def list(self) -> ModelList:
        response = self._client.request("GET", "/models")
        return ModelList.from_dict(response.json())


class AsyncModels:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def retrieve(self, model: str) -> Model:
        response = await self._client.request("GET", f"/models/{model}")
        return Model.from_dict(response.json())

    async def list(self) -> ModelList:
        response = await self._client.request("GET", "/models")
        return ModelList.from_dict(response.json())
