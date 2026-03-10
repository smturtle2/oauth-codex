#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC_PATH = Path(__file__).resolve().parents[1] / "src"
_SRC_PATH_STR = str(_SRC_PATH)
if _SRC_PATH_STR in sys.path:
    sys.path.remove(_SRC_PATH_STR)
sys.path.insert(0, _SRC_PATH_STR)

DEFAULT_IMAGE_URL = "https://raw.githubusercontent.com/github/explore/main/topics/python/python.png"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Image input chat completion smoke test")
    parser.add_argument("--model", default="gpt-5.3-codex", help="Model name")
    parser.add_argument(
        "--prompt",
        default="Describe this image in one short sentence.",
        help="Prompt text",
    )
    parser.add_argument("--image-url", default=DEFAULT_IMAGE_URL, help="Image URL or data URL")
    return parser


def main() -> int:
    from oauth_codex import Client

    args = _build_parser().parse_args()
    client = Client()
    client.authenticate()

    completion = client.chat.completions.create(
        model=args.model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": args.prompt},
                    {"type": "input_image", "image_url": args.image_url},
                ],
            }
        ],
    )

    print("----- image completion -----")
    print(completion.choices[0].message.content)
    print("----------------------------")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
