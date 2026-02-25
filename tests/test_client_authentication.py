from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import Client
from oauth_codex.core_types import OAuthTokens


def _tokens() -> OAuthTokens:
    return OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)


def test_client_constructs_without_authentication_side_effects() -> None:
    Client(token_store=InMemoryTokenStore(_tokens()))


def test_client_no_longer_supports_authenticate_on_init_flag() -> None:
    with pytest.raises(TypeError):
        Client(token_store=InMemoryTokenStore(), authenticate_on_init=True)
