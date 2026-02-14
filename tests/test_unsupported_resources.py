from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import NotSupportedError, OAuthCodexClient
from oauth_codex.legacy_types import OAuthTokens


def _client() -> OAuthCodexClient:
    return OAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )


def test_unsupported_resource_raises_not_supported() -> None:
    client = _client()

    with pytest.raises(NotSupportedError):
        client.images.generate(prompt="draw a cat")

    with pytest.raises(NotSupportedError):
        client.embeddings.create(input="hello", model="text-embedding-3-small")


def test_with_raw_and_streaming_present_on_unsupported() -> None:
    client = _client()
    raw = client.images.with_raw_response
    streaming = client.images.with_streaming_response
    assert raw is not None
    assert streaming is not None
