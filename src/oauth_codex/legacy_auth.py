from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from .errors import (
    OAuthCallbackParseError,
    OAuthStateMismatchError,
    TokenExchangeError,
    TokenRefreshError,
)
from .legacy_types import OAuthConfig, OAuthTokens


def load_oauth_config(override: OAuthConfig | None = None) -> OAuthConfig:
    base = override or OAuthConfig()
    return OAuthConfig(
        client_id=os.getenv("CODEX_OAUTH_CLIENT_ID", base.client_id),
        scope=os.getenv("CODEX_OAUTH_SCOPE", base.scope),
        audience=os.getenv("CODEX_OAUTH_AUDIENCE", base.audience or "") or None,
        redirect_uri=os.getenv("CODEX_OAUTH_REDIRECT_URI", base.redirect_uri),
        discovery_url=os.getenv("CODEX_OAUTH_DISCOVERY_URL", base.discovery_url),
        authorization_endpoint=os.getenv(
            "CODEX_OAUTH_AUTHORIZATION_ENDPOINT", base.authorization_endpoint
        ),
        token_endpoint=os.getenv("CODEX_OAUTH_TOKEN_ENDPOINT", base.token_endpoint),
        originator=os.getenv("CODEX_OAUTH_ORIGINATOR", base.originator),
    )


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


def discover_endpoints(client: httpx.Client, config: OAuthConfig) -> OAuthConfig:
    try:
        response = client.get(config.discovery_url)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return config

    auth_endpoint = payload.get("authorization_endpoint") or config.authorization_endpoint
    token_endpoint = payload.get("token_endpoint") or config.token_endpoint

    return OAuthConfig(
        client_id=config.client_id,
        scope=config.scope,
        audience=config.audience,
        redirect_uri=config.redirect_uri,
        discovery_url=config.discovery_url,
        authorization_endpoint=auth_endpoint,
        token_endpoint=token_endpoint,
        originator=config.originator,
    )


async def discover_endpoints_async(client: httpx.AsyncClient, config: OAuthConfig) -> OAuthConfig:
    try:
        response = await client.get(config.discovery_url)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return config

    auth_endpoint = payload.get("authorization_endpoint") or config.authorization_endpoint
    token_endpoint = payload.get("token_endpoint") or config.token_endpoint

    return OAuthConfig(
        client_id=config.client_id,
        scope=config.scope,
        audience=config.audience,
        redirect_uri=config.redirect_uri,
        discovery_url=config.discovery_url,
        authorization_endpoint=auth_endpoint,
        token_endpoint=token_endpoint,
        originator=config.originator,
    )


def parse_callback_url(callback_url: str, expected_state: str) -> str:
    try:
        parsed = urlparse(callback_url.strip())
    except Exception as exc:
        raise OAuthCallbackParseError("Failed to parse callback URL") from exc

    query = parse_qs(parsed.query)

    if "error" in query:
        err = query.get("error", [""])[0]
        desc = query.get("error_description", [""])[0]
        raise OAuthCallbackParseError(f"OAuth callback returned error: {err} {desc}".strip())

    code = query.get("code", [None])[0]
    state = query.get("state", [None])[0]

    if not code:
        raise OAuthCallbackParseError("OAuth callback is missing authorization code")
    if state != expected_state:
        raise OAuthStateMismatchError("OAuth callback state mismatch")

    return code


def _build_tokens(payload: dict[str, Any]) -> OAuthTokens:
    expires_in = payload.get("expires_in")
    expires_at = None
    if isinstance(expires_in, (int, float)):
        expires_at = time.time() + float(expires_in)

    id_token = payload.get("id_token")
    access_token = payload.get("access_token")
    account_id = payload.get("account_id")
    if not account_id:
        account_id = _extract_chatgpt_account_id(id_token)
    if not account_id:
        account_id = _extract_chatgpt_account_id(access_token)

    return OAuthTokens(
        access_token=payload["access_token"],
        api_key=None,
        refresh_token=payload.get("refresh_token"),
        id_token=id_token,
        token_type=payload.get("token_type", "Bearer"),
        scope=payload.get("scope"),
        expires_at=expires_at,
        account_id=account_id,
        last_refresh=time.time(),
    )


