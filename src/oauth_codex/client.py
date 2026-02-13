from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Iterator, Literal

import httpx

from .auth import (
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
from .errors import (
    AuthRequiredError,
    LLMRequestError,
    ModelValidationError,
    ToolCallRequiredError,
    TokenRefreshError,
)
from .store import FallbackTokenStore
from .tooling import normalize_tool_inputs, to_responses_tools, tool_results_to_response_items
from .types import (
    GenerateResult,
    Message,
    OAuthConfig,
    OAuthTokens,
    StreamEvent,
    TokenStore,
    TokenUsage,
    ToolCall,
    ToolInput,
    ToolResult,
)


class CodexOAuthLLM:
    def __init__(
        self,
        *,
        oauth_config: OAuthConfig | None = None,
        token_store: TokenStore | None = None,
        chatgpt_base_url: str = "https://chatgpt.com/backend-api/codex",
        timeout: float = 60.0,
    ) -> None:
        self.oauth_config = load_oauth_config(oauth_config)
        self.token_store = token_store or FallbackTokenStore()
        self.chatgpt_base_url = chatgpt_base_url.rstrip("/")
        self.timeout = timeout
        self._refresh_leeway_seconds = 60

    def is_authenticated(self) -> bool:
        tokens = self.token_store.load()
        if not tokens:
            return False
        return not tokens.is_expired(leeway_seconds=0)

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
            self.token_store.save(tokens)

    def generate(
        self,
        *,
        model: str,
        prompt: str | None = None,
        messages: list[Message] | None = None,
        api_mode: Literal["responses"] = "responses",
        tools: list[ToolInput] | None = None,
        tool_results: list[ToolResult] | None = None,
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
        )
        if raw_events:
            return events
        return self._text_only_stream_async(events)

    def _require_responses_mode(self, api_mode: str) -> None:
        if api_mode != "responses":
            raise ValueError(
                "Only api_mode='responses' is supported for chatgpt.com/backend-api/codex"
            )

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

    def _ensure_authenticated_sync(self) -> OAuthTokens:
        tokens = self.token_store.load()
        if not tokens:
            self.login()
            tokens = self.token_store.load()
            if not tokens:
                raise AuthRequiredError("OAuth login did not produce stored credentials")

        if tokens.is_expired(leeway_seconds=self._refresh_leeway_seconds):
            tokens = self._refresh_and_persist_sync(tokens)
        return tokens

    async def _ensure_authenticated_async(self) -> OAuthTokens:
        tokens = await asyncio.to_thread(self.token_store.load)
        if not tokens:
            await asyncio.to_thread(self.login)
            tokens = await asyncio.to_thread(self.token_store.load)
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
            self.token_store.save(refreshed)
            return refreshed
        except TokenRefreshError as exc:
            self.token_store.delete()
            raise AuthRequiredError(
                "Your access token could not be refreshed. Please sign in again."
            ) from exc

    async def _refresh_and_persist_async(self, tokens: OAuthTokens) -> OAuthTokens:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                self.oauth_config = await discover_endpoints_async(client, self.oauth_config)
                refreshed = await refresh_tokens_async(client, self.oauth_config, tokens)
            await asyncio.to_thread(self.token_store.save, refreshed)
            return refreshed
        except TokenRefreshError as exc:
            await asyncio.to_thread(self.token_store.delete)
            raise AuthRequiredError(
                "Your access token could not be refreshed. Please sign in again."
            ) from exc

    def _validate_model_sync(self, model: str, tokens: OAuthTokens) -> None:
        _ = model, tokens
        raise ModelValidationError(
            "Model validation via /models is unavailable on chatgpt.com/backend-api/codex. "
            "Disable validate_model."
        )

    async def _validate_model_async(self, model: str, tokens: OAuthTokens) -> None:
        _ = model, tokens
        raise ModelValidationError(
            "Model validation via /models is unavailable on chatgpt.com/backend-api/codex. "
            "Disable validate_model."
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
        if path != "/responses":
            raise LLMRequestError("codex backend path only supports /responses")
        return f"{self.chatgpt_base_url}{path}"

    def _generate_responses_sync(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[dict[str, Any]],
        tool_results: list[ToolResult],
    ) -> GenerateResult:
        events = self._stream_responses_sync(
            model=model,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
        )
        return self._collect_generate_result_from_stream_sync(events)

    async def _generate_responses_async(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[dict[str, Any]],
        tool_results: list[ToolResult],
    ) -> GenerateResult:
        events = self._stream_responses_async(
            model=model,
            messages=messages,
            tools=tools,
            tool_results=tool_results,
        )
        return await self._collect_generate_result_from_stream_async(events)

    def _stream_responses_sync(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[dict[str, Any]],
        tool_results: list[ToolResult],
    ) -> Iterator[StreamEvent]:
        tokens = self._ensure_authenticated_sync()
        payload: dict[str, Any] = {
            "model": model,
            "input": [*messages, *tool_results_to_response_items(tool_results)],
            "instructions": self._derive_instructions(messages),
            "store": False,
            "stream": True,
        }
        if tools:
            payload["tools"] = to_responses_tools(tools)

        yield from self._stream_sse_sync(
            path="/responses",
            payload=payload,
            parser=self._map_responses_stream,
            tokens=tokens,
        )

    async def _stream_responses_async(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[dict[str, Any]],
        tool_results: list[ToolResult],
    ) -> AsyncIterator[StreamEvent]:
        tokens = await self._ensure_authenticated_async()
        payload: dict[str, Any] = {
            "model": model,
            "input": [*messages, *tool_results_to_response_items(tool_results)],
            "instructions": self._derive_instructions(messages),
            "store": False,
            "stream": True,
        }
        if tools:
            payload["tools"] = to_responses_tools(tools)

        async for event in self._stream_sse_async(
            path="/responses",
            payload=payload,
            parser=self._map_responses_stream,
            tokens=tokens,
        ):
            yield event

    def _stream_sse_sync(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        parser,
        tokens: OAuthTokens | None = None,
    ) -> Iterator[StreamEvent]:
        if tokens is None:
            tokens = self._ensure_authenticated_sync()
        url = self._resolve_request_url(path)
        attempted_refresh = False

        while True:
            headers = self._auth_headers(tokens)
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 401 and not attempted_refresh:
                        tokens = self._refresh_and_persist_sync(tokens)
                        attempted_refresh = True
                        continue
                    if response.status_code >= 400:
                        raise LLMRequestError(self._error_message(response))

                    for event_name, data_text in self._iter_sse_events(response.iter_lines()):
                        if data_text == "[DONE]":
                            yield StreamEvent(type="done")
                            return

                        payload_obj = self._parse_sse_data(data_text)
                        if payload_obj is None:
                            continue

                        mapped = parser(event_name, payload_obj)
                        for item in mapped:
                            yield item
                    return

    async def _stream_sse_async(
        self,
        *,
        path: str,
        payload: dict[str, Any],
        parser,
        tokens: OAuthTokens | None = None,
    ) -> AsyncIterator[StreamEvent]:
        if tokens is None:
            tokens = await self._ensure_authenticated_async()
        url = self._resolve_request_url(path)
        attempted_refresh = False

        while True:
            headers = self._auth_headers(tokens)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 401 and not attempted_refresh:
                        tokens = await self._refresh_and_persist_async(tokens)
                        attempted_refresh = True
                        continue
                    if response.status_code >= 400:
                        raise LLMRequestError(self._error_message(response))

                    async for event_name, data_text in self._aiter_sse_events(response.aiter_lines()):
                        if data_text == "[DONE]":
                            yield StreamEvent(type="done")
                            return

                        payload_obj = self._parse_sse_data(data_text)
                        if payload_obj is None:
                            continue

                        mapped = parser(event_name, payload_obj)
                        for item in mapped:
                            yield item
                    return

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

        for event in events:
            if isinstance(event.raw, dict):
                raw_response = event.raw
            if event.type == "text_delta" and isinstance(event.delta, str):
                text_parts.append(event.delta)
            elif event.type == "tool_call_done" and event.tool_call is not None:
                tool_calls.append(event.tool_call)
            elif event.type == "usage":
                usage = event.usage
            elif event.type == "error":
                error_message = event.error or "Streaming request failed"

        if error_message:
            raise LLMRequestError(error_message)

        finish_reason: Literal["stop", "tool_calls", "length", "error"]
        finish_reason = "tool_calls" if tool_calls else "stop"

        return GenerateResult(
            text="".join(text_parts),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            raw_response=raw_response,
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

        async for event in events:
            if isinstance(event.raw, dict):
                raw_response = event.raw
            if event.type == "text_delta" and isinstance(event.delta, str):
                text_parts.append(event.delta)
            elif event.type == "tool_call_done" and event.tool_call is not None:
                tool_calls.append(event.tool_call)
            elif event.type == "usage":
                usage = event.usage
            elif event.type == "error":
                error_message = event.error or "Streaming request failed"

        if error_message:
            raise LLMRequestError(error_message)

        finish_reason: Literal["stop", "tool_calls", "length", "error"]
        finish_reason = "tool_calls" if tool_calls else "stop"

        return GenerateResult(
            text="".join(text_parts),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            raw_response=raw_response,
        )

    def _map_responses_stream(
        self,
        event_name: str,
        payload: dict[str, Any],
    ) -> list[StreamEvent]:
        out: list[StreamEvent] = []
        event_type = str(payload.get("type") or event_name)

        if event_type.endswith("output_text.delta"):
            delta = payload.get("delta")
            if isinstance(delta, str):
                out.append(StreamEvent(type="text_delta", delta=delta, raw=payload))

        if "function_call_arguments.delta" in event_type:
            delta = payload.get("delta")
            out.append(
                StreamEvent(
                    type="tool_call_delta",
                    delta=delta if isinstance(delta, str) else None,
                    raw=payload,
                )
            )

        if "function_call_arguments.done" in event_type:
            call_id = str(payload.get("call_id") or payload.get("id") or "")
            name = str(payload.get("name") or "tool")
            arguments_json = str(payload.get("arguments") or "{}")
            out.append(
                StreamEvent(
                    type="tool_call_done",
                    tool_call=self._build_tool_call(call_id, name, arguments_json),
                    raw=payload,
                )
            )

        if "usage" in payload:
            out.append(StreamEvent(type="usage", usage=self._parse_usage(payload.get("usage")), raw=payload))

        if event_type.endswith("completed"):
            out.append(StreamEvent(type="done", raw=payload))

        if event_type.endswith("error") or payload.get("error"):
            out.append(StreamEvent(type="error", raw=payload, error=self._extract_error_text(payload)))

        return out

    def _build_tool_call(self, call_id: str, name: str, arguments_json: str) -> ToolCall:
        parsed: dict[str, Any] | None
        try:
            obj = json.loads(arguments_json)
            parsed = obj if isinstance(obj, dict) else None
        except ValueError:
            parsed = None
        return ToolCall(id=call_id, name=name, arguments_json=arguments_json, arguments=parsed)

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
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens if isinstance(output_tokens, int) else None,
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
