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
    parser = argparse.ArgumentParser(description="Beta run_tools smoke test")
    parser.add_argument("--model", default="gpt-5.3-codex", help="Model name")
    return parser


def main() -> int:
    from oauth_codex import Client

    args = _build_parser().parse_args()
    client = Client()
    client.authenticate()

    def add(a: int, b: int) -> int:
        return a + b

    completion = client.beta.chat.completions.run_tools(
        model=args.model,
        messages=[{"role": "user", "content": "What is 2 + 3?"}],
        tools=[add],
    )

    print("----- beta run_tools -----")
    print(completion.choices[0].message.content)
    print("--------------------------")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
