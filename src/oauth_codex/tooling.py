from __future__ import annotations

import inspect
import json
from types import UnionType
from typing import Any, get_args, get_origin, get_type_hints

from .core_types import ToolInput, ToolResult, ToolSchema
from .errors import SDKRequestError

try:
    from pydantic import BaseModel
except Exception:  # pragma: no cover - pydantic is a runtime dependency
    BaseModel = None  # type: ignore[assignment]


def _is_pydantic_model_type(annotation: Any) -> bool:
    return bool(
        BaseModel is not None
        and isinstance(annotation, type)
        and issubclass(annotation, BaseModel)
    )


def _pydantic_model_to_schema(model_type: type[Any]) -> dict[str, Any]:
    if hasattr(model_type, "model_json_schema"):
        schema = model_type.model_json_schema()
        if isinstance(schema, dict):
            return schema
    return {"type": "object"}


def _python_type_to_schema(annotation: Any) -> dict[str, Any]:
    if annotation is inspect._empty:
        return {"type": "string"}

    if isinstance(annotation, str):
        normalized = annotation.strip().lower()
        if normalized in {"str", "string"}:
            return {"type": "string"}
        if normalized in {"int", "integer"}:
            return {"type": "integer"}
        if normalized in {"float", "number"}:
            return {"type": "number"}
        if normalized in {"bool", "boolean"}:
            return {"type": "boolean"}
        if "list" in normalized:
            return {"type": "array"}
        if "dict" in normalized:
            return {"type": "object"}
        return {"type": "string"}

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is None:
        if _is_pydantic_model_type(annotation):
            return _pydantic_model_to_schema(annotation)
        if annotation is str:
            return {"type": "string"}
        if annotation is int:
            return {"type": "integer"}
        if annotation is float:
            return {"type": "number"}
        if annotation is bool:
            return {"type": "boolean"}
        if annotation in (dict, dict[str, Any]):
            return {"type": "object"}
        if annotation in (list, list[Any]):
            return {"type": "array"}
        return {"type": "string"}

    if str(origin) == "typing.Union" or origin is UnionType:
        non_none = [arg for arg in args if arg is not type(None)]
        if len(non_none) == 1 and len(non_none) != len(args):
            schema = _python_type_to_schema(non_none[0])
            schema["nullable"] = True
            return schema
        return {"type": "string"}

    if origin in (list, tuple):
        item_annotation = args[0] if args else Any
        return {"type": "array", "items": _python_type_to_schema(item_annotation)}

    if origin in (dict,):
        return {"type": "object"}

    return {"type": "string"}


def callable_to_tool_schema(func: Any) -> ToolSchema:
    signature = inspect.signature(func)
    try:
        resolved_hints = get_type_hints(func)
    except Exception:
        resolved_hints = {}

    doc = inspect.getdoc(func) or ""
    description = doc.splitlines()[0] if doc else f"Tool `{getattr(func, '__name__', 'tool')}`"

    params = [
        param
        for param in signature.parameters.values()
        if param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
    ]
    if len(params) == 1:
        single = params[0]
        single_annotation = resolved_hints.get(single.name, single.annotation)
        if _is_pydantic_model_type(single_annotation):
            model_schema = _python_type_to_schema(single_annotation)
            if model_schema.get("type") == "object":
                return {
                    "type": "function",
                    "name": getattr(func, "__name__", "tool"),
                    "description": description,
                    "parameters": model_schema,
                }

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in params:
        name = param.name
        annotation = resolved_hints.get(name, param.annotation)
        properties[name] = _python_type_to_schema(annotation)
        if param.default is inspect._empty:
            required.append(name)

    return {
        "type": "function",
        "name": getattr(func, "__name__", "tool"),
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }



def _normalize_dict_tool(tool: dict[str, Any]) -> ToolSchema:
    if tool.get("type") == "function" and "function" in tool and isinstance(tool["function"], dict):
        fn = tool["function"]
        return {
            "type": "function",
            "name": fn.get("name", "tool"),
            "description": fn.get("description", f"Tool `{fn.get('name', 'tool')}`"),
            "parameters": fn.get("parameters", {"type": "object", "properties": {}}),
        }

    if tool.get("type") == "function" and "name" in tool:
        return {
            "type": "function",
            "name": tool.get("name", "tool"),
            "description": tool.get("description", f"Tool `{tool.get('name', 'tool')}`"),
            "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
        }

    if "name" in tool:
        return {
            "type": "function",
            "name": tool.get("name", "tool"),
            "description": tool.get("description", f"Tool `{tool.get('name', 'tool')}`"),
            "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
        }

    raise ValueError("Unsupported tool dictionary format")


def normalize_tool_inputs(tools: list[ToolInput] | None) -> list[ToolSchema]:
    if not tools:
        return []

    normalized: list[ToolSchema] = []
    for tool in tools:
        if callable(tool):
            normalized.append(callable_to_tool_schema(tool))
            continue
        if isinstance(tool, dict):
            normalized.append(_normalize_dict_tool(tool))
            continue
        raise TypeError("Tool must be a callable or dict schema")
    return normalized


def to_responses_tools(
    tools: list[ToolSchema],
    *,
    strict_output: bool = False,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for tool in tools:
        item: dict[str, Any] = {
            "type": "function",
            "name": tool["name"],
            "description": tool.get("description", f"Tool `{tool['name']}`"),
            "parameters": dict(tool.get("parameters", {"type": "object", "properties": {}})),
        }
        if strict_output:
            item["strict"] = True
        normalized.append(item)
    return normalized


def normalize_tool_output(output: Any) -> dict[str, Any]:
    if isinstance(output, dict):
        return output
    if isinstance(output, str):
        return {"output": output}
    try:
        json.dumps(output, ensure_ascii=True)
        return {"output": output}
    except TypeError:
        return {"output": str(output)}


def serialize_tool_output(output: Any) -> str:
    return json.dumps(normalize_tool_output(output), ensure_ascii=True)


def tool_results_to_response_items(tool_results: list[ToolResult] | None) -> list[dict[str, Any]]:
    if not tool_results:
        return []
    items: list[dict[str, Any]] = []
    for result in tool_results:
        call_id = result.tool_call_id.strip()
        if not call_id:
            raise SDKRequestError(
                status_code=None,
                provider_code="invalid_tool_call_id",
                user_message=(
                    "tool_results contains an empty tool_call_id; "
                    "call_id restoration may have failed for a streamed function_call_arguments event"
                ),
                retryable=False,
                raw_error={"tool_name": result.name},
            )
        items.append(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": serialize_tool_output(result.output),
            }
        )
    return items
