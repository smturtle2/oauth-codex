from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest

from oauth_codex.auth import (
    build_authorize_url,
    generate_pkce_pair,
    parse_callback_url,
)
from oauth_codex.errors import OAuthCallbackParseError, OAuthStateMismatchError
from oauth_codex.types import OAuthConfig


def test_generate_pkce_pair_length_and_challenge_shape() -> None:
    verifier, challenge = generate_pkce_pair()
    assert 43 <= len(verifier) <= 128
    assert len(challenge) >= 43
    assert "=" not in verifier
    assert "=" not in challenge


def test_build_authorize_url_contains_expected_params() -> None:
    config = OAuthConfig(
        client_id="cid",
        scope="openid profile",
        audience="aud",
        redirect_uri="http://localhost:1455/callback",
        authorization_endpoint="https://auth.example.com/oauth/authorize",
    )

    url = build_authorize_url(config=config, state="state-1", code_challenge="cc-1")
    parsed = urlparse(url)
    q = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "auth.example.com"
    assert q["response_type"] == ["code"]
    assert q["client_id"] == ["cid"]
    assert q["scope"] == ["openid profile"]
    assert q["state"] == ["state-1"]
    assert q["code_challenge"] == ["cc-1"]
    assert q["code_challenge_method"] == ["S256"]
    assert q["redirect_uri"] == ["http://localhost:1455/callback"]
    assert q["audience"] == ["aud"]


def test_parse_callback_url_success() -> None:
    callback = "http://localhost:1455/callback?code=abc123&state=s1"
    code = parse_callback_url(callback_url=callback, expected_state="s1")
    assert code == "abc123"


def test_parse_callback_url_state_mismatch() -> None:
    callback = "http://localhost:1455/callback?code=abc123&state=wrong"
    with pytest.raises(OAuthStateMismatchError):
        parse_callback_url(callback_url=callback, expected_state="s1")


def test_parse_callback_url_missing_code() -> None:
    callback = "http://localhost:1455/callback?state=s1"
    with pytest.raises(OAuthCallbackParseError):
        parse_callback_url(callback_url=callback, expected_state="s1")
