#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Live smoke test for response_format/tool_choice/strict_output/store/reasoning options"
    )
    parser.add_argument(
        "--model",
        default="gpt-5.3-codex",
        help="Model name to use (default: gpt-5.3-codex)",
    )
    return parser


def _ok(label: str, detail: str) -> None:
    print(f"[PASS] {label}: {detail}")


def _fail(label: str, detail: str) -> None:
    print(f"[FAIL] {label}: {detail}")


def _test_response_format_and_reasoning(llm: Any, model: str) -> bool:
    label = "response_format + reasoning"
    try:
        result = llm.generate(
            model=model,
            prompt=(
                "Return a JSON object with exactly two keys: "
                "ok (boolean true) and source ('response_format_test')."
            ),
            response_format={"type": "json_object"},
            reasoning={"effort": "low"},
            return_details=True,
        )
        parsed = json.loads(result.text)
        if not isinstance(parsed, dict):
            _fail(label, "output is not a JSON object")
            return False
        if parsed.get("ok") is not True or parsed.get("source") != "response_format_test":
            _fail(label, f"unexpected JSON payload: {parsed!r}")
            return False
        _ok(label, f"valid JSON returned -> {parsed!r}")
        return True
    except Exception as exc:
        _fail(label, str(exc))
        return False


def _test_tool_choice_required(llm: Any, model: str) -> bool:
    label = "tool_choice=required"
    try:
        result = llm.generate(
            model=model,
            messages=[{"role": "user", "content": "Pick a city for travel planning."}],
            tools=[
                {
                    "type": "function",
                    "name": "pick_city",
                    "description": "Pick one city from user intent",
                    "parameters": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                        "required": ["city"],
                        "additionalProperties": False,
                    },
                }
            ],
            tool_choice="required",
            return_details=True,
        )
        if result.finish_reason != "tool_calls":
            _fail(label, f"finish_reason={result.finish_reason!r}")
            return False
        if not result.tool_calls:
            _fail(label, "no tool call returned")
            return False
        _ok(label, f"tool call returned with args={result.tool_calls[0].arguments!r}")
        return True
    except Exception as exc:
        _fail(label, str(exc))
        return False


def _test_strict_output(llm: Any, model: str) -> bool:
    label = "strict_output=True"
    try:
        result = llm.generate(
            model=model,
            messages=[{"role": "user", "content": "Weather in Seoul in C."}],
            tools=[
                {
                    "type": "function",
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "unit": {"type": "string", "enum": ["C", "F"]},
                        },
                        "required": ["city", "unit"],
                        "additionalProperties": False,
                    },
                }
            ],
            tool_choice="required",
            strict_output=True,
            return_details=True,
        )
        if not result.tool_calls:
            _fail(label, "no tool call returned")
            return False
        args = result.tool_calls[0].arguments or {}
        if not isinstance(args, dict):
            _fail(label, f"tool arguments are not object: {args!r}")
            return False
        keys = set(args.keys())
        if keys != {"city", "unit"}:
            _fail(label, f"unexpected argument keys: {sorted(keys)!r}")
            return False
        _ok(label, f"strict schema arguments -> {args!r}")
        return True
    except Exception as exc:
        _fail(label, str(exc))
        return False


def _test_store_auto_disable(llm: Any, model: str) -> bool:
    label = "store=True auto-disable behavior"
    try:
        result = llm.generate(model=model, prompt="Say OK", store=True, return_details=True)
        if not isinstance(result.text, str) or not result.text.strip():
            _fail(label, "empty response")
            return False
        _ok(label, "request succeeded (SDK handled store policy)")
        return True
    except Exception as exc:
        _fail(label, f"unexpected error: {exc}")
        return False


def main() -> int:
    from oauth_codex import CodexOAuthLLM

    args = _build_parser().parse_args()
    llm = CodexOAuthLLM()

    checks = [
        _test_response_format_and_reasoning(llm, args.model),
        _test_tool_choice_required(llm, args.model),
        _test_strict_output(llm, args.model),
        _test_store_auto_disable(llm, args.model),
    ]
    passed = sum(1 for ok in checks if ok)
    total = len(checks)
    print(f"Result: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
