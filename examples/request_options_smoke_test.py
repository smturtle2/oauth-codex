#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Prefer local source tree when running examples from the repository.
_SRC_PATH = Path(__file__).resolve().parents[1] / "src"
_SRC_PATH_STR = str(_SRC_PATH)
if _SRC_PATH_STR in sys.path:
    sys.path.remove(_SRC_PATH_STR)
sys.path.insert(0, _SRC_PATH_STR)

DEFAULT_IMAGE_URL = "https://raw.githubusercontent.com/github/explore/main/topics/python/python.png"
FALLBACK_IMAGE_URL = "https://httpbin.org/image/png"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Live smoke test for Client generate options")
    parser.add_argument("--model", default="gpt-5.3-codex", help="Model name")
    parser.add_argument(
        "--image-url",
        default=DEFAULT_IMAGE_URL,
        help="Image URL or data URL for input_image test",
    )
    return parser


def _ok(label: str, detail: str) -> None:
    print(f"[PASS] {label}: {detail}")


def _fail(label: str, detail: str) -> None:
    print(f"[FAIL] {label}: {detail}")


def _test_output_schema_and_reasoning(client: Any, model: str) -> bool:
    label = "output_schema + reasoning_effort"
    try:
        response = client.generate(
            [{"role": "user", "content": "Return {'ok': true, 'source': 'messages_api_test'} as JSON."}],
            model=model,
            output_schema={
                "type": "object",
                "properties": {
                    "ok": {"type": "boolean"},
                    "source": {"type": "string"},
                },
            },
            reasoning_effort="low",
        )
        if not isinstance(response, dict):
            _fail(label, f"expected dict output, got {type(response).__name__}")
            return False

        if response.get("ok") is not True or response.get("source") != "messages_api_test":
            _fail(label, f"unexpected JSON payload: {response!r}")
            return False
        _ok(label, f"valid JSON returned -> {response!r}")
        return True
    except Exception as exc:
        _fail(label, str(exc))
        return False


def _test_tool_auto_loop(client: Any, model: str) -> bool:
    label = "tools auto-loop"

    def pick_city(country: str) -> dict[str, str]:
        return {"city": "Seoul", "country": country}

    try:
        response = client.generate(
            [{"role": "user", "content": "Pick one city in Korea and explain briefly."}],
            model=model,
            tools=[pick_city],
        )
        if not isinstance(response, str) or not response.strip():
            _fail(label, "empty text response")
            return False

        _ok(label, "request succeeded")
        return True
    except Exception as exc:
        _fail(label, str(exc))
        return False


def _test_stream_text(client: Any, model: str) -> bool:
    label = "stream text delta"
    try:
        deltas = list(client.stream([{"role": "user", "content": "Say OK in one short sentence."}], model=model))
        text = "".join(deltas).strip()
        if not text:
            _fail(label, "empty stream output")
            return False
        _ok(label, f"streamed {len(deltas)} chunks")
        return True
    except Exception as exc:
        _fail(label, str(exc))
        return False


def _test_image_input_messages(client: Any, model: str, image_url: str) -> bool:
    label = "image input messages"
    image_candidates = [image_url]
    if image_url == DEFAULT_IMAGE_URL:
        image_candidates.append(FALLBACK_IMAGE_URL)

    last_error: Exception | None = None
    for candidate in image_candidates:
        try:
            response = client.generate(
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": "What do you see in this image? Keep it short."},
                            {"type": "input_image", "image_url": candidate},
                        ],
                    }
                ],
                model=model,
            )
            if not isinstance(response, str) or not response.strip():
                _fail(label, f"empty text response for {candidate}")
                return False
            _ok(label, f"received {len(response)} chars ({candidate})")
            return True
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        _fail(label, str(last_error))
    return False


def main() -> int:
    from oauth_codex import OAuthCodexClient

    args = _build_parser().parse_args()
    client = OAuthCodexClient()

    checks = [
        _test_output_schema_and_reasoning(client, args.model),
        _test_tool_auto_loop(client, args.model),
        _test_stream_text(client, args.model),
        _test_image_input_messages(client, args.model, args.image_url),
    ]
    passed = sum(1 for ok in checks if ok)
    total = len(checks)
    print(f"Result: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
