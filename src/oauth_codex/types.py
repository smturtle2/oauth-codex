from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Protocol, TypeAlias

Message: TypeAlias = dict[str, Any]
ValidationMode: TypeAlias = Literal["warn", "error", "ignore"]
StoreBehavior: TypeAlias = Literal["auto_disable", "error", "passthrough"]
TruncationMode: TypeAlias = Literal["auto", "disabled"]


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
    output_tokens: int | None = None
    total_tokens: int | None = None
    cached_tokens: int | None = None
    reasoning_tokens: int | None = None
    # Backward-compatible aliases
    cached_input_tokens: int | None = None
    reasoning_output_tokens: int | None = None

    def __post_init__(self) -> None:
        if self.cached_tokens is None and self.cached_input_tokens is not None:
            self.cached_tokens = self.cached_input_tokens
        if self.cached_input_tokens is None and self.cached_tokens is not None:
            self.cached_input_tokens = self.cached_tokens
        if self.reasoning_tokens is None and self.reasoning_output_tokens is not None:
            self.reasoning_tokens = self.reasoning_output_tokens
        if self.reasoning_output_tokens is None and self.reasoning_tokens is not None:
            self.reasoning_output_tokens = self.reasoning_tokens


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
    response_id: str | None = None


@dataclass
class StreamEvent:
    type: Literal[
        "response_started",
        "text_delta",
        "reasoning_delta",
        "reasoning_done",
        "tool_call_started",
        "tool_call_arguments_delta",
        "tool_call_delta",
        "tool_call_done",
        "usage",
        "response_completed",
        "done",
        "error",
    ]
    delta: str | None = None
    tool_call: ToolCall | None = None
    usage: TokenUsage | None = None
    raw: dict[str, Any] | None = None
    error: str | None = None
    call_id: str | None = None
    response_id: str | None = None
    finish_reason: str | None = None
    schema_version: str = "v1"


ToolSchema = dict[str, Any]
ToolInput: TypeAlias = ToolSchema | Callable[..., Any]


class TokenStore(Protocol):
    def load(self) -> OAuthTokens | None:
        ...

    def save(self, tokens: OAuthTokens) -> None:
        ...

    def delete(self) -> None:
        ...


@dataclass
class ModelCapabilities:
    supports_reasoning: bool = True
    supports_tools: bool = True
    supports_store: bool = False
    supports_response_format: bool = True


@dataclass
class ResponseCompat:
    id: str
    output: list[dict[str, Any]] = field(default_factory=list)
    output_text: str = ""
    usage: TokenUsage | None = None
    error: dict[str, Any] | None = None
    reasoning_summary: str | None = None
    reasoning_items: list[dict[str, Any]] = field(default_factory=list)
    encrypted_reasoning_content: str | None = None
    finish_reason: str | None = None
    previous_response_id: str | None = None
    raw_response: dict[str, Any] | None = None


@dataclass
class InputTokensCountResult:
    input_tokens: int
    cached_tokens: int | None = None
    total_tokens: int | None = None
