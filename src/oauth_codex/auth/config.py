from __future__ import annotations

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
