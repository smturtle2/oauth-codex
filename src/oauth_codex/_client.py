from __future__ import annotations

import asyncio
from typing import Any, Mapping

from ._base_client import AsyncAPIClient, SyncAPIClient
from .auth.config import OAuthConfig
from ._engine import OAuthCodexClient as _EngineClient
from .resources.files import (
    AsyncFiles,
    AsyncFilesWithRawResponse,
    AsyncFilesWithStreamingResponse,
    Files,
    FilesWithRawResponse,
    FilesWithStreamingResponse,
)
from .resources.models import (
    AsyncModels,
    AsyncModelsWithRawResponse,
    AsyncModelsWithStreamingResponse,
    Models,
    ModelsWithRawResponse,
    ModelsWithStreamingResponse,
)
from .resources.responses.responses import (
    AsyncResponses,
    AsyncResponsesWithRawResponse,
    AsyncResponsesWithStreamingResponse,
    Responses,
    ResponsesWithRawResponse,
    ResponsesWithStreamingResponse,
)
from .resources.vector_stores.vector_stores import (
    AsyncVectorStores,
    AsyncVectorStoresWithRawResponse,
    AsyncVectorStoresWithStreamingResponse,
    VectorStores,
    VectorStoresWithRawResponse,
    VectorStoresWithStreamingResponse,
)
from .store import FallbackTokenStore


class OAuthCodexClient(SyncAPIClient):
    def __init__(
        self,
        *,
        oauth_config: OAuthConfig | None = None,
        token_store: Any | None = None,
        base_url: str | None = None,
        chatgpt_base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        validation_mode: str = "warn",
        store_behavior: str = "auto_disable",
        compat_storage_dir: str | None = None,
        on_request_start: Any | None = None,
        on_request_end: Any | None = None,
        on_auth_refresh: Any | None = None,
        on_error: Any | None = None,
        http_client: Any | None = None,
        **_: Any,
    ) -> None:
        super().__init__()
        _ = default_headers, default_query, http_client

        resolved_base_url = (
            base_url or chatgpt_base_url or "https://chatgpt.com/backend-api/codex"
        ).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self._engine = _EngineClient(
            oauth_config=oauth_config,
            token_store=token_store or FallbackTokenStore(),
            chatgpt_base_url=resolved_base_url,
            timeout=timeout,
            validation_mode=validation_mode,
            store_behavior=store_behavior,
            max_retries=max_retries,
            compat_storage_dir=compat_storage_dir,
            on_request_start=on_request_start,
            on_request_end=on_request_end,
            on_auth_refresh=on_auth_refresh,
            on_error=on_error,
        )
        self._vector_file_batches: dict[str, dict[str, Any]] = {}

    @property
    def responses(self) -> Responses:
        return Responses(self)

    @property
    def files(self) -> Files:
        return Files(self)

    @property
    def vector_stores(self) -> VectorStores:
        return VectorStores(self)

    @property
    def models(self) -> Models:
        return Models(self)

    @property
    def with_raw_response(self) -> OAuthCodexClientWithRawResponse:
        return OAuthCodexClientWithRawResponse(self)

    @property
    def with_streaming_response(self) -> OAuthCodexClientWithStreamingResponse:
        return OAuthCodexClientWithStreamingResponse(self)

    def is_authenticated(self) -> bool:
        return self._engine.is_authenticated()

    def is_expired(self, *, leeway_seconds: int = 60) -> bool:
        return self._engine.is_expired(leeway_seconds=leeway_seconds)

    def refresh_if_needed(self, *, force: bool = False) -> bool:
        return self._engine.refresh_if_needed(force=force)

    def login(self) -> None:
        self._engine.login()


