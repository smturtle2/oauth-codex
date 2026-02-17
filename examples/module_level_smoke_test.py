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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Client generate smoke test")
    parser.add_argument("--model", default="gpt-5.3-codex", help="Model name")
    parser.add_argument("--prompt", default="Say hello in one sentence", help="Prompt")
    return parser


def main() -> int:
    from oauth_codex import Client

    args = _build_parser().parse_args()
    client = Client()
    response = client.generate(
        [{"role": "user", "content": args.prompt}],
        model=args.model,
    )

    print("----- module-level response -----")
    print(response)
    print("---------------------------------")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
