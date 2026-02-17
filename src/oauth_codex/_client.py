from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any, AsyncIterator, Callable, Iterator, get_type_hints

from pydantic import BaseModel

from ._base_client import SyncAPIClient
from ._engine import OAuthCodexClient as _EngineClient
from .auth.config import OAuthConfig
from .core_types import (
    GenerateResult,
    ReasoningEffort,
    ToolCall,
    ToolResult,
    listMessage,
)
from .store import FallbackTokenStore
from .tooling import build_strict_response_format, callable_to_tool_schema, normalize_tool_output

DEFAULT_MODEL = "gpt-5.3-codex"
DEFAULT_MAX_TOOL_ROUNDS = 16
StructuredOutputSchema = type[BaseModel] | dict[str, Any]


class OAuthCodexClient(SyncAPIClient):
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
        self.default_model = DEFAULT_MODEL
        self.max_tool_rounds = DEFAULT_MAX_TOOL_ROUNDS

    def is_authenticated(self) -> bool:
        return self._engine.is_authenticated()

    def is_expired(self, *, leeway_seconds: int = 60) -> bool:
        return self._engine.is_expired(leeway_seconds=leeway_seconds)

    def refresh_if_needed(self, *, force: bool = False) -> bool:
        return self._engine.refresh_if_needed(force=force)

    async def arefresh_if_needed(self, *, force: bool = False) -> bool:
        return await self._engine.arefresh_if_needed(force=force)

    def login(self) -> None:
        self._engine.login()

    async def alogin(self) -> None:
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
        messages = self._normalize_initial_messages(messages)
        normalized_tools, tools_by_name = self._normalize_tools(tools)
        response_format, effective_strict_output = self._resolve_structured_output_options(
            output_schema=output_schema,
            strict_output=strict_output,
        )

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None
        output_parts: list[str] = []

        for _ in range(self.max_tool_rounds):
            result = self._engine.generate(
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
                return_details=True,
            )
            if not isinstance(result, GenerateResult):
                raise TypeError("internal error: expected GenerateResult")

            if result.text:
                output_parts.append(result.text)

            if not result.tool_calls:
                text = "".join(output_parts)
                if output_schema is None:
                    return text
                return self._parse_structured_output_text(text=text, output_schema=output_schema)

            tool_results = self._execute_tool_calls_sync(result.tool_calls, tools_by_name)
            previous_response_id = result.response_id

        raise RuntimeError(f"automatic tool execution exceeded {self.max_tool_rounds} rounds")

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
        messages = self._normalize_initial_messages(messages)
        normalized_tools, tools_by_name = self._normalize_tools(tools)
        response_format, effective_strict_output = self._resolve_structured_output_options(
            output_schema=output_schema,
            strict_output=strict_output,
        )

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None
        output_parts: list[str] = []

        for _ in range(self.max_tool_rounds):
            result = await self._engine.agenerate(
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
                return_details=True,
            )
            if not isinstance(result, GenerateResult):
                raise TypeError("internal error: expected GenerateResult")

            if result.text:
                output_parts.append(result.text)

            if not result.tool_calls:
                text = "".join(output_parts)
                if output_schema is None:
                    return text
                return self._parse_structured_output_text(text=text, output_schema=output_schema)

            tool_results = await self._execute_tool_calls_async(result.tool_calls, tools_by_name)
            previous_response_id = result.response_id

        raise RuntimeError(f"automatic tool execution exceeded {self.max_tool_rounds} rounds")

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
        messages = self._normalize_initial_messages(messages)
        normalized_tools, tools_by_name = self._normalize_tools(tools)
        response_format, effective_strict_output = self._resolve_structured_output_options(
            output_schema=output_schema,
            strict_output=strict_output,
        )

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None

        for _ in range(self.max_tool_rounds):
            tool_calls: list[ToolCall] = []
            round_response_id: str | None = previous_response_id
            events = self._engine.generate_stream(
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
                raw_events=True,
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

        raise RuntimeError(f"automatic tool execution exceeded {self.max_tool_rounds} rounds")

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
        messages = self._normalize_initial_messages(messages)
        normalized_tools, tools_by_name = self._normalize_tools(tools)
        response_format, effective_strict_output = self._resolve_structured_output_options(
            output_schema=output_schema,
            strict_output=strict_output,
        )

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None

        for _ in range(self.max_tool_rounds):
            tool_calls: list[ToolCall] = []
            round_response_id: str | None = previous_response_id
            events = await self._engine.agenerate_stream(
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
                raw_events=True,
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

            tool_results = await self._execute_tool_calls_async(tool_calls, tools_by_name)
            previous_response_id = round_response_id

        raise RuntimeError(f"automatic tool execution exceeded {self.max_tool_rounds} rounds")

    def _resolve_model(self, model: str | None) -> str:
        return model or self.default_model

    def _resolve_structured_output_options(
        self,
        *,
        output_schema: StructuredOutputSchema | None,
        strict_output: bool | None,
    ) -> tuple[dict[str, Any] | None, bool]:
        effective_strict_output = strict_output if strict_output is not None else bool(output_schema)
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
    ) -> tuple[list[dict[str, Any]], dict[str, Callable[..., Any]]]:
        if tools is None:
            return [], {}
        if not isinstance(tools, list):
            raise TypeError("tools must be a list of callables")

        schemas: list[dict[str, Any]] = []
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
                        raise TypeError("async tool is not supported in generate(); use agenerate()")
                    output = self._normalize_tool_output(value)
                except Exception as exc:
                    output = {"error": str(exc) or exc.__class__.__name__}
            results.append(ToolResult(tool_call_id=call.id, name=call.name, output=output))
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
            results.append(ToolResult(tool_call_id=call.id, name=call.name, output=output))
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
                        raise TypeError(f"tool argument `{param.name}` must be a JSON object")
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


Client = OAuthCodexClient
