from __future__ import annotations

from typing import Any

import httpx


class OAuthCodexError(Exception):
    pass


class OpenAIError(OAuthCodexError):
    pass


class APIError(OpenAIError):
    def __init__(self, message: str, request: httpx.Request | None = None, *, body: object | None = None) -> None:
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
    def __init__(self, message: str, *, response: httpx.Response, body: object | None = None) -> None:
        super().__init__(message, response.request, body=body)
        self.response = response
        self.status_code = response.status_code
        self.request_id = response.headers.get("x-request-id")


class APIConnectionError(APIError):
    def __init__(self, *, message: str = "Connection error.", request: httpx.Request | None = None) -> None:
        super().__init__(message, request, body=None)


class APITimeoutError(APIConnectionError):
    def __init__(self, request: httpx.Request | None = None) -> None:
        super().__init__(message="Request timed out.", request=request)


class BadRequestError(APIStatusError):
    pass


class AuthenticationError(APIStatusError):
    pass


class PermissionDeniedError(APIStatusError):
    pass


class NotFoundError(APIStatusError):
    pass


class ConflictError(APIStatusError):
    pass


class UnprocessableEntityError(APIStatusError):
    pass


class RateLimitError(APIStatusError):
    pass


class InternalServerError(APIStatusError):
    pass


class APIResponseValidationError(APIError):
    def __init__(self, response: httpx.Response, body: object | None, *, message: str | None = None) -> None:
        super().__init__(message or "Data returned by API invalid for expected schema.", response.request, body=body)
        self.response = response
        self.status_code = response.status_code


class OAuthCallbackParseError(OAuthCodexError):
    pass


class OAuthStateMismatchError(OAuthCodexError):
    pass


class TokenExchangeError(OAuthCodexError):
    pass


class TokenRefreshError(OAuthCodexError):
    pass


class AuthRequiredError(OAuthCodexError):
    pass


class ParameterValidationError(OAuthCodexError):
    pass


class ModelValidationError(OAuthCodexError):
    pass


class ContinuityError(OAuthCodexError):
    pass


class TokenStoreError(OAuthCodexError):
    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class TokenStoreReadError(TokenStoreError):
    pass


class TokenStoreWriteError(TokenStoreError):
    pass


class TokenStoreDeleteError(TokenStoreError):
    pass


class SDKRequestError(OAuthCodexError):
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
    def __init__(self, message: str, *, code: str = "not_supported") -> None:
        super().__init__(
            status_code=400,
            provider_code=code,
            user_message=message,
            retryable=False,
        )
        self.code = code


class ToolCallRequiredError(OAuthCodexError):
    def __init__(self, message: str, tool_calls: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.tool_calls = tool_calls or []


# Backward-compatible aliases for callers that still import legacy names.
LLMRequestError = SDKRequestError
CodexOAuthLLMError = OAuthCodexError
