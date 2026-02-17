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
    parser = argparse.ArgumentParser(description="Codex OAuth login + generate smoke test")
    parser.add_argument(
        "--model",
        default="gpt-5.3-codex",
        help="Model name to use (default: gpt-5.3-codex)",
    )
    parser.add_argument(
        "--prompt",
        default="안녕! 내 이름 알아?",
        help="Prompt to send after login",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Use SSE streaming output",
    )
    parser.add_argument(
        "--base-url",
        default="https://chatgpt.com/backend-api/codex",
        help="Backend base URL",
    )
    return parser


def main() -> int:
    from oauth_codex import AuthRequiredError, OAuthCodexClient

    args = _build_parser().parse_args()

    client = OAuthCodexClient(base_url=args.base_url)

    if client.is_authenticated():
        print("Already authenticated. Reusing saved credentials.")
    else:
        print("Not authenticated. Starting OAuth login flow...")
        client.login()

    print(f"Authenticated: {client.is_authenticated()}")
    print(f"Requesting response with model={args.model!r}...")

    try:
        if args.stream:
            print("----- stream begin -----")
            for delta in client.stream(
                [{"role": "user", "content": args.prompt}],
                model=args.model,
            ):
                print(delta, end="", flush=True)
            print("\n----- stream end -----")
        else:
            response = client.generate(
                [{"role": "user", "content": args.prompt}],
                model=args.model,
            )
            print("----- response -----")
            print(response)
            print("--------------------")
    except AuthRequiredError as exc:
        print("Authentication flow requires user action.")
        print(str(exc))
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
