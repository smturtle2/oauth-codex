from __future__ import annotations

from typing import Any

import httpx


class OAuthCodexError(Exception):
    """Base class for all public oauth-codex exceptions."""

    pass


class OpenAIError(OAuthCodexError):
    """Compatibility base error alias for OpenAI-style exception handling."""

    pass


CodexError = OAuthCodexError


class APIError(OpenAIError):
    """Base error for request/response failures returned by the API layer.

    Attributes:
        message: Human-readable error message.
        request: Originating `httpx.Request` when available.
        body: Raw parsed error body when available.
        code: Provider error code extracted from `body` when present.
        param: Provider parameter field extracted from `body` when present.
        type: Provider error type extracted from `body` when present.
    """

    def __init__(
        self,
        message: str,
        request: httpx.Request | None = None,
        *,
        body: object | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.request = request
        self.body = body
        self.code: str | None = None
        self.param: str | None = None
        self.type: str | None = None
        if isinstance(body, dict):
            raw_code = body.get("code")
            raw_param = body.get("param")
            raw_type = body.get("type")
            self.code = raw_code if isinstance(raw_code, str) else None
            self.param = raw_param if isinstance(raw_param, str) else None
            self.type = raw_type if isinstance(raw_type, str) else None


class APIStatusError(APIError):
    """HTTP status error with access to response metadata.

    Attributes:
        response: Full `httpx.Response`.
        status_code: HTTP status code from the response.
        request_id: Request identifier from `x-request-id` header when present.
    """

    def __init__(
        self, message: str, *, response: httpx.Response, body: object | None = None
    ) -> None:
        super().__init__(message, response.request, body=body)
        self.response = response
        self.status_code = response.status_code
        self.request_id = response.headers.get("x-request-id")


class APIConnectionError(APIError):
    """Network-level connection failure while talking to the API."""

    def __init__(
        self,
        *,
        message: str = "Connection error.",
        request: httpx.Request | None = None,
    ) -> None:
        super().__init__(message, request, body=None)


class APITimeoutError(APIConnectionError):
    """Request timeout while waiting for API response."""

    def __init__(self, request: httpx.Request | None = None) -> None:
        super().__init__(message="Request timed out.", request=request)


class BadRequestError(APIStatusError):
    """HTTP 400 response from the API."""

    pass


class AuthenticationError(APIStatusError):
    """HTTP 401 response from the API."""

    pass


class PermissionDeniedError(APIStatusError):
    """HTTP 403 response from the API."""

    pass


class NotFoundError(APIStatusError):
    """HTTP 404 response from the API."""

    pass


class ConflictError(APIStatusError):
    """HTTP 409 response from the API."""

    pass


class UnprocessableEntityError(APIStatusError):
    """HTTP 422 response from the API."""

    pass


class RateLimitError(APIStatusError):
    """HTTP 429 response from the API."""

    pass


class InternalServerError(APIStatusError):
    """HTTP 5xx server error returned by the API."""

    pass


class APIResponseValidationError(APIError):
    """API response payload failed SDK-side schema validation."""

    def __init__(
        self,
        response: httpx.Response,
        body: object | None,
        *,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message or "Data returned by API invalid for expected schema.",
            response.request,
            body=body,
        )
        self.response = response
        self.status_code = response.status_code


class OAuthCallbackParseError(OAuthCodexError):
    """OAuth browser callback could not be parsed."""

    pass


class OAuthStateMismatchError(OAuthCodexError):
    """OAuth callback state does not match the initiated login request."""

    pass


class TokenExchangeError(OAuthCodexError):
    """OAuth authorization code exchange for tokens failed."""

    pass


class TokenRefreshError(OAuthCodexError):
    """Refreshing an existing OAuth token failed."""

    pass


class AuthRequiredError(OAuthCodexError):
    """Authenticated call was attempted without valid credentials."""

    pass


class ParameterValidationError(OAuthCodexError):
    """Input parameters failed SDK validation before sending request."""

    pass


class ModelValidationError(OAuthCodexError):
    """Model capability or model name validation failed."""

    pass


class ContinuityError(OAuthCodexError):
    """Response continuity state is invalid for continuation requests."""

    pass


class TokenStoreError(OAuthCodexError):
    """Base class for token persistence layer failures.

    Attributes:
        cause: Original exception raised by the storage backend, when present.
    """

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class TokenStoreReadError(TokenStoreError):
    """Token load/read operation failed."""

    pass


class TokenStoreWriteError(TokenStoreError):
    """Token save/write operation failed."""

    pass


class TokenStoreDeleteError(TokenStoreError):
    """Token delete operation failed."""

    pass


class SDKRequestError(OAuthCodexError):
    """Normalized SDK error for provider and compatibility request failures.

    Attributes:
        status_code: HTTP-like status code when available.
        provider_code: Provider-specific machine-readable error code.
        user_message: Human-readable message intended for callers.
        retryable: Whether the request may succeed on retry.
        request_id: Provider request identifier when available.
        raw_error: Original provider payload or underlying exception data.
    """

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


class NotSupportedError(SDKRequestError):
    """Requested operation is not supported by the active backend/profile."""

    def __init__(self, message: str, *, code: str = "not_supported") -> None:
        super().__init__(
            status_code=400,
            provider_code=code,
            user_message=message,
            retryable=False,
        )
        self.code = code


class ToolCallRequiredError(OAuthCodexError):
    """Model response requires tool execution before completion.

    Attributes:
        message: Human-readable explanation for the tool requirement.
        tool_calls: Tool call payloads that must be executed.
    """

    def __init__(
        self, message: str, tool_calls: list[dict[str, Any]] | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.tool_calls = tool_calls or []
