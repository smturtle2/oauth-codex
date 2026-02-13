from __future__ import annotations

from oauth_codex.tooling import (
    callable_to_tool_schema,
    normalize_tool_inputs,
    to_responses_tools,
    tool_results_to_response_items,
)
from oauth_codex.types import ToolResult


def test_callable_to_tool_schema_builds_json_schema() -> None:
    def get_weather(city: str, days: int = 1) -> str:
        """Get weather summary."""
        return f"{city}:{days}"

    schema = callable_to_tool_schema(get_weather)

    assert schema["type"] == "function"
    assert schema["name"] == "get_weather"
    assert schema["description"] == "Get weather summary."
    assert schema["parameters"]["type"] == "object"
    assert schema["parameters"]["properties"]["city"]["type"] == "string"
    assert schema["parameters"]["properties"]["days"]["type"] == "integer"
    assert schema["parameters"]["required"] == ["city"]


def test_normalize_tool_inputs_supports_callable_and_dict() -> None:
    def get_weather(city: str) -> str:
        """Get weather summary."""
        return city

    tools = normalize_tool_inputs(
        [
            get_weather,
            {
                "type": "function",
                "function": {
                    "name": "search_docs",
                    "description": "Search docs",
                    "parameters": {"type": "object", "properties": {"q": {"type": "string"}}},
                },
            },
        ]
    )

    assert len(tools) == 2
    assert tools[0]["name"] == "get_weather"
    assert tools[1]["name"] == "search_docs"


def test_tool_result_mapping_for_responses() -> None:
    tool_results = [ToolResult(tool_call_id="c1", name="x", output={"ok": True})]

    response_items = tool_results_to_response_items(tool_results)

    assert response_items[0]["type"] == "function_call_output"
    assert response_items[0]["call_id"] == "c1"
    assert isinstance(response_items[0]["output"], str)


def test_tool_schema_conversion_for_responses_api() -> None:
    tools = [
        {
            "type": "function",
            "name": "search",
            "description": "Search docs",
            "parameters": {"type": "object", "properties": {"q": {"type": "string"}}},
        }
    ]

    responses = to_responses_tools(tools)

    assert responses[0]["type"] == "function"
    assert responses[0]["name"] == "search"
