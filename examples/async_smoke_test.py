#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Async client smoke test")
    parser.add_argument("--model", default="gpt-5.3-codex", help="Model name")
    parser.add_argument("--prompt", default="Summarize OAuth PKCE in 2 bullets", help="Prompt")
    return parser


async def _run(model: str, prompt: str) -> int:
    from oauth_codex import AsyncOAuthCodexClient

    client = AsyncOAuthCodexClient()
    response = await client.responses.create(model=model, input=prompt)

    print("----- async response -----")
    print(response.output_text)
    print("--------------------------")
    return 0


def main() -> int:
    args = _build_parser().parse_args()
    return asyncio.run(_run(args.model, args.prompt))


if __name__ == "__main__":
    raise SystemExit(main())
