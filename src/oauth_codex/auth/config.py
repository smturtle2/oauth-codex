from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class OAuthConfig:
    client_id: str = "app_EMoamEEZ73f0CkXaXp7hrann"
    scope: str = "openid profile email offline_access"
    audience: str | None = None
    redirect_uri: str = "http://localhost:1455/auth/callback"
    discovery_url: str = "https://auth.openai.com/.well-known/oauth-authorization-server"
    authorization_endpoint: str = "https://auth.openai.com/oauth/authorize"
    token_endpoint: str = "https://auth.openai.com/oauth/token"
    originator: str = "codex_cli_rs"


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
