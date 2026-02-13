#!/usr/bin/env python3
from __future__ import annotations

import argparse


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex OAuth login + generation smoke test")
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
        help="Use streaming output",
    )
    return parser


def main() -> int:
    from oauth_codex import AuthRequiredError, CodexOAuthLLM, ToolCallRequiredError

    args = _build_parser().parse_args()

    llm = CodexOAuthLLM()

    if llm.is_authenticated():
        print("Already authenticated. Reusing saved credentials.")
    else:
        print("Not authenticated. Starting OAuth login flow...")
        llm.login()

    print(f"Authenticated: {llm.is_authenticated()}")

    print(f"Requesting response with model={args.model!r}...")
    try:
        if args.stream:
            print("----- stream begin -----")
            for chunk in llm.generate_stream(
                model=args.model,
                prompt=args.prompt,
            ):
                print(chunk, end="", flush=True)
            print("\n----- stream end -----")
        else:
            text = llm.generate(
                model=args.model,
                prompt=args.prompt,
            )
            print("----- response -----")
            print(text)
            print("--------------------")
    except ToolCallRequiredError as exc:
        print("Model requested function/tool calling. This smoke test only prints text responses.")
        print(f"tool_calls={len(exc.tool_calls)}")
        for call in exc.tool_calls:
            print(f"- id={call.id!r} name={call.name!r} args={call.arguments_json!r}")
        return 2
    except AuthRequiredError as exc:
        print("Authentication flow requires user action.")
        print(str(exc))
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
