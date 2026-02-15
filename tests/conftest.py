from __future__ import annotations

from dataclasses import replace

import pytest

from oauth_codex.core_types import OAuthTokens


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
        refresh_token="refresh-1",
        expires_at=9_999_999_999,
        token_type="Bearer",
        account_id="acct-1",
    )
