from __future__ import annotations

from typing import Any

from .._resource import AsyncAPIResource, SyncAPIResource
from ._unsupported import raise_unsupported
from ._wrappers import (
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
)
from ..types.shared import ModelCapabilities


class Models(SyncAPIResource):
    def capabilities(self, model: str) -> ModelCapabilities:
        caps = self._client._engine.model_capabilities(model)
        return ModelCapabilities(
            supports_reasoning=bool(caps.supports_reasoning),
            supports_tools=bool(caps.supports_tools),
            supports_store=bool(caps.supports_store),
            supports_response_format=bool(caps.supports_response_format),
        )

    def retrieve(self, model: str, **_: Any) -> dict[str, Any]:
        caps = self.capabilities(model)
        return {
            "id": model,
            "object": "model",
            "owned_by": "oauth-codex",
            "capabilities": caps.to_dict(),
        }

    def list(self, **_: Any) -> dict[str, Any]:
        return {
            "object": "list",
            "data": [self.retrieve("gpt-5.3-codex")],
        }

    def delete(self, *_: Any, **__: Any) -> None:
        raise_unsupported("models.delete")

    @property
    def with_raw_response(self) -> ModelsWithRawResponse:
        return ModelsWithRawResponse(self)

    @property
    def with_streaming_response(self) -> ModelsWithStreamingResponse:
        return ModelsWithStreamingResponse(self)


class AsyncModels(AsyncAPIResource):
    async def capabilities(self, model: str) -> ModelCapabilities:
        caps = self._client._engine.model_capabilities(model)
        return ModelCapabilities(
            supports_reasoning=bool(caps.supports_reasoning),
            supports_tools=bool(caps.supports_tools),
            supports_store=bool(caps.supports_store),
            supports_response_format=bool(caps.supports_response_format),
        )

    async def retrieve(self, model: str, **_: Any) -> dict[str, Any]:
        caps = await self.capabilities(model)
        return {
            "id": model,
            "object": "model",
            "owned_by": "oauth-codex",
            "capabilities": caps.to_dict(),
        }

    async def list(self, **_: Any) -> dict[str, Any]:
        return {
            "object": "list",
            "data": [await self.retrieve("gpt-5.3-codex")],
        }

    async def delete(self, *_: Any, **__: Any) -> None:
        raise_unsupported("models.delete")

    @property
    def with_raw_response(self) -> AsyncModelsWithRawResponse:
        return AsyncModelsWithRawResponse(self)

    @property
    def with_streaming_response(self) -> AsyncModelsWithStreamingResponse:
        return AsyncModelsWithStreamingResponse(self)


class ModelsWithRawResponse:
    def __init__(self, models: Models) -> None:
        self.capabilities = to_raw_response_wrapper(models.capabilities)
        self.retrieve = to_raw_response_wrapper(models.retrieve)
        self.list = to_raw_response_wrapper(models.list)
        self.delete = to_raw_response_wrapper(models.delete)


class AsyncModelsWithRawResponse:
    def __init__(self, models: AsyncModels) -> None:
        self.capabilities = async_to_raw_response_wrapper(models.capabilities)
        self.retrieve = async_to_raw_response_wrapper(models.retrieve)
        self.list = async_to_raw_response_wrapper(models.list)
        self.delete = async_to_raw_response_wrapper(models.delete)


class ModelsWithStreamingResponse:
    def __init__(self, models: Models) -> None:
        self.capabilities = to_streamed_response_wrapper(models.capabilities)
        self.retrieve = to_streamed_response_wrapper(models.retrieve)
        self.list = to_streamed_response_wrapper(models.list)
        self.delete = to_streamed_response_wrapper(models.delete)


class AsyncModelsWithStreamingResponse:
    def __init__(self, models: AsyncModels) -> None:
        self.capabilities = async_to_streamed_response_wrapper(models.capabilities)
        self.retrieve = async_to_streamed_response_wrapper(models.retrieve)
        self.list = async_to_streamed_response_wrapper(models.list)
        self.delete = async_to_streamed_response_wrapper(models.delete)
