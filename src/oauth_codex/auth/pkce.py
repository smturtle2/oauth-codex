from __future__ import annotations

import base64
import hashlib
import secrets
from urllib.parse import urlencode

from .config import OAuthConfig


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def generate_pkce_pair() -> tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(64))
    if len(verifier) < 43:
        verifier = (verifier + "A" * 43)[:43]
    if len(verifier) > 128:
        verifier = verifier[:128]

    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = _b64url(digest)
    return verifier, challenge


def generate_state() -> str:
    return _b64url(secrets.token_bytes(24))


def build_authorize_url(config: OAuthConfig, state: str, code_challenge: str) -> str:
    query = {
        "response_type": "code",
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
        "scope": config.scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "id_token_add_organizations": "true",
        "codex_cli_simplified_flow": "true",
        "originator": config.originator,
    }
    if config.audience:
        query["audience"] = config.audience
    return f"{config.authorization_endpoint}?{urlencode(query)}"


__all__ = ["build_authorize_url", "generate_pkce_pair", "generate_state"]
