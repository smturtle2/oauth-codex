from __future__ import annotations

from dataclasses import replace

import pytest

from oauth_codex.types import OAuthConfig, OAuthTokens


class InMemoryTokenStore:
    def __init__(self, tokens: OAuthTokens | None = None) -> None:
        self.tokens = tokens

    def load(self) -> OAuthTokens | None:
        return self.tokens

    def save(self, tokens: OAuthTokens) -> None:
        self.tokens = replace(tokens)

    def delete(self) -> None:
        self.tokens = None


@pytest.fixture
def valid_tokens() -> OAuthTokens:
    return OAuthTokens(
        access_token="access-1",
        api_key="sk-test",
        refresh_token="refresh-1",
        token_type="Bearer",
        expires_at=9_999_999_999,
    )


@pytest.fixture
def oauth_config() -> OAuthConfig:
    return OAuthConfig(client_id="test-client")
