from __future__ import annotations

import json
import time
import uuid
from typing import Any

from oauth_codex.tooling import (
    build_strict_response_format,
    callable_to_tool_schema,
    to_responses_tools,
)
from oauth_codex.types.chat.completions import ChatCompletion

PydanticBaseModel: Any = None
try:
    from pydantic import BaseModel as PydanticBaseModel
except Exception:
    pass


def _is_pydantic_model_type(value: Any) -> bool:
    return bool(
        PydanticBaseModel is not None
        and isinstance(value, type)
        and issubclass(value, PydanticBaseModel)
    )


def _normalize_response_format(response_format: Any) -> Any:
    if _is_pydantic_model_type(response_format):
        return build_strict_response_format(response_format)
    return response_format


def _normalize_tools(tools: Any) -> Any:
    if not isinstance(tools, list):
        return tools

    normalized: list[Any] = []
    for tool in tools:
        if callable(tool):
            normalized.extend(to_responses_tools([callable_to_tool_schema(tool)]))
            continue
        normalized.append(tool)
    return normalized


def _parse_text_with_model(response_format: type[Any], text: str) -> Any:
    try:
        return response_format.model_validate_json(text)
    except Exception:
        return response_format.model_validate(json.loads(text))


def _extract_output_text(response_data: dict[str, Any]) -> str:
    output_text = response_data.get("output_text")
    if isinstance(output_text, str):
        return output_text

    chunks: list[str] = []
    output = response_data.get("output")
    if not isinstance(output, list):
        return ""

    for item in output:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("text"), str):
            chunks.append(item["text"])

        content = item.get("content")
        if not isinstance(content, list):
            continue

        for entry in content:
            if not isinstance(entry, dict):
                continue
            entry_type = entry.get("type")
            if entry_type in {"text", "output_text"} and isinstance(
                entry.get("text"), str
            ):
                chunks.append(entry["text"])

    return "".join(chunks)


def _to_chat_completion(
    *,
    response_data: dict[str, Any],
    requested_model: str,
) -> ChatCompletion:
    usage_data = response_data.get("usage")
    prompt_tokens = 0
    completion_tokens = 0

    if isinstance(usage_data, dict):
        prompt_tokens = int(
            usage_data.get("prompt_tokens") or usage_data.get("input_tokens") or 0
        )
        completion_tokens = int(
            usage_data.get("completion_tokens") or usage_data.get("output_tokens") or 0
        )
    total_tokens = prompt_tokens + completion_tokens

    return ChatCompletion.model_validate(
        {
            "id": response_data.get("id") or f"chatcmpl-{uuid.uuid4().hex}",
            "created": int(response_data.get("created") or time.time()),
            "model": response_data.get("model") or requested_model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": response_data.get("finish_reason") or "stop",
                    "message": {
                        "role": "assistant",
                        "content": _extract_output_text(response_data),
                    },
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": int(usage_data.get("total_tokens") or total_tokens)
                if isinstance(usage_data, dict)
                else total_tokens,
            },
            "system_fingerprint": response_data.get("system_fingerprint"),
            "raw_response": response_data,
        }
    )


class Completions:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any
    ) -> ChatCompletion:
        payload = dict(kwargs)
        if "response_format" in payload:
            payload["response_format"] = _normalize_response_format(
                payload["response_format"]
            )
        if "tools" in payload:
            payload["tools"] = _normalize_tools(payload["tools"])
        payload["model"] = model
        payload["input"] = messages

        response = self._client.responses.create(**payload)
        response_data = response.to_dict(exclude_unset=False, exclude_none=False)
        return _to_chat_completion(response_data=response_data, requested_model=model)

    def parse(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        response_format: type[Any],
        **kwargs: Any,
    ) -> ChatCompletion:
        if not _is_pydantic_model_type(response_format):
            raise TypeError("response_format must be a Pydantic model type")

        completion = self.create(
            model=model,
            messages=messages,
            response_format=response_format,
            **kwargs,
        )

        text = ""
        if completion.choices:
            text = completion.choices[0].message.content or ""

        parsed = _parse_text_with_model(response_format, text)
        setattr(completion, "parsed", parsed)
        for choice in completion.choices:
            setattr(choice.message, "parsed", parsed)
        return completion


class AsyncCompletions:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def create(
        self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any
    ) -> ChatCompletion:
        payload = dict(kwargs)
        if "response_format" in payload:
            payload["response_format"] = _normalize_response_format(
                payload["response_format"]
            )
        if "tools" in payload:
            payload["tools"] = _normalize_tools(payload["tools"])
        payload["model"] = model
        payload["input"] = messages

        response = await self._client.responses.create(**payload)
        response_data = response.to_dict(exclude_unset=False, exclude_none=False)
        return _to_chat_completion(response_data=response_data, requested_model=model)

    async def aparse(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        response_format: type[Any],
        **kwargs: Any,
    ) -> ChatCompletion:
        if not _is_pydantic_model_type(response_format):
            raise TypeError("response_format must be a Pydantic model type")

        completion = await self.create(
            model=model,
            messages=messages,
            response_format=response_format,
            **kwargs,
        )

        text = ""
        if completion.choices:
            text = completion.choices[0].message.content or ""

        parsed = _parse_text_with_model(response_format, text)
        setattr(completion, "parsed", parsed)
        for choice in completion.choices:
            setattr(choice.message, "parsed", parsed)
        return completion


class Chat:
    def __init__(self, client: Any) -> None:
        self.completions = Completions(client)


class AsyncChat:
    def __init__(self, client: Any) -> None:
        self.completions = AsyncCompletions(client)
