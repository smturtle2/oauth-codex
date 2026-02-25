from __future__ import annotations

import asyncio
import importlib
import random
import time
from typing import Any, Mapping

import httpx


class _BaseClientCommon:
    def __init__(
        self, *, base_url: str = "", timeout: float = 60.0, max_retries: int = 2
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, int(max_retries))
        self._exceptions_module: Any | None = None

    def _resolve_url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{normalized_path}" if self.base_url else normalized_path

    def _should_retry_status(self, status_code: int) -> bool:
        return status_code in {408, 409, 429} or status_code >= 500

    def _retry_delay_seconds(self, attempt: int) -> float:
        base = min(0.5 * (2**attempt), 8.0)
        jitter = random.uniform(0.0, 0.25)
        return base + jitter

    def _exceptions(self) -> Any:
        if self._exceptions_module is not None:
            return self._exceptions_module
        self._exceptions_module = importlib.import_module("oauth_codex._exceptions")
        return self._exceptions_module

    def _status_error_class_name(self, status_code: int) -> str:
        if status_code == 400:
            return "BadRequestError"
        if status_code == 401:
            return "AuthenticationError"
        if status_code == 403:
            return "PermissionDeniedError"
        if status_code == 404:
            return "NotFoundError"
        if status_code == 409:
            return "ConflictError"
        if status_code == 422:
            return "UnprocessableEntityError"
        if status_code == 429:
            return "RateLimitError"
        if status_code >= 500:
            return "InternalServerError"
        return "APIStatusError"

    def _extract_error_payload(self, response: httpx.Response) -> Any:
        try:
            payload = response.json()
        except ValueError:
            return response.text
        return payload

    def _extract_error_message(self, response: httpx.Response, payload: Any) -> str:
        default_message = f"Request failed with status code {response.status_code}"
        if isinstance(payload, dict):
            raw_error = payload.get("error")
            if isinstance(raw_error, dict):
                message = raw_error.get("message")
                if isinstance(message, str) and message:
                    return message
            message = payload.get("message")
            if isinstance(message, str) and message:
                return message
        if isinstance(payload, str) and payload:
            return payload
        return default_message

    def _build_status_error(self, response: httpx.Response) -> Exception:
        exceptions = self._exceptions()
        payload = self._extract_error_payload(response)
        message = self._extract_error_message(response, payload)

        class_name = self._status_error_class_name(response.status_code)
        error_cls = getattr(exceptions, class_name, None)
        if error_cls is None:
            error_cls = getattr(exceptions, "APIStatusError", Exception)

        try:
            return error_cls(message, response=response, body=payload)
        except TypeError:
            try:
                return error_cls(message)
            except TypeError:
                return Exception(message)

    def _build_connection_error(self, error: httpx.RequestError) -> Exception:
        exceptions = self._exceptions()
        timeout_cls = getattr(exceptions, "APITimeoutError", None)
        connection_cls = getattr(exceptions, "APIConnectionError", Exception)

        if isinstance(error, httpx.TimeoutException) and timeout_cls is not None:
            try:
                return timeout_cls(error.request)
            except TypeError:
                try:
                    return timeout_cls(request=error.request)
                except TypeError:
                    pass

        try:
            return connection_cls(message=str(error), request=error.request)
        except TypeError:
            try:
                return connection_cls(str(error))
            except TypeError:
                return Exception(str(error))


class SyncAPIClient(_BaseClientCommon):
    def __init__(
        self,
        *,
        base_url: str = "",
        timeout: float = 60.0,
        max_retries: int = 2,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(base_url=base_url, timeout=timeout, max_retries=max_retries)
        self._client = http_client or httpx.Client(timeout=timeout)
        self._owns_http_client = http_client is None

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        json_data: Any = None,
        data: Any = None,
        files: Any = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        return self._request(
            method,
            path,
            params=params,
            headers=headers,
            json_data=json_data,
            data=data,
            files=files,
            timeout=timeout,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        json_data: Any = None,
        data: Any = None,
        files: Any = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        url = self._resolve_url(path)
        request_timeout = self.timeout if timeout is None else timeout

        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    headers=headers,
                    json=json_data,
                    data=data,
                    files=files,
                    timeout=request_timeout,
                )
            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    time.sleep(self._retry_delay_seconds(attempt))
                    continue
                raise self._build_connection_error(exc) from exc

            if (
                self._should_retry_status(response.status_code)
                and attempt < self.max_retries
            ):
                time.sleep(self._retry_delay_seconds(attempt))
                continue

            if response.status_code >= 400:
                raise self._build_status_error(response)

            return response

        raise RuntimeError("Request retries exhausted")

    def close(self) -> None:
        if self._owns_http_client:
            self._client.close()

    def __enter__(self) -> SyncAPIClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()


class AsyncAPIClient(_BaseClientCommon):
    def __init__(
        self,
        *,
        base_url: str = "",
        timeout: float = 60.0,
        max_retries: int = 2,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(base_url=base_url, timeout=timeout, max_retries=max_retries)
        self._client = http_client or httpx.AsyncClient(timeout=timeout)
        self._owns_http_client = http_client is None

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        json_data: Any = None,
        data: Any = None,
        files: Any = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        return await self._request(
            method,
            path,
            params=params,
            headers=headers,
            json_data=json_data,
            data=data,
            files=files,
            timeout=timeout,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        json_data: Any = None,
        data: Any = None,
        files: Any = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        url = self._resolve_url(path)
        request_timeout = self.timeout if timeout is None else timeout

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    headers=headers,
                    json=json_data,
                    data=data,
                    files=files,
                    timeout=request_timeout,
                )
            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(self._retry_delay_seconds(attempt))
                    continue
                raise self._build_connection_error(exc) from exc

            if (
                self._should_retry_status(response.status_code)
                and attempt < self.max_retries
            ):
                await asyncio.sleep(self._retry_delay_seconds(attempt))
                continue

            if response.status_code >= 400:
                raise self._build_status_error(response)

            return response

        raise RuntimeError("Request retries exhausted")

    async def close(self) -> None:
        if self._owns_http_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncAPIClient:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.close()