class AsyncOAuthCodexClient(AsyncAPIClient):
    def __init__(
        self,
        *,
        oauth_config: OAuthConfig | None = None,
        token_store: Any | None = None,
        base_url: str | None = None,
        chatgpt_base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        validation_mode: str = "warn",
        store_behavior: str = "auto_disable",
        compat_storage_dir: str | None = None,
        on_request_start: Any | None = None,
        on_request_end: Any | None = None,
        on_auth_refresh: Any | None = None,
        on_error: Any | None = None,
        http_client: Any | None = None,
        **_: Any,
    ) -> None:
        super().__init__()
        _ = default_headers, default_query, http_client

        resolved_base_url = (
            base_url or chatgpt_base_url or "https://chatgpt.com/backend-api/codex"
        ).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self._engine = _EngineClient(
            oauth_config=oauth_config,
            token_store=token_store or FallbackTokenStore(),
            chatgpt_base_url=resolved_base_url,
            timeout=timeout,
            validation_mode=validation_mode,
            store_behavior=store_behavior,
            max_retries=max_retries,
            compat_storage_dir=compat_storage_dir,
            on_request_start=on_request_start,
            on_request_end=on_request_end,
            on_auth_refresh=on_auth_refresh,
            on_error=on_error,
        )
        self._vector_file_batches: dict[str, dict[str, Any]] = {}

    @property
    def responses(self) -> AsyncResponses:
        return AsyncResponses(self)

    @property
    def files(self) -> AsyncFiles:
        return AsyncFiles(self)

    @property
    def vector_stores(self) -> AsyncVectorStores:
        return AsyncVectorStores(self)

    @property
    def models(self) -> AsyncModels:
        return AsyncModels(self)

    @property
    def with_raw_response(self) -> AsyncOAuthCodexClientWithRawResponse:
        return AsyncOAuthCodexClientWithRawResponse(self)

    @property
    def with_streaming_response(self) -> AsyncOAuthCodexClientWithStreamingResponse:
        return AsyncOAuthCodexClientWithStreamingResponse(self)

    def is_authenticated(self) -> bool:
        return self._engine.is_authenticated()

    def is_expired(self, *, leeway_seconds: int = 60) -> bool:
        return self._engine.is_expired(leeway_seconds=leeway_seconds)

    async def refresh_if_needed(self, *, force: bool = False) -> bool:
        return await self._engine.arefresh_if_needed(force=force)

    async def login(self) -> None:
        await asyncio.to_thread(self._engine.login)


class OAuthCodexClientWithRawResponse:
    def __init__(self, client: OAuthCodexClient) -> None:
        self.responses = ResponsesWithRawResponse(client.responses)
        self.files = FilesWithRawResponse(client.files)
        self.vector_stores = VectorStoresWithRawResponse(client.vector_stores)
        self.models = ModelsWithRawResponse(client.models)


class AsyncOAuthCodexClientWithRawResponse:
    def __init__(self, client: AsyncOAuthCodexClient) -> None:
        self.responses = AsyncResponsesWithRawResponse(client.responses)
        self.files = AsyncFilesWithRawResponse(client.files)
        self.vector_stores = AsyncVectorStoresWithRawResponse(client.vector_stores)
        self.models = AsyncModelsWithRawResponse(client.models)


class OAuthCodexClientWithStreamingResponse:
    def __init__(self, client: OAuthCodexClient) -> None:
        self.responses = ResponsesWithStreamingResponse(client.responses)
        self.files = FilesWithStreamingResponse(client.files)
        self.vector_stores = VectorStoresWithStreamingResponse(client.vector_stores)
        self.models = ModelsWithStreamingResponse(client.models)


class AsyncOAuthCodexClientWithStreamingResponse:
    def __init__(self, client: AsyncOAuthCodexClient) -> None:
        self.responses = AsyncResponsesWithStreamingResponse(client.responses)
        self.files = AsyncFilesWithStreamingResponse(client.files)
        self.vector_stores = AsyncVectorStoresWithStreamingResponse(client.vector_stores)
        self.models = AsyncModelsWithStreamingResponse(client.models)


Client = OAuthCodexClient
AsyncClient = AsyncOAuthCodexClient
