#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Prefer local source tree when running examples from the repository.
_SRC_PATH = Path(__file__).resolve().parents[1] / "src"
_SRC_PATH_STR = str(_SRC_PATH)
if _SRC_PATH_STR in sys.path:
    sys.path.remove(_SRC_PATH_STR)
sys.path.insert(0, _SRC_PATH_STR)

DEFAULT_IMAGE_URL = "https://raw.githubusercontent.com/github/explore/main/topics/python/python.png"
FALLBACK_IMAGE_URL = "https://httpbin.org/image/png"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Client image input smoke test")
    parser.add_argument("--model", default="gpt-5.3-codex", help="Model name")
    parser.add_argument(
        "--prompt",
        default="Describe this image in one short sentence.",
        help="Prompt text",
    )
    parser.add_argument(
        "--image-url",
        default=DEFAULT_IMAGE_URL,
        help="Image URL or data URL",
    )
    return parser


def main() -> int:
    from oauth_codex import Client, SDKRequestError

    args = _build_parser().parse_args()
    client = Client()
    image_candidates = [args.image_url]
    if args.image_url == DEFAULT_IMAGE_URL:
        image_candidates.append(FALLBACK_IMAGE_URL)

    last_error: str | None = None
    for image_url in image_candidates:
        try:
            response = client.generate(
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": args.prompt},
                            {"type": "input_image", "image_url": image_url},
                        ],
                    }
                ],
                model=args.model,
            )
            break
        except SDKRequestError as exc:
            last_error = str(exc)
            print(f"image request failed for {image_url}")
            print(last_error)
    else:
        print("Try a different --image-url (https URL or data URL).")
        return 2

    print("----- image input response -----")
    print(response)
    print("-------------------------------")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
