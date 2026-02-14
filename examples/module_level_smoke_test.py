#!/usr/bin/env python3
from __future__ import annotations

import argparse


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Module-level lazy client smoke test")
    parser.add_argument("--model", default="gpt-5.3-codex", help="Model name")
    parser.add_argument("--prompt", default="Say hello in one sentence", help="Prompt")
    return parser


def main() -> int:
    import oauth_codex

    args = _build_parser().parse_args()

    # Optional module-level OAuth/client settings can be configured here.
    # oauth_codex.oauth_client_id = "..."
    # oauth_codex.base_url = "https://chatgpt.com/backend-api/codex"

    response = oauth_codex.responses.create(model=args.model, input=args.prompt)

    print("----- module-level response -----")
    print(response.output_text)
    print("---------------------------------")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
