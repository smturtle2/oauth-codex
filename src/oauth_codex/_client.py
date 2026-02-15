from __future__ import annotations

import base64
import asyncio
import inspect
import json
import mimetypes
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Iterator, get_type_hints

from pydantic import BaseModel

from ._base_client import SyncAPIClient
from ._engine import OAuthCodexClient as _EngineClient
from .auth.config import OAuthConfig
from .core_types import (
    GenerateResult,
    ImageInput,
    Message,
    ReasoningEffort,
    ToolCall,
    ToolResult,
)
from .store import FallbackTokenStore
from .tooling import callable_to_tool_schema, normalize_tool_output

DEFAULT_MODEL = "gpt-5.3-codex"
DEFAULT_MAX_TOOL_ROUNDS = 8


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
        prompt: str | None = None,
        *,
        images: ImageInput | list[ImageInput] | None = None,
        tools: list[Callable[..., Any]] | None = None,
        model: str | None = None,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
    ) -> str:
        messages = self._build_messages(prompt=prompt, images=images)
        normalized_tools, tools_by_name = self._normalize_tools(tools)

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None
        output_parts: list[str] = []

        for _ in range(self.max_tool_rounds):
            result = self._engine.generate(
                model=self._resolve_model(model),
                messages=messages,
                tools=normalized_tools,
                tool_results=tool_results,
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
                return "".join(output_parts)

            tool_results = self._execute_tool_calls_sync(result.tool_calls, tools_by_name)
            previous_response_id = result.response_id

        raise RuntimeError(f"automatic tool execution exceeded {self.max_tool_rounds} rounds")

    async def agenerate(
        self,
        prompt: str | None = None,
        *,
        images: ImageInput | list[ImageInput] | None = None,
        tools: list[Callable[..., Any]] | None = None,
        model: str | None = None,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
    ) -> str:
        messages = self._build_messages(prompt=prompt, images=images)
        normalized_tools, tools_by_name = self._normalize_tools(tools)

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None
        output_parts: list[str] = []

        for _ in range(self.max_tool_rounds):
            result = await self._engine.agenerate(
                model=self._resolve_model(model),
                messages=messages,
                tools=normalized_tools,
                tool_results=tool_results,
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
                return "".join(output_parts)

            tool_results = await self._execute_tool_calls_async(result.tool_calls, tools_by_name)
            previous_response_id = result.response_id

        raise RuntimeError(f"automatic tool execution exceeded {self.max_tool_rounds} rounds")

    def stream(
        self,
        prompt: str | None = None,
        *,
        images: ImageInput | list[ImageInput] | None = None,
        tools: list[Callable[..., Any]] | None = None,
        model: str | None = None,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
    ) -> Iterator[str]:
        messages = self._build_messages(prompt=prompt, images=images)
        normalized_tools, tools_by_name = self._normalize_tools(tools)

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None

        for _ in range(self.max_tool_rounds):
            tool_calls: list[ToolCall] = []
            round_response_id: str | None = previous_response_id
            events = self._engine.generate_stream(
                model=self._resolve_model(model),
                messages=messages,
                tools=normalized_tools,
                tool_results=tool_results,
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
        prompt: str | None = None,
        *,
        images: ImageInput | list[ImageInput] | None = None,
        tools: list[Callable[..., Any]] | None = None,
        model: str | None = None,
        reasoning_effort: ReasoningEffort = "medium",
        temperature: float | None = None,
        top_p: float | None = None,
        max_output_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        messages = self._build_messages(prompt=prompt, images=images)
        normalized_tools, tools_by_name = self._normalize_tools(tools)

        previous_response_id: str | None = None
        tool_results: list[ToolResult] | None = None

        for _ in range(self.max_tool_rounds):
            tool_calls: list[ToolCall] = []
            round_response_id: str | None = previous_response_id
            events = await self._engine.agenerate_stream(
                model=self._resolve_model(model),
                messages=messages,
                tools=normalized_tools,
                tool_results=tool_results,
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

    def _build_messages(
        self,
        *,
        prompt: str | None,
        images: ImageInput | list[ImageInput] | None,
    ) -> list[Message]:
        image_urls = self._normalize_images(images)

        if prompt is not None and not isinstance(prompt, str):
            raise TypeError("prompt must be a string")
        if prompt is None and not image_urls:
            raise ValueError("Either prompt or images must be provided")

        content: list[dict[str, Any]] = []
        if prompt:
            content.append({"type": "input_text", "text": prompt})
        for image_url in image_urls:
            content.append({"type": "input_image", "image_url": image_url})

        if not content:
            raise ValueError("Either prompt or images must be provided")
        if len(content) == 1 and content[0]["type"] == "input_text":
            return [{"role": "user", "content": content[0]["text"]}]
        return [{"role": "user", "content": content}]

    def _normalize_images(self, images: ImageInput | list[ImageInput] | None) -> list[str]:
        if images is None:
            return []

        raw_items: list[ImageInput]
        if isinstance(images, (str, Path)):
            raw_items = [images]
        elif isinstance(images, list):
            raw_items = images
        else:
            raise TypeError("images must be a string/Path or list of string/Path")

        normalized: list[str] = []
        for item in raw_items:
            normalized.append(self._coerce_image_to_url(item))
        return normalized

    def _coerce_image_to_url(self, image: ImageInput) -> str:
        if isinstance(image, Path):
            return self._path_to_data_url(image)

        value = image.strip()
        if value.startswith(("http://", "https://", "data:")):
            return value
        return self._path_to_data_url(Path(value).expanduser())

    def _path_to_data_url(self, path: Path) -> str:
        if not path.is_file():
            raise FileNotFoundError(f"image file not found: {path}")

        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

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
