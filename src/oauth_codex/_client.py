from __future__ import annotations

import asyncio
from typing import Any, Mapping

from ._base_client import AsyncAPIClient, SyncAPIClient
from .auth.config import OAuthConfig
from .client import OAuthCodexClient as _LegacyEngine
from .resources.audio.audio import AsyncAudio, Audio
from .resources.batches import AsyncBatches, Batches
from .resources.beta.beta import AsyncBeta, Beta
from .resources.chat.chat import AsyncChat, Chat
from .resources.completions import AsyncCompletions, Completions
from .resources.containers.containers import AsyncContainers, Containers
from .resources.conversations.conversations import AsyncConversations, Conversations
from .resources.embeddings import AsyncEmbeddings, Embeddings
from .resources.evals.evals import AsyncEvals, Evals
from .resources.files import (
    AsyncFiles,
    AsyncFilesWithRawResponse,
    AsyncFilesWithStreamingResponse,
    Files,
    FilesWithRawResponse,
    FilesWithStreamingResponse,
)
from .resources.fine_tuning.fine_tuning import AsyncFineTuning, FineTuning
from .resources.images import AsyncImages, Images
from .resources.models import (
    AsyncModels,
    AsyncModelsWithRawResponse,
    AsyncModelsWithStreamingResponse,
    Models,
    ModelsWithRawResponse,
    ModelsWithStreamingResponse,
)
from .resources.moderations import AsyncModerations, Moderations
from .resources.realtime.realtime import AsyncRealtime, Realtime
from .resources.responses.responses import (
    AsyncResponses,
    AsyncResponsesWithRawResponse,
    AsyncResponsesWithStreamingResponse,
    Responses,
    ResponsesWithRawResponse,
    ResponsesWithStreamingResponse,
)
from .resources.uploads.uploads import AsyncUploads, Uploads
from .resources.vector_stores.vector_stores import (
    AsyncVectorStores,
    AsyncVectorStoresWithRawResponse,
    AsyncVectorStoresWithStreamingResponse,
    VectorStores,
    VectorStoresWithRawResponse,
    VectorStoresWithStreamingResponse,
)
from .resources.videos import AsyncVideos, Videos
from .resources.webhooks import AsyncWebhooks, Webhooks
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

        resolved_base_url = (base_url or chatgpt_base_url or "https://chatgpt.com/backend-api/codex").rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self._engine = _LegacyEngine(
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
    def completions(self) -> Completions:
        return Completions(self)

    @property
    def chat(self) -> Chat:
        return Chat(self)

    @property
    def embeddings(self) -> Embeddings:
        return Embeddings(self)

    @property
    def images(self) -> Images:
        return Images(self)

    @property
    def audio(self) -> Audio:
        return Audio(self)

    @property
    def moderations(self) -> Moderations:
        return Moderations(self)

    @property
    def fine_tuning(self) -> FineTuning:
        return FineTuning(self)

    @property
    def webhooks(self) -> Webhooks:
        return Webhooks(self)

    @property
    def beta(self) -> Beta:
        return Beta(self)

    @property
    def batches(self) -> Batches:
        return Batches(self)

    @property
    def uploads(self) -> Uploads:
        return Uploads(self)

    @property
    def realtime(self) -> Realtime:
        return Realtime(self)

    @property
    def conversations(self) -> Conversations:
        return Conversations(self)

    @property
    def evals(self) -> Evals:
        return Evals(self)

    @property
    def containers(self) -> Containers:
        return Containers(self)

    @property
    def videos(self) -> Videos:
        return Videos(self)

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

        resolved_base_url = (base_url or chatgpt_base_url or "https://chatgpt.com/backend-api/codex").rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self._engine = _LegacyEngine(
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
    def completions(self) -> AsyncCompletions:
        return AsyncCompletions(self)

    @property
    def chat(self) -> AsyncChat:
        return AsyncChat(self)

    @property
    def embeddings(self) -> AsyncEmbeddings:
        return AsyncEmbeddings(self)

    @property
    def images(self) -> AsyncImages:
        return AsyncImages(self)

    @property
    def audio(self) -> AsyncAudio:
        return AsyncAudio(self)

    @property
    def moderations(self) -> AsyncModerations:
        return AsyncModerations(self)

    @property
    def fine_tuning(self) -> AsyncFineTuning:
        return AsyncFineTuning(self)

    @property
    def webhooks(self) -> AsyncWebhooks:
        return AsyncWebhooks(self)

    @property
    def beta(self) -> AsyncBeta:
        return AsyncBeta(self)

    @property
    def batches(self) -> AsyncBatches:
        return AsyncBatches(self)

    @property
    def uploads(self) -> AsyncUploads:
        return AsyncUploads(self)

    @property
    def realtime(self) -> AsyncRealtime:
        return AsyncRealtime(self)

    @property
    def conversations(self) -> AsyncConversations:
        return AsyncConversations(self)

    @property
    def evals(self) -> AsyncEvals:
        return AsyncEvals(self)

    @property
    def containers(self) -> AsyncContainers:
        return AsyncContainers(self)

    @property
    def videos(self) -> AsyncVideos:
        return AsyncVideos(self)

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
