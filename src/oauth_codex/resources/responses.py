from __future__ import annotations

from typing import Any

from oauth_codex._models import BaseModel


class Response(BaseModel):
    pass


class Responses:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, **json_data: Any) -> Response:
        response = self._client.request("POST", "/responses", json_data=json_data)
        return Response.from_dict(response.json())


class AsyncResponses:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(self, **json_data: Any) -> Response:
        response = await self._client.request("POST", "/responses", json_data=json_data)
        return Response.from_dict(response.json())
