from __future__ import annotations
"""Legacy internal engine.

This module keeps the pre-1.0 request/auth/stream implementation and is used by
the new OpenAI-style surface in `oauth_codex._client` as an internal runtime
backend. External users should import from package root (`oauth_codex`) only.
"""

import asyncio
import json
import random
import time
import uuid
import warnings
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Iterator, Literal

import httpx

from .legacy_auth import (
    build_authorize_url,
    discover_endpoints,
    discover_endpoints_async,
    exchange_code_for_tokens,
    generate_pkce_pair,
    generate_state,
    load_oauth_config,
    parse_callback_url,
    refresh_tokens,
    refresh_tokens_async,
)
from .compat_store import LocalCompatStore
from .errors import (
    AuthRequiredError,
    ContinuityError,
    LLMRequestError,
    ModelValidationError,
    NotSupportedError,
    ParameterValidationError,
    SDKRequestError,
    TokenStoreDeleteError,
    TokenStoreReadError,
    TokenStoreWriteError,
    ToolCallRequiredError,
    TokenRefreshError,
)
from .store import FallbackTokenStore
from .tooling import normalize_tool_inputs, to_responses_tools, tool_results_to_response_items
from .legacy_types import (
    GenerateResult,
    InputTokensCountResult,
    Message,
    ModelCapabilities,
    OAuthConfig,
    OAuthTokens,
    ResponseCompat,
    StoreBehavior,
    StreamEvent,
    TokenStore,
    TokenUsage,
    TruncationMode,
    ValidationMode,
    ToolCall,
    ToolInput,
    ToolResult,
)


