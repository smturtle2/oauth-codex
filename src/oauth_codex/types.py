from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Protocol, TypeAlias

Message: TypeAlias = dict[str, Any]


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


@dataclass
class OAuthTokens:
    access_token: str
    api_key: str | None = None
    refresh_token: str | None = None
    id_token: str | None = None
    token_type: str = "Bearer"
    scope: str | None = None
    expires_at: float | None = None
    account_id: str | None = None
    last_refresh: float | None = None

    def is_expired(self, *, leeway_seconds: int = 0) -> bool:
        if self.expires_at is None:
            return False
        import time

        return time.time() + max(leeway_seconds, 0) >= self.expires_at


@dataclass
class TokenUsage:
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class ToolCall:
    id: str
    name: str
    arguments_json: str
    arguments: dict[str, Any] | None = None


@dataclass
class ToolResult:
    tool_call_id: str
    name: str
    output: str | dict[str, Any]


@dataclass
class GenerateResult:
    text: str
    tool_calls: list[ToolCall]
    finish_reason: Literal["stop", "tool_calls", "length", "error"]
    usage: TokenUsage | None = None
    raw_response: dict[str, Any] | None = None


@dataclass
class StreamEvent:
    type: Literal[
        "text_delta",
        "tool_call_delta",
        "tool_call_done",
        "usage",
        "done",
        "error",
    ]
    delta: str | None = None
    tool_call: ToolCall | None = None
    usage: TokenUsage | None = None
    raw: dict[str, Any] | None = None
    error: str | None = None


ToolSchema = dict[str, Any]
ToolInput: TypeAlias = ToolSchema | Callable[..., Any]


class TokenStore(Protocol):
    def load(self) -> OAuthTokens | None:
        ...

    def save(self, tokens: OAuthTokens) -> None:
        ...

    def delete(self) -> None:
        ...
