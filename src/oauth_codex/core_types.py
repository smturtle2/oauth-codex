"""Core public data types used by oauth-codex.

`Message` represents a single Responses API input message dictionary, and
`listMessage` is the list container commonly passed to resource methods such as
`client.chat.completions.create(...)` and `client.responses.create(...)`.

Recommended minimal message shape:

    [{"role": "user", "content": "hello"}]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Protocol, TypeAlias

#: A single response input message item (for example role/content dict).
Message: TypeAlias = dict[str, Any]
#: List of response input messages accepted by resource-style client methods.
listMessage: TypeAlias = list[Message]
ValidationMode: TypeAlias = Literal["warn", "error", "ignore"]
TruncationMode: TypeAlias = Literal["auto", "disabled"]


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
class ToolResult:
    tool_call_id: str
    name: str
    output: dict[str, Any]


ToolSchema = dict[str, Any]
ToolInput: TypeAlias = ToolSchema | Callable[..., Any]


class TokenStore(Protocol):
    def load(self) -> OAuthTokens | None:
        ...

    def save(self, tokens: OAuthTokens) -> None:
        ...

    def delete(self) -> None:
        ...
