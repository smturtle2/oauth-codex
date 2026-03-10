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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Responses API smoke test")
    parser.add_argument("--model", default="gpt-5.3-codex", help="Model name")
    parser.add_argument(
        "--prompt",
        default="Explain response streaming in one short paragraph.",
        help="Prompt text",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Use client.responses.stream(...) instead of create(...)",
    )
    return parser


def main() -> int:
    from oauth_codex import Client

    args = _build_parser().parse_args()
    client = Client()
    client.authenticate()

    if args.stream:
        print("----- stream begin -----")
        for event in client.responses.stream(
            model=args.model,
            input=[{"role": "user", "content": args.prompt}],
        ):
            if event.delta:
                print(event.delta, end="", flush=True)
        print("\n----- stream end -----")
        return 0

    response = client.responses.create(
        model=args.model,
        input=[{"role": "user", "content": args.prompt}],
    )

    print("----- responses.create -----")
    print(response.output_text)
    print("----------------------------")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
