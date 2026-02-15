from __future__ import annotations

import pytest

from oauth_codex.tooling import _ensure_strict_json_schema, build_strict_response_format, to_responses_tools


def test_build_strict_response_format_normalizes_recursive_object_schema() -> None:
    response_format = build_strict_response_format(
        {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"},
                    },
                },
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                        },
                    },
                },
                "choice": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {
                                "a": {"type": "string"},
                            },
                        },
                        {
                            "type": "object",
                            "properties": {
                                "b": {"type": "string"},
                            },
                        },
                    ],
                },
            },
        }
    )

    schema = response_format["schema"]
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["nested", "items", "choice"]
    assert schema["properties"]["nested"]["additionalProperties"] is False
    assert schema["properties"]["items"]["items"]["additionalProperties"] is False
    assert schema["properties"]["choice"]["anyOf"][0]["additionalProperties"] is False
    assert schema["properties"]["choice"]["anyOf"][1]["additionalProperties"] is False


def test_build_strict_response_format_inlines_ref_with_sibling_keys() -> None:
    response_format = build_strict_response_format(
        {
            "type": "object",
            "properties": {
                "item": {
                    "$ref": "#/$defs/Item",
                    "description": "Inline ref",
                }
            },
            "$defs": {
                "Item": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "default": None},
                    },
                }
            },
        }
    )

    item_schema = response_format["schema"]["properties"]["item"]
    assert "$ref" not in item_schema
    assert item_schema["description"] == "Inline ref"
    assert item_schema["additionalProperties"] is False
    assert "default" not in item_schema["properties"]["name"]


def test_build_strict_response_format_rejects_invalid_schema_input() -> None:
    with pytest.raises(TypeError):
        build_strict_response_format({"type": "json_schema", "schema": "bad"})

    with pytest.raises(ValueError, match="root must be a JSON object"):
        build_strict_response_format({"type": "array", "items": {"type": "string"}})


def test_ensure_strict_json_schema_fails_fast_on_unresolvable_ref() -> None:
    with pytest.raises(ValueError, match="Unresolvable JSON pointer ref"):
        _ensure_strict_json_schema(
            {
                "type": "object",
                "properties": {
                    "item": {
                        "$ref": "#/$defs/Missing",
                        "description": "broken",
                    }
                },
            }
        )


def test_to_responses_tools_applies_strict_schema_to_parameters() -> None:
    tools = [
        {
            "type": "function",
            "name": "demo",
            "description": "Demo tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "payload": {
                        "type": "object",
                        "properties": {"value": {"type": "string"}},
                    }
                },
            },
        }
    ]

    normalized = to_responses_tools(tools, strict_output=True)
    assert normalized[0]["strict"] is True
    assert normalized[0]["parameters"]["additionalProperties"] is False
    assert normalized[0]["parameters"]["properties"]["payload"]["additionalProperties"] is False
