from __future__ import annotations

from conftest import InMemoryTokenStore
from oauth_codex import OAuthCodexClient
from oauth_codex.types import OAuthTokens


def test_model_capabilities_api() -> None:
    client = OAuthCodexClient(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )

    caps = client.models.capabilities("gpt-5.3-codex")

    assert caps.supports_reasoning is True
    assert caps.supports_tools is True
    assert caps.supports_response_format is True
    assert caps.supports_store is False
