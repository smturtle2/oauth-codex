#!/usr/bin/env python3
from __future__ import annotations

import argparse


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex OAuth login + responses smoke test")
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
            events = client.responses.create(model=args.model, input=args.prompt, stream=True)
            for event in events:
                if event.type == "text_delta" and event.delta:
                    print(event.delta, end="", flush=True)
            print("\n----- stream end -----")
        else:
            response = client.responses.create(model=args.model, input=args.prompt)
            print("----- response -----")
            print(response.output_text)
            print("--------------------")
    except AuthRequiredError as exc:
        print("Authentication flow requires user action.")
        print(str(exc))
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
