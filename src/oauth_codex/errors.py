from __future__ import annotations

from dataclasses import dataclass

from .types import ToolCall


class CodexOAuthLLMError(RuntimeError):
    """Base exception for this SDK."""


class OAuthCallbackParseError(CodexOAuthLLMError):
    pass


class OAuthStateMismatchError(CodexOAuthLLMError):
    pass


class TokenExchangeError(CodexOAuthLLMError):
    pass


class TokenRefreshError(CodexOAuthLLMError):
    pass


class AuthRequiredError(CodexOAuthLLMError):
    pass


class ModelValidationError(CodexOAuthLLMError):
    pass


class LLMRequestError(CodexOAuthLLMError):
    pass


@dataclass
class ToolCallRequiredError(CodexOAuthLLMError):
    message: str
    tool_calls: list[ToolCall]

    def __str__(self) -> str:
        return self.message
