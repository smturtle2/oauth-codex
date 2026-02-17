#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Prefer local source tree when running examples from the repository.
_SRC_PATH = Path(__file__).resolve().parents[1] / "src"
_SRC_PATH_STR = str(_SRC_PATH)
if _SRC_PATH_STR in sys.path:
    sys.path.remove(_SRC_PATH_STR)
sys.path.insert(0, _SRC_PATH_STR)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Async client smoke test")
    parser.add_argument("--model", default="gpt-5.3-codex", help="Model name")
    parser.add_argument("--prompt", default="Summarize OAuth PKCE in 2 bullets", help="Prompt text")
    return parser


async def _run(model: str, prompt: str) -> int:
    from oauth_codex import Client

    client = Client()
    response = await client.agenerate(
        [{"role": "user", "content": prompt}],
        model=model,
    )

    print("----- async response -----")
    print(response)
    print("--------------------------")
    return 0


def main() -> int:
    args = _build_parser().parse_args()
    return asyncio.run(_run(args.model, args.prompt))


if __name__ == "__main__":
    raise SystemExit(main())
