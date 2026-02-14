#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Live smoke test for responses request options")
    parser.add_argument("--model", default="gpt-5.3-codex", help="Model name")
    return parser


def _ok(label: str, detail: str) -> None:
    print(f"[PASS] {label}: {detail}")


def _fail(label: str, detail: str) -> None:
    print(f"[FAIL] {label}: {detail}")


def _test_response_format_and_reasoning(client: Any, model: str) -> bool:
    label = "response_format + reasoning"
    try:
        response = client.responses.create(
            model=model,
            input=(
                "Return a JSON object with exactly two keys: "
                "ok (boolean true) and source ('response_format_test')."
            ),
            response_format={"type": "json_object"},
            reasoning={"effort": "low"},
        )
        if not response.output_text:
            _fail(label, "empty output_text")
            return False

        parsed = json.loads(response.output_text)
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


def _test_tool_choice_required(client: Any, model: str) -> bool:
    label = "tool_choice=required"
    try:
        response = client.responses.create(
            model=model,
            input=[{"role": "user", "content": "Pick a city for travel planning."}],
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
        )

        if response.finish_reason not in {"tool_calls", "stop", None}:
            _fail(label, f"unexpected finish_reason={response.finish_reason!r}")
            return False

        _ok(label, f"finish_reason={response.finish_reason!r}")
        return True
    except Exception as exc:
        _fail(label, str(exc))
        return False


def _test_store_auto_disable(client: Any, model: str) -> bool:
    label = "store=True policy"
    try:
        response = client.responses.create(model=model, input="Say OK", store=True)
        if not isinstance(response.output_text, str) or not response.output_text.strip():
            _fail(label, "empty response")
            return False
        _ok(label, "request succeeded")
        return True
    except Exception as exc:
        _fail(label, f"unexpected error: {exc}")
        return False


def main() -> int:
    from oauth_codex import OAuthCodexClient

    args = _build_parser().parse_args()
    client = OAuthCodexClient()

    checks = [
        _test_response_format_and_reasoning(client, args.model),
        _test_tool_choice_required(client, args.model),
        _test_store_auto_disable(client, args.model),
    ]
    passed = sum(1 for ok in checks if ok)
    total = len(checks)
    print(f"Result: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