def _extract_chatgpt_account_id(jwt_token: str | None) -> str | None:
    if not jwt_token or "." not in jwt_token:
        return None
    parts = jwt_token.split(".")
    if len(parts) < 2:
        return None
    payload_b64 = parts[1]
    padding = "=" * (-len(payload_b64) % 4)
    try:
        raw = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None

    auth_claims = payload.get("https://api.openai.com/auth")
    if isinstance(auth_claims, dict):
        account = auth_claims.get("chatgpt_account_id") or auth_claims.get("account_id")
        if isinstance(account, str) and account:
            return account
    return None


def exchange_code_for_tokens(
    client: httpx.Client,
    config: OAuthConfig,
    code: str,
    code_verifier: str,
) -> OAuthTokens:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
        "code_verifier": code_verifier,
    }

    if config.audience:
        data["audience"] = config.audience

    response = client.post(config.token_endpoint, data=data)
    if response.status_code >= 400:
        detail = _extract_oauth_error(response)
        raise TokenExchangeError(f"OAuth token exchange failed: {detail}")

    payload = response.json()
    if "access_token" not in payload:
        raise TokenExchangeError("OAuth token exchange failed: access_token missing")
    return _build_tokens(payload)


def refresh_tokens(
    client: httpx.Client,
    config: OAuthConfig,
    tokens: OAuthTokens,
) -> OAuthTokens:
    if not tokens.refresh_token:
        raise TokenRefreshError("No refresh_token available")

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": tokens.refresh_token,
        "client_id": config.client_id,
        "scope": "openid profile email",
    }

    response = client.post(config.token_endpoint, json=payload)
    if response.status_code >= 400:
        detail = _extract_oauth_error(response)
        raise TokenRefreshError(f"OAuth token refresh failed: {detail}")

    payload = response.json()
    if "access_token" not in payload:
        raise TokenRefreshError("OAuth token refresh failed: access_token missing")

    new_tokens = _build_tokens(payload)
    if not new_tokens.refresh_token:
        new_tokens.refresh_token = tokens.refresh_token
    if not new_tokens.account_id:
        new_tokens.account_id = tokens.account_id
    if not new_tokens.id_token:
        new_tokens.id_token = tokens.id_token
    if not new_tokens.api_key:
        new_tokens.api_key = tokens.api_key
    return new_tokens


async def refresh_tokens_async(
    client: httpx.AsyncClient,
    config: OAuthConfig,
    tokens: OAuthTokens,
) -> OAuthTokens:
    if not tokens.refresh_token:
        raise TokenRefreshError("No refresh_token available")

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": tokens.refresh_token,
        "client_id": config.client_id,
        "scope": "openid profile email",
    }

    response = await client.post(config.token_endpoint, json=payload)
    if response.status_code >= 400:
        detail = _extract_oauth_error(response)
        raise TokenRefreshError(f"OAuth token refresh failed: {detail}")

    payload = response.json()
    if "access_token" not in payload:
        raise TokenRefreshError("OAuth token refresh failed: access_token missing")

    new_tokens = _build_tokens(payload)
    if not new_tokens.refresh_token:
        new_tokens.refresh_token = tokens.refresh_token
    if not new_tokens.account_id:
        new_tokens.account_id = tokens.account_id
    if not new_tokens.id_token:
        new_tokens.id_token = tokens.id_token
    if not new_tokens.api_key:
        new_tokens.api_key = tokens.api_key
    return new_tokens


def _extract_oauth_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        return f"status={response.status_code}"

    if isinstance(payload, dict):
        error = payload.get("error")
        desc = payload.get("error_description") or payload.get("message")
        text = " ".join([part for part in [str(error) if error else "", str(desc) if desc else ""] if part])
        return text or f"status={response.status_code}"
    return f"status={response.status_code}"
