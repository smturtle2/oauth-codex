from __future__ import annotations

import asyncio
import inspect
import json
from collections.abc import AsyncIterator, Iterator
from typing import Any, Callable, Literal, cast, get_type_hints

from pydantic import BaseModel

from ._sdk_client import AsyncClient as _CodexAsyncClient
from ._sdk_client import Client as _CodexClient

from ._base_client import AsyncAPIClient, SyncAPIClient
from ._engine import OAuthCodexClient as _EngineClient
from .auth.config import OAuthConfig
from .core_types import (
    GenerateResult,
    OAuthTokens,
    ReasoningEffort,
    StreamEvent,
    TokenUsage,
    ToolCall,
    ToolResult,
    listMessage,
)
from .store import FallbackTokenStore
from .tooling import (
    build_strict_response_format,
    callable_to_tool_schema,
    normalize_tool_inputs,
    normalize_tool_output,
    to_responses_tools,
    tool_results_to_response_items,
)

DEFAULT_MODEL = "gpt-5.3-codex"
DEFAULT_MAX_TOOL_ROUNDS = 16
StructuredOutputSchema = type[BaseModel] | dict[str, Any]
StreamEventType = Literal[
    "response_started",
    "text_delta",
    "reasoning_delta",
    "reasoning_done",
    "tool_call_started",
    "tool_call_arguments_delta",
    "tool_call_done",
    "usage",
    "response_completed",
    "done",
    "error",
]


def _method_is_overridden(
    instance: object, owner: type[object], method_name: str
) -> bool:
    method = getattr(instance, method_name, None)
    original = getattr(owner, method_name, None)
    if method is None or original is None:
        return False
    return getattr(method, "__func__", method) is not original


def _omit_none(values: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in values.items() if v is not None}


