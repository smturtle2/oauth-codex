from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ._client import OAuthCodexClient
from .auth.config import OAuthConfig

if TYPE_CHECKING:
    from .resources.files import Files
    from .resources.models import Models
    from .resources.responses.responses import Responses
    from .resources.vector_stores.vector_stores import VectorStores

# Module-level configurable options.
oauth_client_id: str | None = None
oauth_scope: str | None = None
oauth_audience: str | None = None
oauth_redirect_uri: str | None = None
oauth_discovery_url: str | None = None
oauth_authorization_endpoint: str | None = None
oauth_token_endpoint: str | None = None
oauth_originator: str | None = None

base_url: str | None = None
timeout: float = 60.0
max_retries: int = 2
default_headers: dict[str, str] | None = None
default_query: dict[str, object] | None = None
http_client: Any | None = None

_client: OAuthCodexClient | None = None


def _build_oauth_config() -> OAuthConfig:
    config = OAuthConfig()
    if oauth_client_id is not None:
        config.client_id = oauth_client_id
    if oauth_scope is not None:
        config.scope = oauth_scope
    if oauth_audience is not None:
        config.audience = oauth_audience
    if oauth_redirect_uri is not None:
        config.redirect_uri = oauth_redirect_uri
    if oauth_discovery_url is not None:
        config.discovery_url = oauth_discovery_url
    if oauth_authorization_endpoint is not None:
        config.authorization_endpoint = oauth_authorization_endpoint
    if oauth_token_endpoint is not None:
        config.token_endpoint = oauth_token_endpoint
    if oauth_originator is not None:
        config.originator = oauth_originator
    return config


def _load_client() -> OAuthCodexClient:
    global _client
    if _client is None:
        _client = OAuthCodexClient(
            oauth_config=_build_oauth_config(),
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            default_query=default_query,
            http_client=http_client,
        )
    return _client


def _reset_client() -> None:
    global _client
    _client = None


class LazyProxy:
    def __init__(self, attr: str) -> None:
        self._attr = attr

    def __getattr__(self, name: str) -> Any:
        target = getattr(_load_client(), self._attr)
        return getattr(target, name)


if TYPE_CHECKING:
    responses: Responses = cast(Responses, LazyProxy("responses"))
    files: Files = cast(Files, LazyProxy("files"))
    vector_stores: VectorStores = cast(VectorStores, LazyProxy("vector_stores"))
    models: Models = cast(Models, LazyProxy("models"))
else:
    responses = LazyProxy("responses")
    files = LazyProxy("files")
    vector_stores = LazyProxy("vector_stores")
    models = LazyProxy("models")