class OAuthCodexClient:
    _PROTECTED_REQUEST_HEADERS = frozenset({"authorization", "chatgpt-account-id", "content-type"})

    def __init__(
        self,
        *,
        oauth_config: OAuthConfig | None = None,
        token_store: TokenStore | None = None,
        chatgpt_base_url: str = "https://chatgpt.com/backend-api/codex",
        timeout: float = 60.0,
        validation_mode: ValidationMode = "warn",
        store_behavior: StoreBehavior = "auto_disable",
        max_retries: int = 2,
        backoff_base_seconds: float = 0.25,
        compat_storage_dir: str | Path | None = None,
        on_request_start: Callable[[dict[str, Any]], None] | None = None,
        on_request_end: Callable[[dict[str, Any]], None] | None = None,
        on_auth_refresh: Callable[[dict[str, Any]], None] | None = None,
        on_error: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.oauth_config = load_oauth_config(oauth_config)
        self.token_store = token_store or FallbackTokenStore()
        self.chatgpt_base_url = chatgpt_base_url.rstrip("/")
        self.timeout = timeout
        self.validation_mode = validation_mode
        self.store_behavior = store_behavior
        self.max_retries = max(0, max_retries)
        self.backoff_base_seconds = max(0.05, backoff_base_seconds)
        self._compat_store = LocalCompatStore(base_dir=compat_storage_dir)
        self.on_request_start = on_request_start
        self.on_request_end = on_request_end
        self.on_auth_refresh = on_auth_refresh
        self.on_error = on_error
        self._refresh_leeway_seconds = 60
        self._tool_call_name_by_id: dict[str, str] = {}
        self._tool_call_args_buffer: dict[str, str] = {}
        self._tool_call_started: set[str] = set()
        self.responses = _ResponsesResource(self)
        self.files = _FilesResource(self)
        self.vector_stores = _VectorStoresResource(self)
        self.models = _ModelsResource(self)

    @property
    def _engine(self) -> OAuthCodexClient:
        # Backward-compatible alias for callers that used wrapper-style access.
        return self

    def is_authenticated(self) -> bool:
        tokens = self._load_tokens_sync()
        if not tokens:
            return False
        return not tokens.is_expired(leeway_seconds=0)

    def is_expired(self, *, leeway_seconds: int = 60) -> bool:
        tokens = self._load_tokens_sync()
        if not tokens:
            return True
        return tokens.is_expired(leeway_seconds=leeway_seconds)

    def refresh_if_needed(self, *, force: bool = False) -> bool:
        tokens = self._load_tokens_sync()
        if not tokens:
            return False
        if force or tokens.is_expired(leeway_seconds=self._refresh_leeway_seconds):
            self._refresh_and_persist_sync(tokens)
            return True
        return False

    async def arefresh_if_needed(self, *, force: bool = False) -> bool:
        tokens = await self._load_tokens_async()
        if not tokens:
            return False
        if force or tokens.is_expired(leeway_seconds=self._refresh_leeway_seconds):
            await self._refresh_and_persist_async(tokens)
            return True
        return False

    def login(self) -> None:
        with httpx.Client(timeout=self.timeout) as client:
            self.oauth_config = discover_endpoints(client, self.oauth_config)

            code_verifier, code_challenge = generate_pkce_pair()
            state = generate_state()
            authorize_url = build_authorize_url(self.oauth_config, state, code_challenge)

            print("Open this URL in your browser and complete sign-in:")
            print(authorize_url)
            callback_url = input("Paste the full localhost callback URL: ").strip()

            code = parse_callback_url(callback_url, state)
            tokens = exchange_code_for_tokens(
                client=client,
                config=self.oauth_config,
                code=code,
                code_verifier=code_verifier,
            )
            self._save_tokens_sync(tokens)

    def generate(
        self,
        *,
        model: str,
        prompt: str | None = None,
        messages: list[Message] | None = None,
        api_mode: Literal["responses"] = "responses",
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        validation_mode: ValidationMode | None = None,
        return_details: bool = False,
        validate_model: bool = False,
    ) -> str | GenerateResult:
        self._require_responses_mode(api_mode)

        normalized_messages = self._normalize_messages(prompt=prompt, messages=messages)
        normalized_tools = normalize_tool_inputs(tools)
        normalized_tool_results = self._normalize_tool_results(tool_results)

        if validate_model:
            tokens = self._ensure_authenticated_sync()
            self._validate_model_sync(model, tokens)

        result = self._generate_responses_sync(
            model=model,
            messages=normalized_messages,
            tools=normalized_tools,
            tool_results=normalized_tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            validation_mode=validation_mode,
        )

        if return_details:
            return result

        if result.tool_calls:
            raise ToolCallRequiredError(
                "Model requested tool calls. Execute them and call generate again with tool_results.",
                result.tool_calls,
            )
        return result.text

    async def agenerate(
        self,
        *,
        model: str,
        prompt: str | None = None,
        messages: list[Message] | None = None,
        api_mode: Literal["responses"] = "responses",
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        validation_mode: ValidationMode | None = None,
        return_details: bool = False,
        validate_model: bool = False,
    ) -> str | GenerateResult:
        self._require_responses_mode(api_mode)

        normalized_messages = self._normalize_messages(prompt=prompt, messages=messages)
        normalized_tools = normalize_tool_inputs(tools)
        normalized_tool_results = self._normalize_tool_results(tool_results)

        if validate_model:
            tokens = await self._ensure_authenticated_async()
            await self._validate_model_async(model, tokens)

        result = await self._generate_responses_async(
            model=model,
            messages=normalized_messages,
            tools=normalized_tools,
            tool_results=normalized_tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            validation_mode=validation_mode,
        )

        if return_details:
            return result

        if result.tool_calls:
            raise ToolCallRequiredError(
                "Model requested tool calls. Execute them and call generate again with tool_results.",
                result.tool_calls,
            )
        return result.text

    def generate_stream(
        self,
        *,
        model: str,
        prompt: str | None = None,
        messages: list[Message] | None = None,
        api_mode: Literal["responses"] = "responses",
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        validation_mode: ValidationMode | None = None,
        raw_events: bool = False,
        validate_model: bool = False,
    ) -> Iterator[str] | Iterator[StreamEvent]:
        self._require_responses_mode(api_mode)

        normalized_messages = self._normalize_messages(prompt=prompt, messages=messages)
        normalized_tools = normalize_tool_inputs(tools)
        normalized_tool_results = self._normalize_tool_results(tool_results)

        if normalized_tools and not raw_events:
            raise ValueError("raw_events=True is required when tools are provided for streaming")

        if validate_model:
            tokens = self._ensure_authenticated_sync()
            self._validate_model_sync(model, tokens)

        events = self._stream_responses_sync(
            model=model,
            messages=normalized_messages,
            tools=normalized_tools,
            tool_results=normalized_tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            validation_mode=validation_mode,
        )
        if raw_events:
            return events
        return self._text_only_stream(events)

    async def agenerate_stream(
        self,
        *,
        model: str,
        prompt: str | None = None,
        messages: list[Message] | None = None,
        api_mode: Literal["responses"] = "responses",
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        validation_mode: ValidationMode | None = None,
        raw_events: bool = False,
        validate_model: bool = False,
    ) -> AsyncIterator[str] | AsyncIterator[StreamEvent]:
        self._require_responses_mode(api_mode)

        normalized_messages = self._normalize_messages(prompt=prompt, messages=messages)
        normalized_tools = normalize_tool_inputs(tools)
        normalized_tool_results = self._normalize_tool_results(tool_results)

        if normalized_tools and not raw_events:
            raise ValueError("raw_events=True is required when tools are provided for streaming")

        if validate_model:
            tokens = await self._ensure_authenticated_async()
            await self._validate_model_async(model, tokens)

        events = self._stream_responses_async(
            model=model,
            messages=normalized_messages,
            tools=normalized_tools,
            tool_results=normalized_tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            validation_mode=validation_mode,
        )
        if raw_events:
            return events
        return self._text_only_stream_async(events)

    def responses_create(
        self,
        *,
        model: str,
        input: str | Message | list[Message] | None = None,
        messages: list[Message] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        stream: bool = False,
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> ResponseCompat | Iterator[StreamEvent]:
        self._validate_extra_params(extra, validation_mode=validation_mode)
        normalized_messages = self._normalize_responses_input(input=input, messages=messages)
        normalized_tools = normalize_tool_inputs(tools)
        normalized_tool_results = self._normalize_tool_results(tool_results)

        if stream:
            return self._stream_responses_sync(
                model=model,
                messages=normalized_messages,
                tools=normalized_tools,
                tool_results=normalized_tool_results,
                response_format=response_format,
                tool_choice=tool_choice,
                strict_output=strict_output,
                store=store,
                reasoning=reasoning,
                previous_response_id=previous_response_id,
                instructions=instructions,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_output_tokens,
                metadata=metadata,
                include=include,
                max_tool_calls=max_tool_calls,
                parallel_tool_calls=parallel_tool_calls,
                truncation=truncation,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                service_tier=service_tier,
                validation_mode=validation_mode,
            )

        result = self._generate_responses_sync(
            model=model,
            messages=normalized_messages,
            tools=normalized_tools,
            tool_results=normalized_tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            validation_mode=validation_mode,
        )
        self._validate_response_continuity(
            raw_response=result.raw_response,
            previous_response_id=previous_response_id,
        )
        response = self._generate_result_to_response(
            result,
            previous_response_id=previous_response_id,
        )
        return response

    async def aresponses_create(
        self,
        *,
        model: str,
        input: str | Message | list[Message] | None = None,
        messages: list[Message] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        stream: bool = False,
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> ResponseCompat | AsyncIterator[StreamEvent]:
        self._validate_extra_params(extra, validation_mode=validation_mode)
        normalized_messages = self._normalize_responses_input(input=input, messages=messages)
        normalized_tools = normalize_tool_inputs(tools)
        normalized_tool_results = self._normalize_tool_results(tool_results)

        if stream:
            return self._stream_responses_async(
                model=model,
                messages=normalized_messages,
                tools=normalized_tools,
                tool_results=normalized_tool_results,
                response_format=response_format,
                tool_choice=tool_choice,
                strict_output=strict_output,
                store=store,
                reasoning=reasoning,
                previous_response_id=previous_response_id,
                instructions=instructions,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_output_tokens,
                metadata=metadata,
                include=include,
                max_tool_calls=max_tool_calls,
                parallel_tool_calls=parallel_tool_calls,
                truncation=truncation,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                service_tier=service_tier,
                validation_mode=validation_mode,
            )

        result = await self._generate_responses_async(
            model=model,
            messages=normalized_messages,
            tools=normalized_tools,
            tool_results=normalized_tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            validation_mode=validation_mode,
        )
        self._validate_response_continuity(
            raw_response=result.raw_response,
            previous_response_id=previous_response_id,
        )
        response = self._generate_result_to_response(
            result,
            previous_response_id=previous_response_id,
        )
        return response

    def responses_input_tokens_count(
        self,
        *,
        model: str,
        input: str | Message | list[Message],
        tools: list[ToolInput] | None = None,
    ) -> InputTokensCountResult:
        messages = self._normalize_responses_input(input=input, messages=None)
        payload: dict[str, Any] = {"model": model, "input": messages}
        if tools:
            payload["tools"] = to_responses_tools(normalize_tool_inputs(tools))
        data = self._request_json_sync(path="/responses/input_tokens", payload=payload)
        return self._parse_input_tokens_count(data)

    async def aresponses_input_tokens_count(
        self,
        *,
        model: str,
        input: str | Message | list[Message],
        tools: list[ToolInput] | None = None,
    ) -> InputTokensCountResult:
        messages = self._normalize_responses_input(input=input, messages=None)
        payload: dict[str, Any] = {"model": model, "input": messages}
        if tools:
            payload["tools"] = to_responses_tools(normalize_tool_inputs(tools))
        data = await self._request_json_async(path="/responses/input_tokens", payload=payload)
        return self._parse_input_tokens_count(data)

    def files_create(
        self,
        *,
        file: Any,
        purpose: str,
        **metadata: Any,
    ) -> dict[str, Any]:
        if self._is_codex_profile():
            try:
                return self._compat_store.create_file(file=file, purpose=purpose, metadata=metadata)
            except Exception as exc:
                self._raise_local_compat_error(exc)
        files = {"file": file}
        data = {"purpose": purpose, **metadata}
        return self._request_multipart_sync(path="/files", data=data, files=files)

    async def afiles_create(
        self,
        *,
        file: Any,
        purpose: str,
        **metadata: Any,
    ) -> dict[str, Any]:
        if self._is_codex_profile():
            try:
                return await asyncio.to_thread(
                    self._compat_store.create_file,
                    file=file,
                    purpose=purpose,
                    metadata=metadata,
                )
            except Exception as exc:
                self._raise_local_compat_error(exc)
        files = {"file": file}
        data = {"purpose": purpose, **metadata}
        return await self._request_multipart_async(path="/files", data=data, files=files)

    def vector_store_request(self, *, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        normalized_payload = payload or {}
        if self._is_codex_profile():
            try:
                return self._compat_vector_store_request(
                    method=method,
                    path=path,
                    payload=normalized_payload,
                )
            except Exception as exc:
                self._raise_local_compat_error(exc)
        return self._request_json_sync(path=path, payload=payload or {}, method=method)

    async def avector_store_request(
        self, *, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        normalized_payload = payload or {}
        if self._is_codex_profile():
            try:
                return await asyncio.to_thread(
                    self._compat_vector_store_request,
                    method=method,
                    path=path,
                    payload=normalized_payload,
                )
            except Exception as exc:
                self._raise_local_compat_error(exc)
        return await self._request_json_async(path=path, payload=normalized_payload, method=method)

    def _require_responses_mode(self, api_mode: str) -> None:
        if api_mode != "responses":
            raise ValueError(
                "Only api_mode='responses' is supported for chatgpt.com/backend-api/codex"
            )

    def _validate_extra_params(
        self,
        extra: dict[str, Any],
        *,
        validation_mode: ValidationMode | None,
    ) -> None:
        for key in sorted(extra.keys()):
            self._warn_or_error(
                f"unsupported parameter: {key}",
                code="unsupported_parameter",
                validation_mode=validation_mode,
            )

    def _normalize_responses_input(
        self,
        *,
        input: str | Message | list[Message] | None,
        messages: list[Message] | None,
    ) -> list[Message]:
        if input is not None and messages is not None:
            raise ValueError("Provide only one of `input` or `messages`")
        if input is None and messages is None:
            raise ValueError("`input` is required")
        if isinstance(input, str):
            return [{"role": "user", "content": input}]
        if isinstance(input, dict):
            return [dict(input)]
        if isinstance(input, list):
            if not input:
                raise ValueError("`input` must be a non-empty list when provided as list")
            return [dict(item) for item in input]
        if messages is not None:
            if not isinstance(messages, list) or not messages:
                raise ValueError("`messages` must be a non-empty list")
            return [dict(item) for item in messages]
        raise TypeError("Unsupported `input` type")

    def _normalize_continuation_items(self, items: Any) -> list[Message]:
        if not isinstance(items, list):
            raise ValueError("continuation_input must be a list")
        normalized: list[Message] = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("continuation_input must contain dictionaries")
            normalized.append(dict(item))
        return normalized

    def _build_effective_responses_input(
        self,
        *,
        messages: list[Message],
        tool_results: list[ToolResult],
        previous_response_id: str | None,
    ) -> tuple[list[Message], str | None]:
        current_turn: list[Message] = [*messages, *tool_results_to_response_items(tool_results)]
        if not self._is_codex_profile() or not previous_response_id:
            return current_turn, previous_response_id

        try:
            record = self._compat_store.get_response_continuity(previous_response_id)
            prior_items = self._normalize_continuation_items(record.get("continuation_input"))
        except Exception as exc:
            self._raise_local_compat_error(exc)
            return [], None

        return [*prior_items, *current_turn], None

    def _extract_output_items_for_continuation(
        self,
        *,
        raw_response: dict[str, Any] | None,
        text_parts: list[str],
        tool_calls: list[ToolCall],
    ) -> list[Message]:
        if isinstance(raw_response, dict):
            candidates: list[Any] = [raw_response.get("output")]
            response_obj = raw_response.get("response")
            if isinstance(response_obj, dict):
                candidates.append(response_obj.get("output"))
            for candidate in candidates:
                if not isinstance(candidate, list):
                    continue
                normalized = [dict(item) for item in candidate if isinstance(item, dict)]
                if normalized:
                    return normalized

        output_items: list[Message] = []
        text = "".join(text_parts)
        if text:
            output_items.append(
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": text}],
                }
            )
        for call in tool_calls:
            output_items.append(
                {
                    "type": "function_call",
                    "call_id": call.id,
                    "name": call.name,
                    "arguments": call.arguments_json,
                }
            )
        return output_items

    def _persist_response_continuity_sync(
        self,
        *,
        model: str,
        request_input: list[Message],
        response_id: str | None,
        previous_response_id: str | None,
        raw_response: dict[str, Any] | None,
        text_parts: list[str],
        tool_calls: list[ToolCall],
    ) -> None:
        if not self._is_codex_profile():
            return
        if not response_id:
            return

        try:
            normalized_request_input = self._normalize_continuation_items(request_input)
            output_items = self._extract_output_items_for_continuation(
                raw_response=raw_response,
                text_parts=text_parts,
                tool_calls=tool_calls,
            )
            continuation_input = [*normalized_request_input, *output_items]
            self._compat_store.upsert_response_continuity(
                response_id=response_id,
                model=model,
                continuation_input=continuation_input,
                previous_response_id=previous_response_id,
            )
        except Exception as exc:
            self._raise_local_compat_error(exc)

    async def _persist_response_continuity_async(
        self,
        *,
        model: str,
        request_input: list[Message],
        response_id: str | None,
        previous_response_id: str | None,
        raw_response: dict[str, Any] | None,
        text_parts: list[str],
        tool_calls: list[ToolCall],
    ) -> None:
        await asyncio.to_thread(
            self._persist_response_continuity_sync,
            model=model,
            request_input=request_input,
            response_id=response_id,
            previous_response_id=previous_response_id,
            raw_response=raw_response,
            text_parts=text_parts,
            tool_calls=tool_calls,
        )

    def _generate_result_to_response(
        self,
        result: GenerateResult,
        *,
        previous_response_id: str | None,
    ) -> ResponseCompat:
        response_id = result.response_id or f"resp_{uuid.uuid4().hex}"
        if previous_response_id and response_id == previous_response_id:
            raise ContinuityError("response.id must differ from previous_response_id")

        output_items: list[dict[str, Any]] = []
        if result.text:
            output_items.append(
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": result.text}],
                }
            )
        for call in result.tool_calls:
            output_items.append(
                {
                    "type": "function_call",
                    "call_id": call.id,
                    "name": call.name,
                    "arguments": call.arguments_json,
                }
            )
        raw = result.raw_response if isinstance(result.raw_response, dict) else {}
        error_payload = raw.get("error") if isinstance(raw.get("error"), dict) else None
        reasoning_summary, reasoning_items, encrypted_reasoning = self._extract_reasoning_fields(raw)
        return ResponseCompat(
            id=response_id,
            output=output_items,
            output_text=result.text,
            usage=result.usage,
            error=error_payload,
            reasoning_summary=reasoning_summary,
            reasoning_items=reasoning_items,
            encrypted_reasoning_content=encrypted_reasoning,
            finish_reason=result.finish_reason,
            previous_response_id=previous_response_id,
            raw_response=result.raw_response,
        )

    def _validate_response_continuity(
        self,
        *,
        raw_response: dict[str, Any] | None,
        previous_response_id: str | None,
    ) -> None:
        if not previous_response_id:
            return
        if not isinstance(raw_response, dict):
            return
        raw_previous = raw_response.get("previous_response_id")
        if raw_previous is None:
            return
        if not isinstance(raw_previous, str):
            raise ContinuityError("response previous_response_id is not a string")
        if raw_previous != previous_response_id:
            raise ContinuityError(
                "response previous_response_id does not match requested previous_response_id"
            )

    def _parse_input_tokens_count(self, payload: dict[str, Any]) -> InputTokensCountResult:
        input_tokens = payload.get("input_tokens")
        if not isinstance(input_tokens, int):
            raise SDKRequestError(
                status_code=None,
                provider_code="invalid_input_tokens_response",
                user_message="input_tokens.count response missing input_tokens",
                retryable=False,
                raw_error=payload,
            )
        cached_tokens = payload.get("cached_tokens")
        total_tokens = payload.get("total_tokens")
        return InputTokensCountResult(
            input_tokens=input_tokens,
            cached_tokens=cached_tokens if isinstance(cached_tokens, int) else None,
            total_tokens=total_tokens if isinstance(total_tokens, int) else None,
        )

    def _extract_reasoning_fields(
        self,
        payload: dict[str, Any],
    ) -> tuple[str | None, list[dict[str, Any]], str | None]:
        reasoning_items: list[dict[str, Any]] = []
        reasoning_summary: str | None = None
        encrypted: str | None = None

        output = payload.get("output")
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type")
                if item_type in {"reasoning", "reasoning_summary"}:
                    reasoning_items.append(item)
                    summary = item.get("summary")
                    if isinstance(summary, str) and summary and reasoning_summary is None:
                        reasoning_summary = summary
                if item_type == "reasoning_encrypted":
                    content = item.get("content")
                    if isinstance(content, str) and content:
                        encrypted = content

        if reasoning_summary is None:
            reasoning_obj = payload.get("reasoning")
            if isinstance(reasoning_obj, dict):
                summary = reasoning_obj.get("summary")
                if isinstance(summary, str) and summary:
                    reasoning_summary = summary
                enc = reasoning_obj.get("encrypted_content")
                if isinstance(enc, str) and enc:
                    encrypted = enc
                if reasoning_obj:
                    reasoning_items.append(dict(reasoning_obj))

        return reasoning_summary, reasoning_items, encrypted

    def _request_json_sync(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        method: str = "POST",
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        validation_mode: ValidationMode | None = None,
    ) -> dict[str, Any]:
        tokens = self._ensure_authenticated_sync()
        url = self._resolve_request_url(path)
        attempted_refresh = False
        mode = self._effective_validation_mode(validation_mode)
        normalized_extra_headers = self._normalize_extra_headers(
            extra_headers, validation_mode=mode
        )
        normalized_extra_query = self._validate_extra_query(extra_query, validation_mode=mode)

        for attempt in range(self.max_retries + 1):
            request_id = f"req_{uuid.uuid4().hex}"
            self._emit_hook(
                self.on_request_start,
                {
                    "request_id": request_id,
                    "path": path,
                    "model": payload.get("model"),
                    "auth_state": "authenticated",
                    "refreshed": attempted_refresh,
                    "options": payload,
                },
            )
            headers = self._auth_headers(tokens)
            if normalized_extra_headers:
                headers.update(normalized_extra_headers)
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method.upper(),
                    url,
                    headers=headers,
                    json=payload,
                    params=normalized_extra_query,
                )
            if response.status_code == 401 and not attempted_refresh:
                tokens = self._refresh_and_persist_sync(tokens)
                attempted_refresh = True
                continue
            if self._is_retryable_status(response.status_code) and attempt < self.max_retries:
                time.sleep(self._compute_retry_delay(attempt))
                continue
            if response.status_code >= 400:
                exc = self._build_sdk_request_error(response)
                self._emit_hook(
                    self.on_error,
                    {
                        "request_id": request_id,
                        "status_code": exc.status_code,
                        "provider_code": exc.provider_code,
                        "message": exc.user_message,
                        "retryable": exc.retryable,
                    },
                )
                raise exc

            parsed = response.json()
            if not isinstance(parsed, dict):
                raise SDKRequestError(
                    status_code=response.status_code,
                    provider_code="invalid_json_shape",
                    user_message="Expected JSON object response",
                    retryable=False,
                    request_id=request_id,
                    raw_error=parsed,
                )
            self._emit_hook(
                self.on_request_end,
                {
                    "request_id": request_id,
                    "path": path,
                    "status_code": response.status_code,
                    "refreshed": attempted_refresh,
                },
            )
            return parsed
        raise SDKRequestError(
            status_code=None,
            provider_code="retry_exhausted",
            user_message="Request failed after retries",
            retryable=False,
        )

    async def _request_json_async(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        method: str = "POST",
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        validation_mode: ValidationMode | None = None,
    ) -> dict[str, Any]:
        tokens = await self._ensure_authenticated_async()
        url = self._resolve_request_url(path)
        attempted_refresh = False
        mode = self._effective_validation_mode(validation_mode)
        normalized_extra_headers = self._normalize_extra_headers(
            extra_headers, validation_mode=mode
        )
        normalized_extra_query = self._validate_extra_query(extra_query, validation_mode=mode)

        for attempt in range(self.max_retries + 1):
            request_id = f"req_{uuid.uuid4().hex}"
            self._emit_hook(
                self.on_request_start,
                {
                    "request_id": request_id,
                    "path": path,
                    "model": payload.get("model"),
                    "auth_state": "authenticated",
                    "refreshed": attempted_refresh,
                    "options": payload,
                },
            )
            headers = self._auth_headers(tokens)
            if normalized_extra_headers:
                headers.update(normalized_extra_headers)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method.upper(),
                    url,
                    headers=headers,
                    json=payload,
                    params=normalized_extra_query,
                )
            if response.status_code == 401 and not attempted_refresh:
                tokens = await self._refresh_and_persist_async(tokens)
                attempted_refresh = True
                continue
            if self._is_retryable_status(response.status_code) and attempt < self.max_retries:
                await asyncio.sleep(self._compute_retry_delay(attempt))
                continue
            if response.status_code >= 400:
                exc = self._build_sdk_request_error(response)
                self._emit_hook(
                    self.on_error,
                    {
                        "request_id": request_id,
                        "status_code": exc.status_code,
                        "provider_code": exc.provider_code,
                        "message": exc.user_message,
                        "retryable": exc.retryable,
                    },
                )
                raise exc
            parsed = response.json()
            if not isinstance(parsed, dict):
                raise SDKRequestError(
                    status_code=response.status_code,
                    provider_code="invalid_json_shape",
                    user_message="Expected JSON object response",
                    retryable=False,
                    request_id=request_id,
                    raw_error=parsed,
                )
            self._emit_hook(
                self.on_request_end,
                {
                    "request_id": request_id,
                    "path": path,
                    "status_code": response.status_code,
                    "refreshed": attempted_refresh,
                },
            )
            return parsed
        raise SDKRequestError(
            status_code=None,
            provider_code="retry_exhausted",
            user_message="Request failed after retries",
            retryable=False,
        )

    def _request_multipart_sync(
        self,
        *,
        path: str,
        data: dict[str, Any],
        files: dict[str, Any],
    ) -> dict[str, Any]:
        tokens = self._ensure_authenticated_sync()
        url = self._resolve_request_url(path)
        headers = self._auth_headers(tokens)
        headers.pop("Content-Type", None)
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, headers=headers, data=data, files=files)
        if response.status_code >= 400:
            raise self._build_sdk_request_error(response)
        parsed = response.json()
        if not isinstance(parsed, dict):
            raise SDKRequestError(
                status_code=response.status_code,
                provider_code="invalid_json_shape",
                user_message="Expected JSON object response",
                retryable=False,
                raw_error=parsed,
            )
        return parsed

    async def _request_multipart_async(
        self,
        *,
        path: str,
        data: dict[str, Any],
        files: dict[str, Any],
    ) -> dict[str, Any]:
        tokens = await self._ensure_authenticated_async()
        url = self._resolve_request_url(path)
        headers = self._auth_headers(tokens)
        headers.pop("Content-Type", None)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, data=data, files=files)
        if response.status_code >= 400:
            raise self._build_sdk_request_error(response)
        parsed = response.json()
        if not isinstance(parsed, dict):
            raise SDKRequestError(
                status_code=response.status_code,
                provider_code="invalid_json_shape",
                user_message="Expected JSON object response",
                retryable=False,
                raw_error=parsed,
            )
        return parsed

    def _normalize_messages(
        self,
        *,
        prompt: str | None,
        messages: list[Message] | None,
    ) -> list[Message]:
        if (prompt is None and messages is None) or (prompt is not None and messages is not None):
            raise ValueError("Provide exactly one of `prompt` or `messages`")

        if prompt is not None:
            return [{"role": "user", "content": prompt}]

        if not isinstance(messages, list) or not messages:
            raise ValueError("`messages` must be a non-empty list")
        return [dict(item) for item in messages]

    def _normalize_tool_results(
        self,
        tool_results: list[ToolResult] | None,
    ) -> list[ToolResult]:
        if not tool_results:
            return []

        normalized: list[ToolResult] = []
        for item in tool_results:
            if isinstance(item, ToolResult):
                normalized.append(item)
                continue
            if isinstance(item, dict):
                normalized.append(
                    ToolResult(
                        tool_call_id=str(item["tool_call_id"]),
                        name=str(item["name"]),
                        output=item["output"],
                    )
                )
                continue
            raise TypeError("tool_results items must be ToolResult or dict")
        return normalized

    def model_capabilities(self, model: str) -> ModelCapabilities:
        _ = model
        is_codex_profile = self._is_codex_profile()
        return ModelCapabilities(
            supports_reasoning=True,
            supports_tools=True,
            supports_store=not is_codex_profile,
            supports_response_format=True,
        )

    def _is_codex_profile(self) -> bool:
        return "/backend-api/codex" in self.chatgpt_base_url

    def _supports_remote_files_vector(self) -> bool:
        return not self._is_codex_profile()

    def _raise_local_compat_error(self, exc: Exception) -> None:
        if isinstance(exc, (NotSupportedError, ParameterValidationError, SDKRequestError)):
            raise exc
        if isinstance(exc, (json.JSONDecodeError, OSError)):
            raise SDKRequestError(
                status_code=None,
                provider_code="local_compat_storage_error",
                user_message="Local compatibility storage operation failed",
                retryable=False,
                raw_error={"error": str(exc)},
            ) from exc
        if isinstance(exc, KeyError):
            message = str(exc).strip("'") or "resource not found"
            raise SDKRequestError(
                status_code=404,
                provider_code="not_found",
                user_message=message,
                retryable=False,
                raw_error={"error": message},
            ) from exc
        if isinstance(exc, (TypeError, ValueError)):
            raise ParameterValidationError(str(exc)) from exc
        raise SDKRequestError(
            status_code=None,
            provider_code="local_compat_storage_error",
            user_message="Local compatibility storage operation failed",
            retryable=False,
            raw_error={"error": str(exc)},
        ) from exc

    def _compat_vector_store_request(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_method = method.upper()
        if path == "/vector_stores":
            if normalized_method == "POST":
                return self._compat_store.create_vector_store(payload)
            if normalized_method == "GET":
                return self._compat_store.list_vector_stores(payload)

        if path.startswith("/vector_stores/"):
            tail = path[len("/vector_stores/") :]
            if tail.endswith("/search"):
                vector_store_id = tail[: -len("/search")]
                if not vector_store_id or "/" in vector_store_id:
                    raise ValueError("invalid vector_store_id")
                if normalized_method != "POST":
                    raise ValueError("vector_stores.search only supports POST")
                query = payload.get("query")
                max_num_results = payload.get("max_num_results", 10)
                return self._compat_store.search_vector_store(
                    vector_store_id,
                    query=query,
                    max_num_results=max_num_results,
                )

            if not tail or "/" in tail:
                raise ValueError("invalid vector_store_id")
            if normalized_method == "GET":
                return self._compat_store.retrieve_vector_store(tail)
            if normalized_method == "POST":
                return self._compat_store.update_vector_store(tail, payload)
            if normalized_method == "DELETE":
                return self._compat_store.delete_vector_store(tail)

        raise NotSupportedError(
            f"{path} is not supported on codex OAuth profile",
            code="not_supported_on_codex_oauth",
        )

    def _validate_model_locally(self, model: str) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ModelValidationError("model must be a non-empty string")

    def _emit_hook(self, hook: Callable[[dict[str, Any]], None] | None, payload: dict[str, Any]) -> None:
        if hook is None:
            return
        try:
            hook(payload)
        except Exception:
            return

    def _load_tokens_sync(self) -> OAuthTokens | None:
        try:
            return self.token_store.load()
        except Exception as exc:
            raise TokenStoreReadError("Token store read failed", cause=exc) from exc

    async def _load_tokens_async(self) -> OAuthTokens | None:
        try:
            return await asyncio.to_thread(self.token_store.load)
        except Exception as exc:
            raise TokenStoreReadError("Token store read failed", cause=exc) from exc

    def _save_tokens_sync(self, tokens: OAuthTokens) -> None:
        try:
            self.token_store.save(tokens)
        except Exception as exc:
            raise TokenStoreWriteError("Token store write failed", cause=exc) from exc

    async def _save_tokens_async(self, tokens: OAuthTokens) -> None:
        try:
            await asyncio.to_thread(self.token_store.save, tokens)
        except Exception as exc:
            raise TokenStoreWriteError("Token store write failed", cause=exc) from exc

    def _delete_tokens_sync(self) -> None:
        try:
            self.token_store.delete()
        except Exception as exc:
            raise TokenStoreDeleteError("Token store delete failed", cause=exc) from exc

    async def _delete_tokens_async(self) -> None:
        try:
            await asyncio.to_thread(self.token_store.delete)
        except Exception as exc:
            raise TokenStoreDeleteError("Token store delete failed", cause=exc) from exc

    def _effective_validation_mode(self, override: ValidationMode | None = None) -> ValidationMode:
        return override or self.validation_mode

    def _warn_or_error(
        self,
        message: str,
        *,
        code: str,
        validation_mode: ValidationMode | None = None,
    ) -> None:
        mode = self._effective_validation_mode(validation_mode)
        if mode == "ignore":
            return
        if mode == "error":
            raise ParameterValidationError(f"{code}: {message}")
        warnings.warn(f"{code}: {message}", RuntimeWarning, stacklevel=3)

    def _compute_retry_delay(self, attempt: int) -> float:
        jitter = random.uniform(0.0, self.backoff_base_seconds)
        return self.backoff_base_seconds * (2 ** max(0, attempt)) + jitter

    def _is_retryable_status(self, status_code: int) -> bool:
        return status_code == 429 or status_code >= 500

    def _ensure_authenticated_sync(self) -> OAuthTokens:
        tokens = self._load_tokens_sync()
        if not tokens:
            self.login()
            tokens = self._load_tokens_sync()
            if not tokens:
                raise AuthRequiredError("OAuth login did not produce stored credentials")

        if tokens.is_expired(leeway_seconds=self._refresh_leeway_seconds):
            tokens = self._refresh_and_persist_sync(tokens)
        return tokens

    async def _ensure_authenticated_async(self) -> OAuthTokens:
        tokens = await self._load_tokens_async()
        if not tokens:
            await asyncio.to_thread(self.login)
            tokens = await self._load_tokens_async()
            if not tokens:
                raise AuthRequiredError("OAuth login did not produce stored credentials")

        if tokens.is_expired(leeway_seconds=self._refresh_leeway_seconds):
            tokens = await self._refresh_and_persist_async(tokens)
        return tokens

    def _refresh_and_persist_sync(self, tokens: OAuthTokens) -> OAuthTokens:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                self.oauth_config = discover_endpoints(client, self.oauth_config)
                refreshed = refresh_tokens(client, self.oauth_config, tokens)
            self._save_tokens_sync(refreshed)
            self._emit_hook(
                self.on_auth_refresh,
                {"refreshed": True, "auth_state": "refreshed", "account_id": refreshed.account_id},
            )
            return refreshed
        except TokenRefreshError as exc:
            self._delete_tokens_sync()
            raise AuthRequiredError(
                "Your access token could not be refreshed. Please sign in again."
            ) from exc

    async def _refresh_and_persist_async(self, tokens: OAuthTokens) -> OAuthTokens:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                self.oauth_config = await discover_endpoints_async(client, self.oauth_config)
                refreshed = await refresh_tokens_async(client, self.oauth_config, tokens)
            await self._save_tokens_async(refreshed)
            self._emit_hook(
                self.on_auth_refresh,
                {"refreshed": True, "auth_state": "refreshed", "account_id": refreshed.account_id},
            )
            return refreshed
        except TokenRefreshError as exc:
            await self._delete_tokens_async()
            raise AuthRequiredError(
                "Your access token could not be refreshed. Please sign in again."
            ) from exc

    def _validate_model_sync(self, model: str, tokens: OAuthTokens) -> None:
        _ = tokens
        if self._is_codex_profile():
            self._validate_model_locally(model)
            return
        raise ModelValidationError(
            "Model validation via /models is unavailable on this profile."
        )

    async def _validate_model_async(self, model: str, tokens: OAuthTokens) -> None:
        _ = tokens
        if self._is_codex_profile():
            self._validate_model_locally(model)
            return
        raise ModelValidationError(
            "Model validation via /models is unavailable on this profile."
        )

    def _auth_headers(self, tokens: OAuthTokens) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {tokens.access_token}",
            "Content-Type": "application/json",
        }
        if tokens.account_id:
            headers["ChatGPT-Account-ID"] = tokens.account_id
        return headers

    def _resolve_request_url(self, path: str) -> str:
        if self._is_codex_profile() and path not in {"/responses", "/responses/input_tokens"}:
            raise NotSupportedError(
                f"{path} is not supported on codex OAuth profile",
                code="not_supported_on_codex_oauth",
            )
        return f"{self.chatgpt_base_url}{path}"

    def _normalize_store_value(self, *, store: bool, validation_mode: ValidationMode) -> bool:
        if not store:
            return False
        if not self._is_codex_profile():
            return True
        if self.store_behavior == "passthrough":
            return True
        if self.store_behavior == "error":
            raise ParameterValidationError(
                "store=True is not supported on codex OAuth profile"
            )
        self._warn_or_error(
            "store=True was changed to store=False for codex backend stability",
            code="store_auto_disabled",
            validation_mode=validation_mode,
        )
        return False

    def _normalize_reasoning(
        self,
        reasoning: dict[str, Any] | None,
        *,
        validation_mode: ValidationMode,
    ) -> dict[str, Any] | None:
        if reasoning is None:
            return None
        if not isinstance(reasoning, dict):
            raise ParameterValidationError("reasoning must be a dictionary")
        normalized = dict(reasoning)
        effort = normalized.get("effort")
        if effort is not None and not isinstance(effort, str):
            self._warn_or_error(
                "reasoning.effort should be a string",
                code="invalid_reasoning_effort",
                validation_mode=validation_mode,
            )
            normalized.pop("effort", None)
        summary = normalized.get("summary")
        if summary is not None and not isinstance(summary, (str, bool)):
            self._warn_or_error(
                "reasoning.summary should be a string or boolean",
                code="invalid_reasoning_summary",
                validation_mode=validation_mode,
            )
            normalized.pop("summary", None)
        return normalized

    def _validate_temperature(
        self,
        value: float | None,
        *,
        validation_mode: ValidationMode,
    ) -> float | None:
        if value is None:
            return None
        if not isinstance(value, (int, float)):
            self._warn_or_error(
                "temperature must be numeric",
                code="invalid_temperature",
                validation_mode=validation_mode,
            )
            return None
        if value < 0 or value > 2:
            self._warn_or_error(
                "temperature should be in [0, 2]",
                code="out_of_range_temperature",
                validation_mode=validation_mode,
            )
            return None
        return float(value)

    def _validate_top_p(
        self,
        value: float | None,
        *,
        validation_mode: ValidationMode,
    ) -> float | None:
        if value is None:
            return None
        if not isinstance(value, (int, float)):
            self._warn_or_error(
                "top_p must be numeric",
                code="invalid_top_p",
                validation_mode=validation_mode,
            )
            return None
        if value <= 0 or value > 1:
            self._warn_or_error(
                "top_p should be in (0, 1]",
                code="out_of_range_top_p",
                validation_mode=validation_mode,
            )
            return None
        return float(value)

    def _validate_max_output_tokens(
        self,
        value: int | None,
        *,
        validation_mode: ValidationMode,
    ) -> int | None:
        if value is None:
            return None
        if not isinstance(value, int) or value <= 0:
            self._warn_or_error(
                "max_output_tokens must be a positive integer",
                code="invalid_max_output_tokens",
                validation_mode=validation_mode,
            )
            return None
        return value

    def _validate_metadata(
        self,
        value: dict[str, Any] | None,
        *,
        validation_mode: ValidationMode,
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            self._warn_or_error(
                "metadata must be a dictionary",
                code="invalid_metadata",
                validation_mode=validation_mode,
            )
            return None
        return dict(value)

    def _validate_include(
        self,
        value: list[str] | None,
        *,
        validation_mode: ValidationMode,
    ) -> list[str] | None:
        if value is None:
            return None
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            self._warn_or_error(
                "include must be a list of strings",
                code="invalid_include",
                validation_mode=validation_mode,
            )
            return None
        return list(value)

    def _validate_max_tool_calls(
        self,
        value: int | None,
        *,
        validation_mode: ValidationMode,
    ) -> int | None:
        if value is None:
            return None
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            self._warn_or_error(
                "max_tool_calls must be a positive integer",
                code="invalid_max_tool_calls",
                validation_mode=validation_mode,
            )
            return None
        return value

    def _validate_parallel_tool_calls(
        self,
        value: bool | None,
        *,
        validation_mode: ValidationMode,
    ) -> bool | None:
        if value is None:
            return None
        if not isinstance(value, bool):
            self._warn_or_error(
                "parallel_tool_calls must be a boolean",
                code="invalid_parallel_tool_calls",
                validation_mode=validation_mode,
            )
            return None
        return value

    def _validate_truncation(
        self,
        value: TruncationMode | None,
        *,
        validation_mode: ValidationMode,
    ) -> TruncationMode | None:
        if value is None:
            return None
        if value not in {"auto", "disabled"}:
            self._warn_or_error(
                "truncation must be one of: auto, disabled",
                code="invalid_truncation",
                validation_mode=validation_mode,
            )
            return None
        return value

    def _validate_extra_headers(
        self,
        value: dict[str, str] | None,
        *,
        validation_mode: ValidationMode,
    ) -> dict[str, str] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            self._warn_or_error(
                "extra_headers must be a dictionary",
                code="invalid_extra_headers",
                validation_mode=validation_mode,
            )
            return None
        normalized: dict[str, str] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, str):
                self._warn_or_error(
                    "extra_headers keys and values must be strings",
                    code="invalid_extra_headers",
                    validation_mode=validation_mode,
                )
                return None
            normalized[key] = item
        return normalized

    def _normalize_extra_headers(
        self,
        value: dict[str, str] | None,
        *,
        validation_mode: ValidationMode,
    ) -> dict[str, str] | None:
        normalized = self._validate_extra_headers(value, validation_mode=validation_mode)
        if not normalized:
            return normalized
        filtered: dict[str, str] = {}
        for key, item in normalized.items():
            if key.lower() in self._PROTECTED_REQUEST_HEADERS:
                self._warn_or_error(
                    f"extra_headers cannot override protected header: {key}",
                    code="protected_header_override",
                    validation_mode=validation_mode,
                )
                continue
            filtered[key] = item
        return filtered

    def _validate_extra_query(
        self,
        value: dict[str, Any] | None,
        *,
        validation_mode: ValidationMode,
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            self._warn_or_error(
                "extra_query must be a dictionary",
                code="invalid_extra_query",
                validation_mode=validation_mode,
            )
            return None
        return dict(value)

    def _validate_extra_body(
        self,
        value: dict[str, Any] | None,
        *,
        validation_mode: ValidationMode,
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            self._warn_or_error(
                "extra_body must be a dictionary",
                code="invalid_extra_body",
                validation_mode=validation_mode,
            )
            return None
        return dict(value)

    def _build_responses_payload(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[dict[str, Any]],
        tool_results: list[ToolResult],
        response_format: dict[str, Any] | None,
        tool_choice: str | dict[str, Any] | None,
        strict_output: bool,
        store: bool,
        reasoning: dict[str, Any] | None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        validation_mode: ValidationMode | None = None,
        stream: bool,
    ) -> dict[str, Any]:
        mode = self._effective_validation_mode(validation_mode)
        normalized_store = self._normalize_store_value(store=store, validation_mode=mode)
        normalized_reasoning = self._normalize_reasoning(reasoning, validation_mode=mode)
        normalized_temperature = self._validate_temperature(temperature, validation_mode=mode)
        normalized_top_p = self._validate_top_p(top_p, validation_mode=mode)
        normalized_max_output_tokens = self._validate_max_output_tokens(
            max_output_tokens, validation_mode=mode
        )
        normalized_metadata = self._validate_metadata(metadata, validation_mode=mode)
        normalized_include = self._validate_include(include, validation_mode=mode)
        normalized_max_tool_calls = self._validate_max_tool_calls(
            max_tool_calls, validation_mode=mode
        )
        normalized_parallel_tool_calls = self._validate_parallel_tool_calls(
            parallel_tool_calls, validation_mode=mode
        )
        normalized_truncation = self._validate_truncation(truncation, validation_mode=mode)
        normalized_extra_body = self._validate_extra_body(extra_body, validation_mode=mode)
        if service_tier is not None:
            self._warn_or_error(
                "service_tier is currently ignored on codex backend",
                code="service_tier_ignored",
                validation_mode=mode,
            )

        effective_input, upstream_previous_response_id = self._build_effective_responses_input(
            messages=messages,
            tool_results=tool_results,
            previous_response_id=previous_response_id,
        )
        payload: dict[str, Any] = {
            "model": model,
            "input": effective_input,
            "instructions": instructions or self._derive_instructions(messages),
            "store": normalized_store,
            "stream": stream,
        }
        if tools:
            payload["tools"] = to_responses_tools(tools, strict_output=strict_output)
        if response_format is not None:
            payload["text"] = {"format": dict(response_format)}
        if tool_choice is not None:
            payload["tool_choice"] = dict(tool_choice) if isinstance(tool_choice, dict) else tool_choice
        if normalized_reasoning is not None:
            payload["reasoning"] = normalized_reasoning
        if normalized_temperature is not None:
            payload["temperature"] = normalized_temperature
        if normalized_top_p is not None:
            payload["top_p"] = normalized_top_p
        if normalized_max_output_tokens is not None:
            payload["max_output_tokens"] = normalized_max_output_tokens
        if normalized_metadata is not None:
            payload["metadata"] = normalized_metadata
        if normalized_include is not None:
            payload["include"] = normalized_include
        if normalized_max_tool_calls is not None:
            payload["max_tool_calls"] = normalized_max_tool_calls
        if normalized_parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = normalized_parallel_tool_calls
        if normalized_truncation is not None:
            payload["truncation"] = normalized_truncation
        if upstream_previous_response_id:
            payload["previous_response_id"] = upstream_previous_response_id
        if normalized_extra_body:
            payload.update(normalized_extra_body)
        return payload

    def _generate_responses_sync(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[dict[str, Any]],
        tool_results: list[ToolResult],
        response_format: dict[str, Any] | None,
        tool_choice: str | dict[str, Any] | None,
        strict_output: bool,
        store: bool,
        reasoning: dict[str, Any] | None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        validation_mode: ValidationMode | None = None,
    ) -> GenerateResult:
        events = self._stream_responses_sync(
            model=model,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            validation_mode=validation_mode,
        )
        return self._collect_generate_result_from_stream_sync(events)

    async def _generate_responses_async(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[dict[str, Any]],
        tool_results: list[ToolResult],
        response_format: dict[str, Any] | None,
        tool_choice: str | dict[str, Any] | None,
        strict_output: bool,
        store: bool,
        reasoning: dict[str, Any] | None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        validation_mode: ValidationMode | None = None,
    ) -> GenerateResult:
        events = self._stream_responses_async(
            model=model,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            validation_mode=validation_mode,
        )
        return await self._collect_generate_result_from_stream_async(events)

    def _stream_responses_sync(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[dict[str, Any]],
        tool_results: list[ToolResult],
        response_format: dict[str, Any] | None,
        tool_choice: str | dict[str, Any] | None,
        strict_output: bool,
        store: bool,
        reasoning: dict[str, Any] | None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        validation_mode: ValidationMode | None = None,
    ) -> Iterator[StreamEvent]:
        tokens = self._ensure_authenticated_sync()
        mode = self._effective_validation_mode(validation_mode)
        payload = self._build_responses_payload(
            model=model,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_body=extra_body,
            service_tier=service_tier,
            validation_mode=mode,
            stream=True,
        )
        normalized_extra_headers = self._normalize_extra_headers(
            extra_headers, validation_mode=mode
        )
        normalized_extra_query = self._validate_extra_query(extra_query, validation_mode=mode)
        request_input: list[Message] = []
        if self._is_codex_profile():
            raw_request_input = payload.get("input")
            if isinstance(raw_request_input, list):
                request_input = [dict(item) for item in raw_request_input if isinstance(item, dict)]

        text_parts: list[str] = []
        tool_calls_acc: list[ToolCall] = []
        raw_response: dict[str, Any] | None = None
        response_id: str | None = None
        saw_error = False
        persisted = False

        for event in self._stream_sse_sync(
            path="/responses",
            payload=payload,
            parser=self._map_responses_stream,
            tokens=tokens,
            extra_headers=normalized_extra_headers,
            extra_query=normalized_extra_query,
            validation_mode=mode,
        ):
            if self._is_codex_profile():
                if event.type == "text_delta" and isinstance(event.delta, str):
                    text_parts.append(event.delta)
                elif event.type == "tool_call_done" and event.tool_call is not None:
                    tool_calls_acc.append(event.tool_call)
                elif event.type == "error":
                    saw_error = True

                if isinstance(event.raw, dict):
                    raw_response = event.raw
                    maybe_response_id = self._extract_response_id(event.raw)
                    if maybe_response_id:
                        response_id = maybe_response_id
                if event.response_id:
                    response_id = event.response_id

                if (
                    not persisted
                    and not saw_error
                    and event.type in {"response_completed", "done"}
                ):
                    self._persist_response_continuity_sync(
                        model=model,
                        request_input=request_input,
                        response_id=response_id,
                        previous_response_id=previous_response_id,
                        raw_response=raw_response,
                        text_parts=text_parts,
                        tool_calls=tool_calls_acc,
                    )
                    persisted = True

            yield event

        if self._is_codex_profile() and not persisted and not saw_error:
            self._persist_response_continuity_sync(
                model=model,
                request_input=request_input,
                response_id=response_id,
                previous_response_id=previous_response_id,
                raw_response=raw_response,
                text_parts=text_parts,
                tool_calls=tool_calls_acc,
            )

    async def _stream_responses_async(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[dict[str, Any]],
        tool_results: list[ToolResult],
        response_format: dict[str, Any] | None,
        tool_choice: str | dict[str, Any] | None,
        strict_output: bool,
        store: bool,
        reasoning: dict[str, Any] | None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        validation_mode: ValidationMode | None = None,
    ) -> AsyncIterator[StreamEvent]:
        tokens = await self._ensure_authenticated_async()
        mode = self._effective_validation_mode(validation_mode)
        payload = self._build_responses_payload(
            model=model,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_body=extra_body,
            service_tier=service_tier,
            validation_mode=mode,
            stream=True,
        )
        normalized_extra_headers = self._normalize_extra_headers(
            extra_headers, validation_mode=mode
        )
        normalized_extra_query = self._validate_extra_query(extra_query, validation_mode=mode)
        request_input: list[Message] = []
        if self._is_codex_profile():
            raw_request_input = payload.get("input")
            if isinstance(raw_request_input, list):
                request_input = [dict(item) for item in raw_request_input if isinstance(item, dict)]

        text_parts: list[str] = []
        tool_calls_acc: list[ToolCall] = []
        raw_response: dict[str, Any] | None = None
        response_id: str | None = None
        saw_error = False
        persisted = False

        async for event in self._stream_sse_async(
            path="/responses",
            payload=payload,
            parser=self._map_responses_stream,
            tokens=tokens,
            extra_headers=normalized_extra_headers,
            extra_query=normalized_extra_query,
            validation_mode=mode,
        ):
            if self._is_codex_profile():
                if event.type == "text_delta" and isinstance(event.delta, str):
                    text_parts.append(event.delta)
                elif event.type == "tool_call_done" and event.tool_call is not None:
                    tool_calls_acc.append(event.tool_call)
                elif event.type == "error":
                    saw_error = True

                if isinstance(event.raw, dict):
                    raw_response = event.raw
                    maybe_response_id = self._extract_response_id(event.raw)
                    if maybe_response_id:
                        response_id = maybe_response_id
                if event.response_id:
                    response_id = event.response_id

                if (
                    not persisted
                    and not saw_error
                    and event.type in {"response_completed", "done"}
                ):
                    await self._persist_response_continuity_async(
                        model=model,
                        request_input=request_input,
                        response_id=response_id,
                        previous_response_id=previous_response_id,
                        raw_response=raw_response,
                        text_parts=text_parts,
                        tool_calls=tool_calls_acc,
                    )
                    persisted = True

            yield event

        if self._is_codex_profile() and not persisted and not saw_error:
            await self._persist_response_continuity_async(
                model=model,
                request_input=request_input,
                response_id=response_id,
                previous_response_id=previous_response_id,
                raw_response=raw_response,
                text_parts=text_parts,
                tool_calls=tool_calls_acc,
            )

    def _stream_sse_sync(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        parser,
        tokens: OAuthTokens | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        validation_mode: ValidationMode | None = None,
    ) -> Iterator[StreamEvent]:
        if tokens is None:
            tokens = self._ensure_authenticated_sync()
        url = self._resolve_request_url(path)
        attempted_refresh = False
        last_error: SDKRequestError | None = None
        mode = self._effective_validation_mode(validation_mode)
        normalized_extra_headers = self._normalize_extra_headers(
            extra_headers, validation_mode=mode
        )
        normalized_extra_query = self._validate_extra_query(extra_query, validation_mode=mode)

        for attempt in range(self.max_retries + 1):
            request_id = f"req_{uuid.uuid4().hex}"
            self._emit_hook(
                self.on_request_start,
                {
                    "request_id": request_id,
                    "path": path,
                    "model": payload.get("model"),
                    "auth_state": "authenticated",
                    "refreshed": attempted_refresh,
                    "options": payload,
                },
            )
            headers = self._auth_headers(tokens)
            if normalized_extra_headers:
                headers.update(normalized_extra_headers)
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=payload,
                    params=normalized_extra_query,
                ) as response:
                    if response.status_code == 401 and not attempted_refresh:
                        tokens = self._refresh_and_persist_sync(tokens)
                        attempted_refresh = True
                        continue
                    if self._is_retryable_status(response.status_code) and attempt < self.max_retries:
                        response.read()
                        time.sleep(self._compute_retry_delay(attempt))
                        continue
                    if response.status_code >= 400:
                        response.read()
                        last_error = self._build_sdk_request_error(response, request_id=request_id)
                        self._emit_hook(
                            self.on_error,
                            {
                                "request_id": request_id,
                                "status_code": last_error.status_code,
                                "provider_code": last_error.provider_code,
                                "message": last_error.user_message,
                                "retryable": last_error.retryable,
                            },
                        )
                        raise last_error

                    for event_name, data_text in self._iter_sse_events(response.iter_lines()):
                        if data_text == "[DONE]":
                            self._emit_hook(
                                self.on_request_end,
                                {
                                    "request_id": request_id,
                                    "path": path,
                                    "status_code": response.status_code,
                                    "refreshed": attempted_refresh,
                                },
                            )
                            yield StreamEvent(type="done")
                            return

                        payload_obj = self._parse_sse_data(data_text)
                        if payload_obj is None:
                            continue

                        mapped = parser(event_name, payload_obj)
                        for item in mapped:
                            yield item
                    self._emit_hook(
                        self.on_request_end,
                        {
                            "request_id": request_id,
                            "path": path,
                            "status_code": response.status_code,
                            "refreshed": attempted_refresh,
                        },
                    )
                    return
        if last_error is not None:
            raise last_error
        raise SDKRequestError(
            status_code=None,
            provider_code="retry_exhausted",
            user_message="Streaming request failed after retries",
            retryable=False,
        )

    async def _stream_sse_async(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        parser,
        tokens: OAuthTokens | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        validation_mode: ValidationMode | None = None,
    ) -> AsyncIterator[StreamEvent]:
        if tokens is None:
            tokens = await self._ensure_authenticated_async()
        url = self._resolve_request_url(path)
        attempted_refresh = False
        last_error: SDKRequestError | None = None
        mode = self._effective_validation_mode(validation_mode)
        normalized_extra_headers = self._normalize_extra_headers(
            extra_headers, validation_mode=mode
        )
        normalized_extra_query = self._validate_extra_query(extra_query, validation_mode=mode)

        for attempt in range(self.max_retries + 1):
            request_id = f"req_{uuid.uuid4().hex}"
            self._emit_hook(
                self.on_request_start,
                {
                    "request_id": request_id,
                    "path": path,
                    "model": payload.get("model"),
                    "auth_state": "authenticated",
                    "refreshed": attempted_refresh,
                    "options": payload,
                },
            )
            headers = self._auth_headers(tokens)
            if normalized_extra_headers:
                headers.update(normalized_extra_headers)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=payload,
                    params=normalized_extra_query,
                ) as response:
                    if response.status_code == 401 and not attempted_refresh:
                        tokens = await self._refresh_and_persist_async(tokens)
                        attempted_refresh = True
                        continue
                    if self._is_retryable_status(response.status_code) and attempt < self.max_retries:
                        await response.aread()
                        await asyncio.sleep(self._compute_retry_delay(attempt))
                        continue
                    if response.status_code >= 400:
                        await response.aread()
                        last_error = self._build_sdk_request_error(response, request_id=request_id)
                        self._emit_hook(
                            self.on_error,
                            {
                                "request_id": request_id,
                                "status_code": last_error.status_code,
                                "provider_code": last_error.provider_code,
                                "message": last_error.user_message,
                                "retryable": last_error.retryable,
                            },
                        )
                        raise last_error

                    async for event_name, data_text in self._aiter_sse_events(response.aiter_lines()):
                        if data_text == "[DONE]":
                            self._emit_hook(
                                self.on_request_end,
                                {
                                    "request_id": request_id,
                                    "path": path,
                                    "status_code": response.status_code,
                                    "refreshed": attempted_refresh,
                                },
                            )
                            yield StreamEvent(type="done")
                            return

                        payload_obj = self._parse_sse_data(data_text)
                        if payload_obj is None:
                            continue

                        mapped = parser(event_name, payload_obj)
                        for item in mapped:
                            yield item
                    self._emit_hook(
                        self.on_request_end,
                        {
                            "request_id": request_id,
                            "path": path,
                            "status_code": response.status_code,
                            "refreshed": attempted_refresh,
                        },
                    )
                    return
        if last_error is not None:
            raise last_error
        raise SDKRequestError(
            status_code=None,
            provider_code="retry_exhausted",
            user_message="Streaming request failed after retries",
            retryable=False,
        )

    def _iter_sse_events(self, lines: Iterator[str]) -> Iterator[tuple[str, str]]:
        event_name = "message"
        data_lines: list[str] = []

        for raw in lines:
            line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            if line == "":
                if data_lines:
                    yield event_name, "\n".join(data_lines)
                event_name = "message"
                data_lines = []
                continue

            if line.startswith("event:"):
                event_name = line[6:].strip() or "message"
                continue

            if line.startswith("data:"):
                data_lines.append(line[5:].strip())

        if data_lines:
            yield event_name, "\n".join(data_lines)

    async def _aiter_sse_events(self, lines: AsyncIterator[str]) -> AsyncIterator[tuple[str, str]]:
        event_name = "message"
        data_lines: list[str] = []

        async for raw in lines:
            line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            if line == "":
                if data_lines:
                    yield event_name, "\n".join(data_lines)
                event_name = "message"
                data_lines = []
                continue

            if line.startswith("event:"):
                event_name = line[6:].strip() or "message"
                continue

            if line.startswith("data:"):
                data_lines.append(line[5:].strip())

        if data_lines:
            yield event_name, "\n".join(data_lines)

    def _parse_sse_data(self, data_text: str) -> dict[str, Any] | None:
        try:
            payload = json.loads(data_text)
        except ValueError:
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    def _derive_instructions(self, messages: list[Message]) -> str:
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            if msg.get("role") != "system":
                continue
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
        return "You are Codex, a helpful coding assistant."

    def _collect_generate_result_from_stream_sync(
        self,
        events: Iterator[StreamEvent],
    ) -> GenerateResult:
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        usage: TokenUsage | None = None
        raw_response: dict[str, Any] | None = None
        error_message: str | None = None
        response_id: str | None = None
        finish_reason: Literal["stop", "tool_calls", "length", "error"] = "stop"

        for event in events:
            if isinstance(event.raw, dict):
                raw_response = event.raw
                maybe_id = event.raw.get("id")
                if isinstance(maybe_id, str):
                    response_id = maybe_id
                status = event.raw.get("status")
                if isinstance(status, str) and status == "incomplete":
                    finish_reason = "length"
            if event.response_id:
                response_id = event.response_id
            if event.type == "text_delta" and isinstance(event.delta, str):
                text_parts.append(event.delta)
            elif event.type == "tool_call_done" and event.tool_call is not None:
                tool_calls.append(event.tool_call)
            elif event.type == "usage":
                usage = event.usage
            elif event.type == "error":
                error_message = event.error or "Streaming request failed"
                finish_reason = "error"
            elif event.type == "response_completed" and event.finish_reason:
                if event.finish_reason in {"stop", "tool_calls", "length", "error"}:
                    finish_reason = event.finish_reason  # type: ignore[assignment]

        if error_message:
            raise SDKRequestError(
                status_code=None,
                provider_code="stream_error",
                user_message=error_message,
                retryable=False,
                raw_error=raw_response,
            )

        if finish_reason == "stop" and tool_calls:
            finish_reason = "tool_calls"

        return GenerateResult(
            text="".join(text_parts),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            raw_response=raw_response,
            response_id=response_id,
        )

    async def _collect_generate_result_from_stream_async(
        self,
        events: AsyncIterator[StreamEvent],
    ) -> GenerateResult:
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        usage: TokenUsage | None = None
        raw_response: dict[str, Any] | None = None
        error_message: str | None = None
        response_id: str | None = None
        finish_reason: Literal["stop", "tool_calls", "length", "error"] = "stop"

        async for event in events:
            if isinstance(event.raw, dict):
                raw_response = event.raw
                maybe_id = event.raw.get("id")
                if isinstance(maybe_id, str):
                    response_id = maybe_id
                status = event.raw.get("status")
                if isinstance(status, str) and status == "incomplete":
                    finish_reason = "length"
            if event.response_id:
                response_id = event.response_id
            if event.type == "text_delta" and isinstance(event.delta, str):
                text_parts.append(event.delta)
            elif event.type == "tool_call_done" and event.tool_call is not None:
                tool_calls.append(event.tool_call)
            elif event.type == "usage":
                usage = event.usage
            elif event.type == "error":
                error_message = event.error or "Streaming request failed"
                finish_reason = "error"
            elif event.type == "response_completed" and event.finish_reason:
                if event.finish_reason in {"stop", "tool_calls", "length", "error"}:
                    finish_reason = event.finish_reason  # type: ignore[assignment]

        if error_message:
            raise SDKRequestError(
                status_code=None,
                provider_code="stream_error",
                user_message=error_message,
                retryable=False,
                raw_error=raw_response,
            )

        if finish_reason == "stop" and tool_calls:
            finish_reason = "tool_calls"

        return GenerateResult(
            text="".join(text_parts),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            raw_response=raw_response,
            response_id=response_id,
        )

    def _map_responses_stream(
        self,
        event_name: str,
        payload: dict[str, Any],
    ) -> list[StreamEvent]:
        out: list[StreamEvent] = []
        event_type = str(payload.get("type") or event_name)
        response_id = self._extract_response_id(payload)

        if event_type.endswith("created"):
            out.append(
                StreamEvent(
                    type="response_started",
                    response_id=response_id,
                    raw=payload,
                )
            )

        if event_type.endswith("output_text.delta"):
            delta = payload.get("delta")
            if isinstance(delta, str):
                out.append(
                    StreamEvent(
                        type="text_delta",
                        delta=delta,
                        response_id=response_id,
                        raw=payload,
                    )
                )

        if "reasoning" in event_type and event_type.endswith(".delta"):
            delta = payload.get("delta")
            if isinstance(delta, str):
                out.append(
                    StreamEvent(
                        type="reasoning_delta",
                        delta=delta,
                        response_id=response_id,
                        raw=payload,
                    )
                )

        if "function_call_arguments.delta" in event_type:
            call_id = str(payload.get("call_id") or payload.get("id") or "")
            name = str(payload.get("name") or self._tool_call_name_by_id.get(call_id) or "tool")
            if call_id:
                self._tool_call_name_by_id[call_id] = name
                prev = self._tool_call_args_buffer.get(call_id, "")
                delta_val = payload.get("delta")
                delta_text = delta_val if isinstance(delta_val, str) else ""
                self._tool_call_args_buffer[call_id] = prev + delta_text
                if call_id not in self._tool_call_started:
                    self._tool_call_started.add(call_id)
                    out.append(
                        StreamEvent(
                            type="tool_call_started",
                            call_id=call_id,
                            response_id=response_id,
                            raw=payload,
                        )
                    )
            delta = payload.get("delta")
            out.append(
                StreamEvent(
                    type="tool_call_arguments_delta",
                    delta=delta if isinstance(delta, str) else None,
                    call_id=call_id or None,
                    response_id=response_id,
                    raw=payload,
                )
            )
            # Backward-compatible alias
            out.append(
                StreamEvent(
                    type="tool_call_delta",
                    delta=delta if isinstance(delta, str) else None,
                    call_id=call_id or None,
                    response_id=response_id,
                    raw=payload,
                )
            )

        if "function_call_arguments.done" in event_type:
            call_id = str(payload.get("call_id") or payload.get("id") or "")
            name = str(payload.get("name") or self._tool_call_name_by_id.get(call_id) or "tool")
            arguments_json = str(
                payload.get("arguments")
                or self._tool_call_args_buffer.get(call_id)
                or "{}"
            )
            if call_id and call_id not in self._tool_call_started:
                self._tool_call_started.add(call_id)
                out.append(
                    StreamEvent(
                        type="tool_call_started",
                        call_id=call_id,
                        response_id=response_id,
                        raw=payload,
                    )
                )
            out.append(
                StreamEvent(
                    type="tool_call_done",
                    tool_call=self._build_tool_call(call_id, name, arguments_json),
                    call_id=call_id or None,
                    response_id=response_id,
                    raw=payload,
                )
            )
            if call_id:
                self._tool_call_started.discard(call_id)
                self._tool_call_args_buffer.pop(call_id, None)
                self._tool_call_name_by_id.pop(call_id, None)

        if "usage" in payload:
            out.append(
                StreamEvent(
                    type="usage",
                    usage=self._parse_usage(payload.get("usage")),
                    response_id=response_id,
                    raw=payload,
                )
            )

        if "reasoning" in event_type and event_type.endswith(".done"):
            out.append(
                StreamEvent(
                    type="reasoning_done",
                    response_id=response_id,
                    raw=payload,
                )
            )

        if event_type.endswith("completed"):
            out.append(
                StreamEvent(
                    type="response_completed",
                    response_id=response_id,
                    finish_reason=self._extract_finish_reason(payload),
                    raw=payload,
                )
            )
            out.append(StreamEvent(type="done", response_id=response_id, raw=payload))

        if event_type.endswith("error") or payload.get("error"):
            out.append(
                StreamEvent(
                    type="error",
                    response_id=response_id,
                    raw=payload,
                    error=self._extract_error_text(payload),
                )
            )

        return out

    def _build_tool_call(self, call_id: str, name: str, arguments_json: str) -> ToolCall:
        parsed: dict[str, Any] | None
        try:
            obj = json.loads(arguments_json)
            parsed = obj if isinstance(obj, dict) else None
        except ValueError:
            parsed = None
        return ToolCall(id=call_id, name=name, arguments_json=arguments_json, arguments=parsed)

    def _extract_response_id(self, payload: dict[str, Any]) -> str | None:
        rid = payload.get("response_id")
        if isinstance(rid, str):
            return rid
        rid = payload.get("id")
        if isinstance(rid, str):
            return rid
        response_obj = payload.get("response")
        if isinstance(response_obj, dict):
            rid2 = response_obj.get("id")
            if isinstance(rid2, str):
                return rid2
        return None

    def _extract_finish_reason(self, payload: dict[str, Any]) -> str:
        for key in ("finish_reason", "reason", "status"):
            val = payload.get(key)
            if isinstance(val, str) and val:
                if val in {"completed", "stop"}:
                    return "stop"
                if val in {"tool_calls", "requires_action"}:
                    return "tool_calls"
                if val in {"length", "max_output_tokens"}:
                    return "length"
                if val in {"error", "failed"}:
                    return "error"
                return val
        return "stop"

    def _parse_usage(self, usage: Any) -> TokenUsage | None:
        if not isinstance(usage, dict):
            return None

        output_tokens_details = usage.get("output_tokens_details")
        input_tokens_details = usage.get("input_tokens_details")

        reasoning_output_tokens = None
        cached_input_tokens = None

        if isinstance(output_tokens_details, dict):
            val = output_tokens_details.get("reasoning_tokens")
            if isinstance(val, int):
                reasoning_output_tokens = val

        if isinstance(input_tokens_details, dict):
            val = input_tokens_details.get("cached_tokens")
            if isinstance(val, int):
                cached_input_tokens = val

        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        total_tokens = usage.get("total_tokens")

        return TokenUsage(
            input_tokens=input_tokens if isinstance(input_tokens, int) else None,
            cached_tokens=cached_input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens if isinstance(output_tokens, int) else None,
            reasoning_tokens=reasoning_output_tokens,
            reasoning_output_tokens=reasoning_output_tokens,
            total_tokens=total_tokens if isinstance(total_tokens, int) else None,
        )

    def _extract_error_text(self, payload: dict[str, Any]) -> str:
        err = payload.get("error")
        if isinstance(err, dict):
            parts = [err.get("type"), err.get("message")]
            return " ".join([str(x) for x in parts if x])
        if isinstance(err, str):
            return err
        return "Unknown error"

    def _build_sdk_request_error(
        self,
        response: httpx.Response,
        *,
        request_id: str | None = None,
    ) -> SDKRequestError:
        status_code = response.status_code
        provider_code: str | None = None
        user_message = f"HTTP {status_code}"
        raw_error: Any = None

        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            raw_error = payload
            err = payload.get("error")
            if isinstance(err, dict):
                code = err.get("code") or err.get("type")
                if isinstance(code, str):
                    provider_code = code
                msg = err.get("message")
                if isinstance(msg, str) and msg:
                    user_message = msg
            elif isinstance(err, str):
                user_message = err
            elif isinstance(payload.get("message"), str):
                user_message = payload["message"]
            elif isinstance(payload.get("detail"), str):
                user_message = payload["detail"]
        retryable = status_code == 401 or self._is_retryable_status(status_code)
        return SDKRequestError(
            status_code=status_code,
            provider_code=provider_code,
            user_message=user_message,
            retryable=retryable,
            request_id=request_id,
            raw_error=raw_error,
        )

    def _error_message(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return f"HTTP {response.status_code}"

        if isinstance(payload, dict):
            err = payload.get("error")
            if isinstance(err, dict):
                msg = err.get("message") or err.get("type")
                if msg:
                    return f"HTTP {response.status_code}: {msg}"
            if isinstance(err, str):
                return f"HTTP {response.status_code}: {err}"
            detail = payload.get("detail")
            if isinstance(detail, str) and detail:
                return f"HTTP {response.status_code}: {detail}"
            if "message" in payload:
                return f"HTTP {response.status_code}: {payload['message']}"

        return f"HTTP {response.status_code}"

    def _text_only_stream(self, events: Iterator[StreamEvent]) -> Iterator[str]:
        for event in events:
            if event.type == "text_delta" and event.delta is not None:
                yield event.delta

    async def _text_only_stream_async(self, events: AsyncIterator[StreamEvent]) -> AsyncIterator[str]:
        async for event in events:
            if event.type == "text_delta" and event.delta is not None:
                yield event.delta


class _ResponsesInputTokensResource:
    def __init__(self, engine: OAuthCodexClient) -> None:
        self._engine = engine

    def count(
        self,
        *,
        model: str,
        input: str | dict[str, Any] | list[dict[str, Any]],
        tools: list[ToolInput] | None = None,
    ) -> InputTokensCountResult:
        return self._engine.responses_input_tokens_count(model=model, input=input, tools=tools)


class _AsyncResponsesInputTokensResource:
    def __init__(self, engine: OAuthCodexClient) -> None:
        self._engine = engine

    async def count(
        self,
        *,
        model: str,
        input: str | dict[str, Any] | list[dict[str, Any]],
        tools: list[ToolInput] | None = None,
    ) -> InputTokensCountResult:
        return await self._engine.aresponses_input_tokens_count(model=model, input=input, tools=tools)


class _ResponsesResource:
    def __init__(self, engine: OAuthCodexClient) -> None:
        self._engine = engine
        self.input_tokens = _ResponsesInputTokensResource(engine)

    def create(
        self,
        *,
        model: str,
        input: str | dict[str, Any] | list[dict[str, Any]] | None = None,
        messages: list[dict[str, Any]] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        stream: bool = False,
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> ResponseCompat | Iterator[StreamEvent]:
        return self._engine.responses_create(
            model=model,
            input=input,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            stream=stream,
            validation_mode=validation_mode,
            **extra,
        )


class _AsyncResponsesResource:
    def __init__(self, engine: OAuthCodexClient) -> None:
        self._engine = engine
        self.input_tokens = _AsyncResponsesInputTokensResource(engine)

    async def create(
        self,
        *,
        model: str,
        input: str | dict[str, Any] | list[dict[str, Any]] | None = None,
        messages: list[dict[str, Any]] | None = None,
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
        response_format: dict[str, Any] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        strict_output: bool = False,
        store: bool = False,
        reasoning: dict[str, Any] | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
        include: list[str] | None = None,
        max_tool_calls: int | None = None,
        parallel_tool_calls: bool | None = None,
        truncation: TruncationMode | None = None,
        extra_headers: dict[str, str] | None = None,
        extra_query: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        service_tier: str | None = None,
        stream: bool = False,
        validation_mode: ValidationMode | None = None,
        **extra: Any,
    ) -> ResponseCompat | AsyncIterator[StreamEvent]:
        return await self._engine.aresponses_create(
            model=model,
            input=input,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
            response_format=response_format,
            tool_choice=tool_choice,
            strict_output=strict_output,
            store=store,
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            instructions=instructions,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            metadata=metadata,
            include=include,
            max_tool_calls=max_tool_calls,
            parallel_tool_calls=parallel_tool_calls,
            truncation=truncation,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            service_tier=service_tier,
            stream=stream,
            validation_mode=validation_mode,
            **extra,
        )


class _FilesResource:
    def __init__(self, engine: OAuthCodexClient) -> None:
        self._engine = engine

    def create(self, *, file: Any, purpose: str, **metadata: Any) -> dict[str, Any]:
        return self._engine.files_create(file=file, purpose=purpose, **metadata)


class _AsyncFilesResource:
    def __init__(self, engine: OAuthCodexClient) -> None:
        self._engine = engine

    async def create(self, *, file: Any, purpose: str, **metadata: Any) -> dict[str, Any]:
        return await self._engine.afiles_create(file=file, purpose=purpose, **metadata)


class _VectorStoresResource:
    def __init__(self, engine: OAuthCodexClient) -> None:
        self._engine = engine

    def create(self, **payload: Any) -> dict[str, Any]:
        return self._engine.vector_store_request(method="POST", path="/vector_stores", payload=payload)

    def retrieve(self, vector_store_id: str) -> dict[str, Any]:
        return self._engine.vector_store_request(
            method="GET", path=f"/vector_stores/{vector_store_id}", payload={}
        )

    def list(self, **params: Any) -> dict[str, Any]:
        return self._engine.vector_store_request(method="GET", path="/vector_stores", payload=params)

    def update(self, vector_store_id: str, **payload: Any) -> dict[str, Any]:
        return self._engine.vector_store_request(
            method="POST", path=f"/vector_stores/{vector_store_id}", payload=payload
        )

    def delete(self, vector_store_id: str) -> dict[str, Any]:
        return self._engine.vector_store_request(
            method="DELETE", path=f"/vector_stores/{vector_store_id}", payload={}
        )

    def search(self, vector_store_id: str, *, query: str, **payload: Any) -> dict[str, Any]:
        return self._engine.vector_store_request(
            method="POST",
            path=f"/vector_stores/{vector_store_id}/search",
            payload={"query": query, **payload},
        )


class _AsyncVectorStoresResource:
    def __init__(self, engine: OAuthCodexClient) -> None:
        self._engine = engine

    async def create(self, **payload: Any) -> dict[str, Any]:
        return await self._engine.avector_store_request(
            method="POST", path="/vector_stores", payload=payload
        )

    async def retrieve(self, vector_store_id: str) -> dict[str, Any]:
        return await self._engine.avector_store_request(
            method="GET", path=f"/vector_stores/{vector_store_id}", payload={}
        )

    async def list(self, **params: Any) -> dict[str, Any]:
        return await self._engine.avector_store_request(
            method="GET", path="/vector_stores", payload=params
        )

    async def update(self, vector_store_id: str, **payload: Any) -> dict[str, Any]:
        return await self._engine.avector_store_request(
            method="POST", path=f"/vector_stores/{vector_store_id}", payload=payload
        )

    async def delete(self, vector_store_id: str) -> dict[str, Any]:
        return await self._engine.avector_store_request(
            method="DELETE", path=f"/vector_stores/{vector_store_id}", payload={}
        )

    async def search(self, vector_store_id: str, *, query: str, **payload: Any) -> dict[str, Any]:
        return await self._engine.avector_store_request(
            method="POST",
            path=f"/vector_stores/{vector_store_id}/search",
            payload={"query": query, **payload},
        )


class _ModelsResource:
    def __init__(self, engine: OAuthCodexClient) -> None:
        self._engine = engine

    def capabilities(self, model: str) -> ModelCapabilities:
        return self._engine.model_capabilities(model)


class _AsyncModelsResource:
    def __init__(self, engine: OAuthCodexClient) -> None:
        self._engine = engine

    async def capabilities(self, model: str) -> ModelCapabilities:
        return self._engine.model_capabilities(model)


class AsyncOAuthCodexClient:
    def __init__(
        self,
        *,
        oauth_config: OAuthConfig | None = None,
        token_store: TokenStore | None = None,
        chatgpt_base_url: str = "https://chatgpt.com/backend-api/codex",
        timeout: float = 60.0,
        validation_mode: ValidationMode = "warn",
        store_behavior: StoreBehavior = "auto_disable",
        max_retries: int = 2,
        backoff_base_seconds: float = 0.25,
        compat_storage_dir: str | Path | None = None,
        on_request_start: Callable[[dict[str, Any]], None] | None = None,
        on_request_end: Callable[[dict[str, Any]], None] | None = None,
        on_auth_refresh: Callable[[dict[str, Any]], None] | None = None,
        on_error: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self._engine = OAuthCodexClient(
            oauth_config=oauth_config,
            token_store=token_store,
            chatgpt_base_url=chatgpt_base_url,
            timeout=timeout,
            validation_mode=validation_mode,
            store_behavior=store_behavior,
            max_retries=max_retries,
            backoff_base_seconds=backoff_base_seconds,
            compat_storage_dir=compat_storage_dir,
            on_request_start=on_request_start,
            on_request_end=on_request_end,
            on_auth_refresh=on_auth_refresh,
            on_error=on_error,
        )
        self.responses = _AsyncResponsesResource(self._engine)
        self.files = _AsyncFilesResource(self._engine)
        self.vector_stores = _AsyncVectorStoresResource(self._engine)
        self.models = _AsyncModelsResource(self._engine)

    def is_authenticated(self) -> bool:
        return self._engine.is_authenticated()

    def is_expired(self, *, leeway_seconds: int = 60) -> bool:
        return self._engine.is_expired(leeway_seconds=leeway_seconds)

    async def refresh_if_needed(self, *, force: bool = False) -> bool:
        return await self._engine.arefresh_if_needed(force=force)

    async def login(self) -> None:
        await asyncio.to_thread(self._engine.login)