def _namespace_to_dict(value: Any) -> Any:
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return value.model_dump()
    if isinstance(value, dict):
        return {k: _namespace_to_dict(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_namespace_to_dict(v) for v in value]
    if hasattr(value, "__dict__"):
        return {k: _namespace_to_dict(v) for k, v in vars(value).items()}
    return value


def _serialize_tool_arguments(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value if value is not None else {}, ensure_ascii=True)
    except TypeError:
        return "{}"


class _ResponsesInputTokensAdapter:
    def __init__(self, engine: _EngineClient) -> None:
        self._engine = engine

    def count(
        self,
        *,
        model: str,
        input: str | dict[str, Any] | list[dict[str, Any]],
        tools: list[Any] | None = None,
    ) -> Any:
        return self._engine.responses_input_tokens_count(
            model=model, input=input, tools=tools
        )


class _ResponsesAdapter:
    def __init__(
        self,
        *,
        sync_client: _CodexClient,
        async_client: _CodexAsyncClient,
        engine: _EngineClient,
    ) -> None:
        self._sync_client = sync_client
        self._async_client = async_client
        self._engine = engine
        self.input_tokens = _ResponsesInputTokensAdapter(engine)

    def create(self, **kwargs: Any) -> Any:
        if _method_is_overridden(self._engine, _EngineClient, "responses_create"):
            return self._engine.responses_create(**kwargs)
        payload = self._prepare_payload(kwargs)
        return self._sync_client.responses.create(**payload)

    async def acreate(self, **kwargs: Any) -> Any:
        if _method_is_overridden(self._engine, _EngineClient, "aresponses_create"):
            return await self._engine.aresponses_create(**kwargs)
        payload = self._prepare_payload(kwargs)
        return await self._async_client.responses.create(**payload)

    def _prepare_payload(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        payload = dict(kwargs)
        messages = payload.pop("messages", None)
        input_items = payload.pop("input", None)
        tool_results = payload.pop("tool_results", None)
        tools = payload.pop("tools", None)
        strict_output = bool(payload.get("strict_output"))

        normalized_input = self._normalize_input(
            input_items if input_items is not None else messages
        )
        continuation_items = tool_results_to_response_items(tool_results)
        if continuation_items:
            normalized_input = [*normalized_input, *continuation_items]

        if normalized_input:
            payload["input"] = normalized_input

        if tools is not None:
            payload["tools"] = to_responses_tools(
                normalize_tool_inputs(tools),
                strict_output=strict_output,
            )

        return _omit_none(payload)

    def _normalize_input(self, value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []
        if isinstance(value, str):
            return [{"role": "user", "content": value}]
        if isinstance(value, dict):
            return [dict(value)]
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]
        raise TypeError("`messages` must be a non-empty list")


class OAuthCodexClient(SyncAPIClient):
    """Public single-entry client for oauth-codex.

    This client wraps the OAuth-backed responses engine and exposes a
    generate-first workflow:

    - `generate` and `agenerate` return final text, or a validated JSON object
      when `output_schema` is provided.
    - `stream` and `astream` yield text deltas while still supporting
      automatic tool-call continuation rounds.

    Public attributes:
        default_model: Model used when `model` is omitted. Defaults to
            `"gpt-5.3-codex"`.
        max_tool_rounds: Maximum number of automatic tool continuation rounds
            before raising `RuntimeError`.
        responses/files/models/vector_stores: Resource-style namespaces that mirror the
            internal engine resources for lower-level API access.

    Example:
        from oauth_codex import Client

        client = Client(authenticate_on_init=True)
        text = client.generate([{"role": "user", "content": "hello"}])
    """

    def __init__(
        self,
        *,
        oauth_config: OAuthConfig | None = None,
        token_store: Any | None = None,
        base_url: str | None = None,
        chatgpt_base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        compat_storage_dir: str | None = None,
        on_request_start: Any | None = None,
        on_request_end: Any | None = None,
        on_auth_refresh: Any | None = None,
        on_error: Any | None = None,
        authenticate_on_init: bool = False,
    ) -> None:
        """Create a `Client` instance.

        Args:
            oauth_config: Optional OAuth endpoint/client configuration.
            token_store: Token persistence backend. If omitted, a fallback
                keyring/file store is used.
            base_url: Base URL for Codex backend requests.
            chatgpt_base_url: Legacy alias for `base_url`. `base_url` takes
                precedence when both are provided.
            timeout: Request timeout in seconds.
            max_retries: Number of retry attempts for retryable failures.
            compat_storage_dir: Optional local compatibility storage path.
            on_request_start: Optional callback invoked when a request starts.
            on_request_end: Optional callback invoked when a request ends.
            on_auth_refresh: Optional callback invoked after token refresh.
            on_error: Optional callback invoked when request/auth errors occur.
            authenticate_on_init: When `True`, perform authentication during
                client construction. If no stored token exists, interactive
                login is started immediately.
        """
        super().__init__()

        resolved_base_url = (
            base_url or chatgpt_base_url or "https://chatgpt.com/backend-api/codex"
        ).rstrip("/")

        self._engine = _EngineClient(
            oauth_config=oauth_config,
            token_store=token_store or FallbackTokenStore(),
            chatgpt_base_url=resolved_base_url,
            timeout=timeout,
            validation_mode="warn",
            store_behavior="auto_disable",
            max_retries=max_retries,
            compat_storage_dir=compat_storage_dir,
            on_request_start=on_request_start,
            on_request_end=on_request_end,
            on_auth_refresh=on_auth_refresh,
            on_error=on_error,
        )

        self._codex_client = _CodexClient(
            token_store=token_store,
            oauth_config=oauth_config,
            base_url=resolved_base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._codex_async_client = _CodexAsyncClient(
            token_store=token_store,
            oauth_config=oauth_config,
            base_url=resolved_base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        self._responses_adapter = _ResponsesAdapter(
            sync_client=self._codex_client,
            async_client=self._codex_async_client,
            engine=self._engine,
        )
        self.responses = self._engine.responses
        setattr(self.responses, "create", self._responses_adapter.create)
        setattr(self.responses, "acreate", self._responses_adapter.acreate)
        self.files = self._engine.files
        self.vector_stores = self._engine.vector_stores
        self.models = self._engine.models
        self.chat = self._codex_client.chat

        self.default_model = DEFAULT_MODEL
        self.max_tool_rounds = DEFAULT_MAX_TOOL_ROUNDS

        if authenticate_on_init:
            self.authenticate()

    def is_authenticated(self) -> bool:
        """Return whether usable OAuth tokens are currently available.

        Returns:
            `True` when a token is available, otherwise `False`.
        """
        return self._engine.is_authenticated()

    def is_expired(self, *, leeway_seconds: int = 60) -> bool:
        """Return whether the current token is expired or near expiry.

        Args:
            leeway_seconds: Safety margin in seconds added before expiry check.

        Returns:
            `True` if the token is expired within the given leeway.
        """
        return self._engine.is_expired(leeway_seconds=leeway_seconds)

    def refresh_if_needed(self, *, force: bool = False) -> bool:
        """Refresh tokens when needed.

        Args:
            force: Refresh even when token is not currently expired.

        Returns:
            `True` if refresh happened and succeeded, otherwise `False`.
        """
        return self._engine.refresh_if_needed(force=force)

    async def arefresh_if_needed(self, *, force: bool = False) -> bool:
        """Async version of `refresh_if_needed`.

        Args:
            force: Refresh even when token is not currently expired.

        Returns:
            `True` if refresh happened and succeeded, otherwise `False`.
        """
        return await self._engine.arefresh_if_needed(force=force)

    def authenticate(self) -> None:
        """Ensure usable OAuth credentials are available now.

        This loads stored credentials, starts interactive login when missing,
        and refreshes tokens when expired.
        """
        self._engine._ensure_authenticated_sync()

    def login(self) -> None:
        """Run interactive OAuth login flow in the current thread.

        Raises:
            OAuthCallbackParseError: If callback URL parsing fails.
            OAuthStateMismatchError: If OAuth state verification fails.
            TokenExchangeError: If code-to-token exchange fails.
        """
        self._engine.login()

    async def alogin(self) -> None:
        """Run interactive OAuth login flow without blocking the event loop.

        Raises:
            OAuthCallbackParseError: If callback URL parsing fails.
            OAuthStateMismatchError: If OAuth state verification fails.
            TokenExchangeError: If code-to-token exchange fails.
        """
        await asyncio.to_thread(self._engine.login)

    def generate(
        self,
        messages: listMessage | None = None,
        *,
        tools: list[Callable[..., Any]] | None = None,
        model: str | None = None,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        output_schema: StructuredOutputSchema | None = None,
        strict_output: bool | None = None,
    ) -> str | dict[str, Any]:
        """Generate a final response with automatic tool execution.

        Args:
            messages: Non-empty list of response input messages.
            tools: Optional list of Python callables used for automatic
                function-calling rounds.
            model: Optional model override. Uses `default_model` when omitted.
            reasoning_effort: Reasoning intensity (`"low"`, `"medium"`,
                `"high"`).
            temperature: Sampling temperature.
            top_p: Nucleus sampling probability.
            max_output_tokens: Maximum generated output tokens.
            output_schema: Optional structured-output schema. Accepts a
                Pydantic model type or JSON schema dict.
            strict_output: Strict schema mode. When `output_schema` is set and
                `strict_output` is omitted, strict mode is enabled by default.

        Returns:
            Final text output, or a validated JSON object when `output_schema`
            is provided.

        Raises:
            ValueError: If `messages` is missing/empty, or structured output is
                not valid JSON.
            TypeError: If `messages` is not a list, `tools` are invalid, or
                structured output is not a JSON object.
            RuntimeError: If automatic tool execution exceeds
                `max_tool_rounds`.
            pydantic.ValidationError: If a Pydantic `output_schema` fails
                strict validation.
        """
        messages = self._normalize_initial_messages(messages)
        normalized_tools, tools_by_name = self._normalize_tools(tools)
        response_format, effective_strict_output = (
            self._resolve_structured_output_options(
                output_schema=output_schema,
                strict_output=strict_output,
            )
        )

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None
        output_parts: list[str] = []

        for _ in range(self.max_tool_rounds):
            result = self._create_round_result_sync(
                model=self._resolve_model(model),
                messages=self._messages_for_round(
                    messages=messages,
                    previous_response_id=previous_response_id,
                    tool_results=tool_results,
                ),
                tools=normalized_tools,
                tool_results=tool_results,
                response_format=response_format,
                strict_output=effective_strict_output,
                reasoning={"effort": reasoning_effort},
                previous_response_id=previous_response_id,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_output_tokens,
            )

            if result.text:
                output_parts.append(result.text)

            if not result.tool_calls:
                text = "".join(output_parts)
                if output_schema is None:
                    return text
                return self._parse_structured_output_text(
                    text=text, output_schema=output_schema
                )

            tool_results = self._execute_tool_calls_sync(
                result.tool_calls, tools_by_name
            )
            previous_response_id = result.response_id

        raise RuntimeError(
            f"automatic tool execution exceeded {self.max_tool_rounds} rounds"
        )

    async def agenerate(
        self,
        messages: listMessage | None = None,
        *,
        tools: list[Callable[..., Any]] | None = None,
        model: str | None = None,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        output_schema: StructuredOutputSchema | None = None,
        strict_output: bool | None = None,
    ) -> str | dict[str, Any]:
        """Async response generation with automatic tool execution.

        Args:
            messages: Non-empty list of response input messages.
            tools: Optional list of Python callables used for automatic
                function-calling rounds.
            model: Optional model override. Uses `default_model` when omitted.
            reasoning_effort: Reasoning intensity (`"low"`, `"medium"`,
                `"high"`).
            temperature: Sampling temperature.
            top_p: Nucleus sampling probability.
            max_output_tokens: Maximum generated output tokens.
            output_schema: Optional structured-output schema. Accepts a
                Pydantic model type or JSON schema dict.
            strict_output: Strict schema mode. When `output_schema` is set and
                `strict_output` is omitted, strict mode is enabled by default.

        Returns:
            Final text output, or a validated JSON object when `output_schema`
            is provided.

        Raises:
            ValueError: If `messages` is missing/empty, or structured output is
                not valid JSON.
            TypeError: If `messages` is not a list, `tools` are invalid, or
                structured output is not a JSON object.
            RuntimeError: If automatic tool execution exceeds
                `max_tool_rounds`.
            pydantic.ValidationError: If a Pydantic `output_schema` fails
                strict validation.
        """
        messages = self._normalize_initial_messages(messages)
        normalized_tools, tools_by_name = self._normalize_tools(tools)
        response_format, effective_strict_output = (
            self._resolve_structured_output_options(
                output_schema=output_schema,
                strict_output=strict_output,
            )
        )

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None
        output_parts: list[str] = []

        for _ in range(self.max_tool_rounds):
            result = await self._create_round_result_async(
                model=self._resolve_model(model),
                messages=self._messages_for_round(
                    messages=messages,
                    previous_response_id=previous_response_id,
                    tool_results=tool_results,
                ),
                tools=normalized_tools,
                tool_results=tool_results,
                response_format=response_format,
                strict_output=effective_strict_output,
                reasoning={"effort": reasoning_effort},
                previous_response_id=previous_response_id,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_output_tokens,
            )

            if result.text:
                output_parts.append(result.text)

            if not result.tool_calls:
                text = "".join(output_parts)
                if output_schema is None:
                    return text
                return self._parse_structured_output_text(
                    text=text, output_schema=output_schema
                )

            tool_results = await self._execute_tool_calls_async(
                result.tool_calls, tools_by_name
            )
            previous_response_id = result.response_id

        raise RuntimeError(
            f"automatic tool execution exceeded {self.max_tool_rounds} rounds"
        )

    def stream(
        self,
        messages: listMessage | None = None,
        *,
        tools: list[Callable[..., Any]] | None = None,
        model: str | None = None,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        output_schema: StructuredOutputSchema | None = None,
        strict_output: bool | None = None,
    ) -> Iterator[str]:
        """Stream text deltas with automatic tool execution rounds.

        Args:
            messages: Non-empty list of response input messages.
            tools: Optional list of Python callables used for automatic
                function-calling rounds.
            model: Optional model override. Uses `default_model` when omitted.
            reasoning_effort: Reasoning intensity (`"low"`, `"medium"`,
                `"high"`).
            temperature: Sampling temperature.
            top_p: Nucleus sampling probability.
            max_output_tokens: Maximum generated output tokens.
            output_schema: Optional structured-output schema forwarded to the
                backend. Stream output is still text deltas only.
            strict_output: Strict schema mode. When `output_schema` is set and
                `strict_output` is omitted, strict mode is enabled by default.

        Yields:
            Text delta chunks as they arrive.

        Raises:
            ValueError: If `messages` is missing/empty.
            TypeError: If `messages` is not a list or `tools` are invalid.
            RuntimeError: If automatic tool execution exceeds
                `max_tool_rounds`.
        """
        messages = self._normalize_initial_messages(messages)
        normalized_tools, tools_by_name = self._normalize_tools(tools)
        response_format, effective_strict_output = (
            self._resolve_structured_output_options(
                output_schema=output_schema,
                strict_output=strict_output,
            )
        )

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None

        for _ in range(self.max_tool_rounds):
            tool_calls: list[ToolCall] = []
            round_response_id: str | None = previous_response_id
            events: Iterator[StreamEvent] = self._create_round_stream_sync(
                model=self._resolve_model(model),
                messages=self._messages_for_round(
                    messages=messages,
                    previous_response_id=previous_response_id,
                    tool_results=tool_results,
                ),
                tools=normalized_tools,
                tool_results=tool_results,
                response_format=response_format,
                strict_output=effective_strict_output,
                reasoning={"effort": reasoning_effort},
                previous_response_id=previous_response_id,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_output_tokens,
            )
            for event in events:
                if event.type == "text_delta" and isinstance(event.delta, str):
                    yield event.delta
                if event.type == "tool_call_done" and event.tool_call is not None:
                    tool_calls.append(event.tool_call)
                if event.response_id:
                    round_response_id = event.response_id

            if not tool_calls:
                return

            tool_results = self._execute_tool_calls_sync(tool_calls, tools_by_name)
            previous_response_id = round_response_id

        raise RuntimeError(
            f"automatic tool execution exceeded {self.max_tool_rounds} rounds"
        )

    async def astream(
        self,
        messages: listMessage | None = None,
        *,
        tools: list[Callable[..., Any]] | None = None,
        model: str | None = None,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        output_schema: StructuredOutputSchema | None = None,
        strict_output: bool | None = None,
    ) -> AsyncIterator[str]:
        """Async stream of text deltas with automatic tool execution rounds.

        Args:
            messages: Non-empty list of response input messages.
            tools: Optional list of Python callables used for automatic
                function-calling rounds.
            model: Optional model override. Uses `default_model` when omitted.
            reasoning_effort: Reasoning intensity (`"low"`, `"medium"`,
                `"high"`).
            temperature: Sampling temperature.
            top_p: Nucleus sampling probability.
            max_output_tokens: Maximum generated output tokens.
            output_schema: Optional structured-output schema forwarded to the
                backend. Stream output is still text deltas only.
            strict_output: Strict schema mode. When `output_schema` is set and
                `strict_output` is omitted, strict mode is enabled by default.

        Yields:
            Text delta chunks as they arrive.

        Raises:
            ValueError: If `messages` is missing/empty.
            TypeError: If `messages` is not a list or `tools` are invalid.
            RuntimeError: If automatic tool execution exceeds
                `max_tool_rounds`.
        """
        messages = self._normalize_initial_messages(messages)
        normalized_tools, tools_by_name = self._normalize_tools(tools)
        response_format, effective_strict_output = (
            self._resolve_structured_output_options(
                output_schema=output_schema,
                strict_output=strict_output,
            )
        )

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None

        for _ in range(self.max_tool_rounds):
            tool_calls: list[ToolCall] = []
            round_response_id: str | None = previous_response_id
            events = await self._create_round_stream_async(
                model=self._resolve_model(model),
                messages=self._messages_for_round(
                    messages=messages,
                    previous_response_id=previous_response_id,
                    tool_results=tool_results,
                ),
                tools=normalized_tools,
                tool_results=tool_results,
                response_format=response_format,
                strict_output=effective_strict_output,
                reasoning={"effort": reasoning_effort},
                previous_response_id=previous_response_id,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_output_tokens,
            )
            async for event in events:
                if event.type == "text_delta" and isinstance(event.delta, str):
                    yield event.delta
                if event.type == "tool_call_done" and event.tool_call is not None:
                    tool_calls.append(event.tool_call)
                if event.response_id:
                    round_response_id = event.response_id

            if not tool_calls:
                return

            tool_results = await self._execute_tool_calls_async(
                tool_calls, tools_by_name
            )
            previous_response_id = round_response_id

        raise RuntimeError(
            f"automatic tool execution exceeded {self.max_tool_rounds} rounds"
        )

    def _create_round_result_sync(self, **kwargs: Any) -> GenerateResult:
        if _method_is_overridden(self._engine, _EngineClient, "generate"):
            response = self._engine.generate(return_details=True, **kwargs)
        else:
            response = self.responses.create(**kwargs)
        return self._coerce_generate_result(response)

    async def _create_round_result_async(self, **kwargs: Any) -> GenerateResult:
        if _method_is_overridden(self._engine, _EngineClient, "agenerate"):
            response = await self._engine.agenerate(return_details=True, **kwargs)
        else:
            response = await self._responses_adapter.acreate(**kwargs)
        return self._coerce_generate_result(response)

    def _create_round_stream_sync(self, **kwargs: Any) -> Iterator[StreamEvent]:
        if _method_is_overridden(self._engine, _EngineClient, "generate_stream"):
            events = self._engine.generate_stream(raw_events=True, **kwargs)
            return self._iter_sync_events(events)
        events = self.responses.create(stream=True, **kwargs)
        return self._iter_sync_events(events)

    async def _create_round_stream_async(
        self, **kwargs: Any
    ) -> AsyncIterator[StreamEvent]:
        if _method_is_overridden(self._engine, _EngineClient, "agenerate_stream"):
            events = await self._engine.agenerate_stream(raw_events=True, **kwargs)
            return self._iter_async_events(events)
        events = await self._responses_adapter.acreate(stream=True, **kwargs)
        return self._iter_async_events(events)

    def _iter_sync_events(self, value: Any) -> Iterator[StreamEvent]:
        def _iterator() -> Iterator[StreamEvent]:
            if isinstance(value, Iterator):
                for item in value:
                    event = self._coerce_stream_event(item)
                    if event is not None:
                        yield event
                return
            raw = _namespace_to_dict(value)
            if isinstance(raw, list):
                for item in raw:
                    event = self._coerce_stream_event(item)
                    if event is not None:
                        yield event
                return

            event = self._coerce_stream_event(raw)
            if event is not None:
                yield event
            yield StreamEvent(type="done", response_id=self._extract_response_id(raw))

        return _iterator()

    def _iter_async_events(self, value: Any) -> AsyncIterator[StreamEvent]:
        async def _aiterator() -> AsyncIterator[StreamEvent]:
            if hasattr(value, "__aiter__"):
                async for item in value:
                    event = self._coerce_stream_event(item)
                    if event is not None:
                        yield event
                return

            raw = _namespace_to_dict(value)
            if isinstance(raw, list):
                for item in raw:
                    event = self._coerce_stream_event(item)
                    if event is not None:
                        yield event
                return

            event = self._coerce_stream_event(raw)
            if event is not None:
                yield event
            yield StreamEvent(type="done", response_id=self._extract_response_id(raw))

        return _aiterator()

    def _coerce_stream_event(self, event: Any) -> StreamEvent | None:
        if isinstance(event, StreamEvent):
            return event

        payload = _namespace_to_dict(event)
        if not isinstance(payload, dict):
            return None

        event_type = payload.get("type")
        if not isinstance(event_type, str):
            return None
        if event_type not in {
            "response_started",
            "text_delta",
            "reasoning_delta",
            "reasoning_done",
            "tool_call_started",
            "tool_call_arguments_delta",
            "tool_call_done",
            "usage",
            "response_completed",
            "done",
            "error",
        }:
            return None

        delta = payload.get("delta")
        if not isinstance(delta, str):
            delta = (
                payload.get("text") if isinstance(payload.get("text"), str) else None
            )

        tool_call = self._coerce_tool_call(
            payload.get("tool_call") or payload.get("call")
        )

        return StreamEvent(
            type=cast(StreamEventType, event_type),
            delta=delta,
            tool_call=tool_call,
            raw=payload,
            error=payload.get("error")
            if isinstance(payload.get("error"), str)
            else None,
            call_id=payload.get("call_id")
            if isinstance(payload.get("call_id"), str)
            else None,
            response_id=self._extract_response_id(payload),
            finish_reason=payload.get("finish_reason")
            if isinstance(payload.get("finish_reason"), str)
            else None,
        )

    def _coerce_generate_result(self, response: Any) -> GenerateResult:
        if isinstance(response, GenerateResult):
            return response

        payload = _namespace_to_dict(response)
        if not isinstance(payload, dict):
            raise TypeError("internal error: expected GenerateResult")

        text = self._extract_output_text(payload)
        tool_calls = self._extract_tool_calls(payload)
        finish_reason = payload.get("finish_reason")
        if finish_reason not in {"stop", "tool_calls", "length", "error"}:
            finish_reason = "tool_calls" if tool_calls else "stop"

        return GenerateResult(
            text=text,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=self._extract_usage(payload),
            raw_response=payload,
            response_id=self._extract_response_id(payload),
        )

    def _extract_usage(self, payload: dict[str, Any]) -> TokenUsage | None:
        raw_usage = payload.get("usage")
        if not isinstance(raw_usage, dict):
            return None
        return TokenUsage(
            input_tokens=raw_usage.get("input_tokens")
            if isinstance(raw_usage.get("input_tokens"), int)
            else None,
            output_tokens=raw_usage.get("output_tokens")
            if isinstance(raw_usage.get("output_tokens"), int)
            else None,
            total_tokens=raw_usage.get("total_tokens")
            if isinstance(raw_usage.get("total_tokens"), int)
            else None,
            cached_tokens=raw_usage.get("cached_tokens")
            if isinstance(raw_usage.get("cached_tokens"), int)
            else None,
            reasoning_tokens=raw_usage.get("reasoning_tokens")
            if isinstance(raw_usage.get("reasoning_tokens"), int)
            else None,
        )

    def _extract_response_id(self, payload: Any) -> str | None:
        if isinstance(payload, dict):
            response_id = payload.get("response_id")
            if isinstance(response_id, str) and response_id:
                return response_id
            response_id = payload.get("id")
            if isinstance(response_id, str) and response_id:
                return response_id
            nested = payload.get("response")
            if isinstance(nested, dict):
                nested_id = nested.get("id")
                if isinstance(nested_id, str) and nested_id:
                    return nested_id
        return None

    def _extract_output_text(self, payload: dict[str, Any]) -> str:
        output_text = payload.get("output_text")
        if isinstance(output_text, str):
            return output_text

        if isinstance(output_text, list):
            parts: list[str] = []
            for item in output_text:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            if parts:
                return "".join(parts)

        text_parts: list[str] = []
        output = payload.get("output")
        if not isinstance(output, list):
            return ""

        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "output_text" and isinstance(item.get("text"), str):
                text_parts.append(item["text"])
                continue
            if item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") in {"output_text", "text"} and isinstance(
                    part.get("text"), str
                ):
                    text_parts.append(part["text"])

        return "".join(text_parts)

    def _extract_tool_calls(self, payload: dict[str, Any]) -> list[ToolCall]:
        out: list[ToolCall] = []

        tool_calls = payload.get("tool_calls")
        if isinstance(tool_calls, list):
            for call in tool_calls:
                coerced = self._coerce_tool_call(call)
                if coerced is not None:
                    out.append(coerced)
            if out:
                return out

        output = payload.get("output")
        if not isinstance(output, list):
            return out
        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") not in {"function_call", "tool_call"}:
                continue
            coerced = self._coerce_tool_call(item)
            if coerced is not None:
                out.append(coerced)
        return out

    def _coerce_tool_call(self, value: Any) -> ToolCall | None:
        payload = _namespace_to_dict(value)
        if not isinstance(payload, dict):
            return None

        call_id = payload.get("id")
        if not isinstance(call_id, str) or not call_id:
            call_id = payload.get("call_id")
        if not isinstance(call_id, str) or not call_id:
            return None

        name = payload.get("name")
        if not isinstance(name, str) or not name:
            return None

        arguments = payload.get("arguments_json")
        if not isinstance(arguments, str):
            arguments = _serialize_tool_arguments(payload.get("arguments"))

        parsed_args: dict[str, Any] | None = None
        try:
            maybe_parsed = json.loads(arguments)
            if isinstance(maybe_parsed, dict):
                parsed_args = maybe_parsed
        except json.JSONDecodeError:
            parsed_args = None

        return ToolCall(
            id=call_id, name=name, arguments_json=arguments, arguments=parsed_args
        )

    def _resolve_model(self, model: str | None) -> str:
        return model or self.default_model

    def _resolve_structured_output_options(
        self,
        *,
        output_schema: StructuredOutputSchema | None,
        strict_output: bool | None,
    ) -> tuple[dict[str, Any] | None, bool]:
        effective_strict_output = (
            strict_output if strict_output is not None else bool(output_schema)
        )
        if output_schema is None:
            return None, effective_strict_output
        return build_strict_response_format(output_schema), effective_strict_output

    def _parse_structured_output_text(
        self,
        *,
        text: str,
        output_schema: StructuredOutputSchema,
    ) -> dict[str, Any]:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("structured output is not valid JSON") from exc

        if not isinstance(parsed, dict):
            raise TypeError("structured output must be a JSON object")

        model_type = self._resolve_pydantic_model_type(output_schema)
        if model_type is None:
            return parsed
        validated = model_type.model_validate(parsed, strict=True)
        return validated.model_dump(mode="json")

    def _is_tool_continuation_round(
        self,
        *,
        previous_response_id: str | None,
        tool_results: list[ToolResult] | None,
    ) -> bool:
        return bool(previous_response_id) and bool(tool_results)

    def _messages_for_round(
        self,
        *,
        messages: listMessage,
        previous_response_id: str | None,
        tool_results: list[ToolResult] | None,
    ) -> listMessage:
        if self._is_tool_continuation_round(
            previous_response_id=previous_response_id,
            tool_results=tool_results,
        ):
            return []
        return messages

    def _normalize_initial_messages(self, messages: listMessage | None) -> listMessage:
        if messages is None:
            raise ValueError("`messages` must be a non-empty list")
        if not isinstance(messages, list):
            raise TypeError("`messages` must be a non-empty list")
        if not messages:
            raise ValueError("`messages` must be a non-empty list")
        return messages

    def _normalize_tools(
        self,
        tools: list[Callable[..., Any]] | None,
    ) -> tuple[list[Any], dict[str, Callable[..., Any]]]:
        if tools is None:
            return [], {}
        if not isinstance(tools, list):
            raise TypeError("tools must be a list of callables")

        schemas: list[Any] = []
        tools_by_name: dict[str, Callable[..., Any]] = {}
        for tool in tools:
            if not callable(tool):
                raise TypeError("tools must contain only callables")
            schema = callable_to_tool_schema(tool)
            name = str(schema.get("name") or getattr(tool, "__name__", "tool"))
            if name in tools_by_name:
                raise ValueError(f"duplicate tool name: {name}")
            schemas.append(schema)
            tools_by_name[name] = tool
        return schemas, tools_by_name

    def _execute_tool_calls_sync(
        self,
        tool_calls: list[ToolCall],
        tools_by_name: dict[str, Callable[..., Any]],
    ) -> list[ToolResult]:
        results: list[ToolResult] = []
        for call in tool_calls:
            output: dict[str, Any]
            tool = tools_by_name.get(call.name)
            if tool is None:
                output = {"error": f"tool not found: {call.name}"}
            else:
                try:
                    kwargs = self._parse_tool_kwargs(call.arguments_json)
                    normalized_kwargs = self._normalize_tool_kwargs(tool, kwargs)
                    value = tool(**normalized_kwargs)
                    if inspect.isawaitable(value):
                        raise TypeError(
                            "async tool is not supported in generate(); use agenerate()"
                        )
                    output = self._normalize_tool_output(value)
                except Exception as exc:
                    output = {"error": str(exc) or exc.__class__.__name__}
            results.append(
                ToolResult(tool_call_id=call.id, name=call.name, output=output)
            )
        return results

    async def _execute_tool_calls_async(
        self,
        tool_calls: list[ToolCall],
        tools_by_name: dict[str, Callable[..., Any]],
    ) -> list[ToolResult]:
        results: list[ToolResult] = []
        for call in tool_calls:
            output: dict[str, Any]
            tool = tools_by_name.get(call.name)
            if tool is None:
                output = {"error": f"tool not found: {call.name}"}
            else:
                try:
                    kwargs = self._parse_tool_kwargs(call.arguments_json)
                    normalized_kwargs = self._normalize_tool_kwargs(tool, kwargs)
                    value = tool(**normalized_kwargs)
                    if inspect.isawaitable(value):
                        value = await value
                    output = self._normalize_tool_output(value)
                except Exception as exc:
                    output = {"error": str(exc) or exc.__class__.__name__}
            results.append(
                ToolResult(tool_call_id=call.id, name=call.name, output=output)
            )
        return results

    def _parse_tool_kwargs(self, arguments_json: str) -> dict[str, Any]:
        if not arguments_json:
            return {}
        parsed = json.loads(arguments_json)
        if not isinstance(parsed, dict):
            raise TypeError("tool arguments must be a JSON object")
        return parsed

    def _normalize_tool_kwargs(
        self,
        tool: Callable[..., Any],
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        signature = inspect.signature(tool)
        resolved_hints = self._resolve_tool_type_hints(tool)
        params = [
            param
            for param in signature.parameters.values()
            if param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
        ]
        if not params:
            return kwargs

        if len(params) == 1:
            param = params[0]
            model_type = self._resolve_pydantic_model_type(
                resolved_hints.get(param.name, param.annotation)
            )
            if model_type is not None:
                if param.name in kwargs:
                    payload = kwargs[param.name]
                    if isinstance(payload, model_type):
                        return kwargs
                    if not isinstance(payload, dict):
                        raise TypeError(
                            f"tool argument `{param.name}` must be a JSON object"
                        )
                    normalized = dict(kwargs)
                    normalized[param.name] = model_type.model_validate(payload)
                    return normalized

                if not kwargs and param.default is not inspect._empty:
                    return kwargs

                payload = kwargs
                normalized_payload = (
                    payload
                    if isinstance(payload, model_type)
                    else model_type.model_validate(payload)
                )
                return {param.name: normalized_payload}

        normalized = dict(kwargs)
        for param in params:
            model_type = self._resolve_pydantic_model_type(
                resolved_hints.get(param.name, param.annotation)
            )
            if model_type is None or param.name not in normalized:
                continue
            payload = normalized[param.name]
            if isinstance(payload, model_type):
                continue
            if not isinstance(payload, dict):
                raise TypeError(f"tool argument `{param.name}` must be a JSON object")
            normalized[param.name] = model_type.model_validate(payload)
        return normalized

    def _resolve_pydantic_model_type(self, annotation: Any) -> type[BaseModel] | None:
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return annotation
        return None

    def _resolve_tool_type_hints(self, tool: Callable[..., Any]) -> dict[str, Any]:
        try:
            return get_type_hints(tool)
        except Exception:
            return {}

    def _normalize_tool_output(self, output: Any) -> dict[str, Any]:
        return normalize_tool_output(output)


class AsyncOAuthCodexClient(AsyncAPIClient):
    """Public single-entry async client for oauth-codex.

    This client wraps the OAuth-backed responses engine and exposes a
    generate-first workflow:

    - `generate` returns final text, or a validated JSON object
      when `output_schema` is provided.
    - `stream` yields text deltas while still supporting
      automatic tool-call continuation rounds.
    """

    def __init__(
        self,
        *,
        oauth_config: OAuthConfig | None = None,
        token_store: Any | None = None,
        base_url: str | None = None,
        chatgpt_base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        compat_storage_dir: str | None = None,
        on_request_start: Any | None = None,
        on_request_end: Any | None = None,
        on_auth_refresh: Any | None = None,
        on_error: Any | None = None,
        authenticate_on_init: bool = False,
    ) -> None:
        super().__init__()

        resolved_base_url = (
            base_url or chatgpt_base_url or "https://chatgpt.com/backend-api/codex"
        ).rstrip("/")

        self._engine = _EngineClient(
            oauth_config=oauth_config,
            token_store=token_store or FallbackTokenStore(),
            chatgpt_base_url=resolved_base_url,
            timeout=timeout,
            validation_mode="warn",
            store_behavior="auto_disable",
            max_retries=max_retries,
            compat_storage_dir=compat_storage_dir,
            on_request_start=on_request_start,
            on_request_end=on_request_end,
            on_auth_refresh=on_auth_refresh,
            on_error=on_error,
        )

        self._codex_client = _CodexClient(
            token_store=token_store,
            oauth_config=oauth_config,
            base_url=resolved_base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._codex_async_client = _CodexAsyncClient(
            token_store=token_store,
            oauth_config=oauth_config,
            base_url=resolved_base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._responses_adapter = _ResponsesAdapter(
            sync_client=self._codex_client,
            async_client=self._codex_async_client,
            engine=self._engine,
        )
        self.responses = self._codex_async_client.responses
        setattr(self.responses, "create", self._responses_adapter.acreate)
        self.files = self._codex_async_client.files
        self.vector_stores = self._codex_async_client.vector_stores
        self.models = self._codex_async_client.models
        self.chat = self._codex_async_client.chat

        self.default_model = DEFAULT_MODEL
        self.max_tool_rounds = DEFAULT_MAX_TOOL_ROUNDS

        if authenticate_on_init:
            # We can't easily do async auth in __init__, but we can start it.
            # For now, we'll just rely on the user calling authenticate() or it happening on first request.
            pass

    async def is_authenticated(self) -> bool:
        return await self._engine.ais_authenticated()

    async def is_expired(self, *, leeway_seconds: int = 60) -> bool:
        return await self._engine.ais_expired(leeway_seconds=leeway_seconds)

    async def refresh_if_needed(self, *, force: bool = False) -> bool:
        return await self._engine.arefresh_if_needed(force=force)

    async def authenticate(self) -> None:
        await self._engine._ensure_authenticated_async()

    async def login(self) -> None:
        await asyncio.to_thread(self._engine.login)

    async def generate(
        self,
        messages: listMessage | None = None,
        *,
        tools: list[Callable[..., Any]] | None = None,
        model: str | None = None,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        output_schema: StructuredOutputSchema | None = None,
        strict_output: bool | None = None,
    ) -> str | dict[str, Any]:
        # Implementation copied from agenerate and renamed to generate
        messages = self._normalize_initial_messages(messages)
        normalized_tools, tools_by_name = self._normalize_tools(tools)
        response_format, effective_strict_output = (
            self._resolve_structured_output_options(
                output_schema=output_schema,
                strict_output=strict_output,
            )
        )

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None
        output_parts: list[str] = []

        for _ in range(self.max_tool_rounds):
            result = await self._create_round_result_async(
                model=self._resolve_model(model),
                messages=self._messages_for_round(
                    messages=messages,
                    previous_response_id=previous_response_id,
                    tool_results=tool_results,
                ),
                tools=normalized_tools,
                tool_results=tool_results,
                response_format=response_format,
                strict_output=effective_strict_output,
                reasoning={"effort": reasoning_effort},
                previous_response_id=previous_response_id,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_output_tokens,
            )

            if result.text:
                output_parts.append(result.text)

            if not result.tool_calls:
                text = "".join(output_parts)
                if output_schema is None:
                    return text
                return self._parse_structured_output_text(
                    text=text, output_schema=output_schema
                )

            tool_results = await self._execute_tool_calls_async(
                result.tool_calls, tools_by_name
            )
            previous_response_id = result.response_id

        raise RuntimeError(
            f"automatic tool execution exceeded {self.max_tool_rounds} rounds"
        )

    async def stream(
        self,
        messages: listMessage | None = None,
        *,
        tools: list[Callable[..., Any]] | None = None,
        model: str | None = None,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
        output_schema: StructuredOutputSchema | None = None,
        strict_output: bool | None = None,
    ) -> AsyncIterator[str]:
        # Implementation copied from astream and renamed to stream
        messages = self._normalize_initial_messages(messages)
        normalized_tools, tools_by_name = self._normalize_tools(tools)
        response_format, effective_strict_output = (
            self._resolve_structured_output_options(
                output_schema=output_schema,
                strict_output=strict_output,
            )
        )

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None
        for _ in range(self.max_tool_rounds):
            tool_calls: list[ToolCall] = []
            round_response_id: str | None = previous_response_id
            events = await self._create_round_stream_async(
                model=self._resolve_model(model),
                messages=self._messages_for_round(
                    messages=messages,
                    previous_response_id=previous_response_id,
                    tool_results=tool_results,
                ),
                tools=normalized_tools,
                tool_results=tool_results,
                response_format=response_format,
                strict_output=effective_strict_output,
                reasoning={"effort": reasoning_effort},
                previous_response_id=previous_response_id,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_output_tokens,
            )
            async for event in events:
                if event.type == "text_delta" and isinstance(event.delta, str):
                    yield event.delta
                if event.type == "tool_call_done" and event.tool_call is not None:
                    tool_calls.append(event.tool_call)
                if event.response_id:
                    round_response_id = event.response_id

            if not tool_calls:
                return

            tool_results = await self._execute_tool_calls_async(
                tool_calls, tools_by_name
            )
            previous_response_id = round_response_id

        raise RuntimeError(
            f"automatic tool execution exceeded {self.max_tool_rounds} rounds"
        )

    # Helper methods (shared with sync client)
    def _resolve_model(self, model: str | None) -> str:
        return model or self.default_model

    def _resolve_structured_output_options(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._resolve_structured_output_options(self, **kwargs)

    def _parse_structured_output_text(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._parse_structured_output_text(self, **kwargs)

    def _is_tool_continuation_round(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._is_tool_continuation_round(self, **kwargs)

    def _messages_for_round(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._messages_for_round(self, **kwargs)

    def _normalize_initial_messages(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._normalize_initial_messages(self, **kwargs)

    def _normalize_tools(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._normalize_tools(self, **kwargs)

    async def _execute_tool_calls_async(self, **kwargs: Any) -> Any:
        return await OAuthCodexClient._execute_tool_calls_async(self, **kwargs)

    def _parse_tool_kwargs(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._parse_tool_kwargs(self, **kwargs)

    def _normalize_tool_kwargs(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._normalize_tool_kwargs(self, **kwargs)

    def _resolve_pydantic_model_type(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._resolve_pydantic_model_type(self, **kwargs)

    def _resolve_tool_type_hints(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._resolve_tool_type_hints(self, **kwargs)

    def _normalize_tool_output(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._normalize_tool_output(self, **kwargs)

    async def _create_round_result_async(self, **kwargs: Any) -> Any:
        return await OAuthCodexClient._create_round_result_async(self, **kwargs)

    async def _create_round_stream_async(self, **kwargs: Any) -> Any:
        return await OAuthCodexClient._create_round_stream_async(self, **kwargs)

    def _coerce_stream_event(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._coerce_stream_event(self, **kwargs)

    def _coerce_generate_result(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._coerce_generate_result(self, **kwargs)

    def _extract_usage(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._extract_usage(self, **kwargs)

    def _extract_response_id(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._extract_response_id(self, **kwargs)

    def _extract_output_text(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._extract_output_text(self, **kwargs)

    def _extract_tool_calls(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._extract_tool_calls(self, **kwargs)

    def _coerce_tool_call(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._coerce_tool_call(self, **kwargs)

    def _iter_async_events(self, **kwargs: Any) -> Any:
        return OAuthCodexClient._iter_async_events(self, **kwargs)
],op:
Client = OAuthCodexClient
AsyncClient = AsyncOAuthCodexClient

