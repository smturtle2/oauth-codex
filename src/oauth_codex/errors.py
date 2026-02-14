from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


class ParameterValidationError(CodexOAuthLLMError):
    pass


class ContinuityError(CodexOAuthLLMError):
    pass


class NotSupportedError(LLMRequestError):
    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class TokenStoreError(CodexOAuthLLMError):
    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class TokenStoreReadError(TokenStoreError):
    pass


class TokenStoreWriteError(TokenStoreError):
    pass


class TokenStoreDeleteError(TokenStoreError):
    pass


class SDKRequestError(LLMRequestError):
    def __init__(
        self,
        *,
        status_code: int | None,
        provider_code: str | None,
        user_message: str,
        retryable: bool,
        request_id: str | None = None,
        raw_error: Any = None,
    ) -> None:
        super().__init__(user_message)
        self.status_code = status_code
        self.provider_code = provider_code
        self.user_message = user_message
        self.retryable = retryable
        self.request_id = request_id
        self.raw_error = raw_error

    def __str__(self) -> str:
        code = f"{self.provider_code}: " if self.provider_code else ""
        status = f"HTTP {self.status_code}: " if self.status_code is not None else ""
        return f"{status}{code}{self.user_message}"


@dataclass
class ToolCallRequiredError(CodexOAuthLLMError):
    message: str
    tool_calls: list[ToolCall]

    def __str__(self) -> str:
        return self.message
