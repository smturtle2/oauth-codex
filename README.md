# oauth-codex

Lightweight Python SDK for using the ChatGPT Codex backend with OAuth PKCE.

## Highlights

- OAuth login + token refresh
- Keyring-first token storage with file fallback
- Sync/async text generation and streaming
- Manual function-calling workflow
- Direct requests to `https://chatgpt.com/backend-api/codex/responses`

## Requirements

- Python 3.11+

## Install

```bash
pip install oauth-codex
```

For local development:

```bash
python3 -m pip install -e ".[dev]"
```

## Quick Start

```python
from oauth_codex import CodexOAuthLLM

llm = CodexOAuthLLM()

text = llm.generate(
    model="gpt-5.3-codex",
    prompt="Explain OAuth PKCE in 3 bullets.",
)
print(text)
```

On first use, the SDK prints an OAuth URL. Complete sign-in in your browser, then paste the localhost callback URL.

## Request Options

`generate` / `agenerate` / `generate_stream` / `agenerate_stream` support:

- `response_format` -> sent as `text.format`
- `tool_choice` -> sent as-is
- `strict_output=True` -> adds `"strict": true` to each function tool
- `reasoning` -> sent as-is
- `store` -> sent as-is

Example:

```python
result = llm.generate(
    model="gpt-5.3-codex",
    prompt="Return valid JSON with title and summary",
    response_format={"type": "json_object"},
    tool_choice="required",
    strict_output=True,
    reasoning={"effort": "high"},
    store=False,
    return_details=True,
)
```

Note: the current codex backend rejects `store=True` with `HTTP 400: Store must be set to false`.

## Streaming

```python
for chunk in llm.generate_stream(
    model="gpt-5.3-codex",
    prompt="Write one short paragraph about PKCE.",
):
    print(chunk, end="", flush=True)
```

## Async

```python
import asyncio
from oauth_codex import CodexOAuthLLM


async def main() -> None:
    llm = CodexOAuthLLM()
    text = await llm.agenerate(
        model="gpt-5.3-codex",
        prompt="Summarize OAuth in 2 lines.",
    )
    print(text)


asyncio.run(main())
```

## Manual Function Calling

When tools are requested:

- `return_details=False` raises `ToolCallRequiredError`
- `return_details=True` returns tool calls in `GenerateResult`

```python
from oauth_codex import CodexOAuthLLM


def get_weather(city: str) -> str:
    return f"Sunny in {city}"


llm = CodexOAuthLLM()
result = llm.generate(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "What is the weather in Seoul?"}],
    tools=[get_weather],
    return_details=True,
)

if result.finish_reason == "tool_calls":
    tool_results = [
        {
            "tool_call_id": result.tool_calls[0].id,
            "name": result.tool_calls[0].name,
            "output": get_weather((result.tool_calls[0].arguments or {}).get("city", "Seoul")),
        }
    ]
    final = llm.generate(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "What is the weather in Seoul?"}],
        tools=[get_weather],
        tool_results=tool_results,
        return_details=True,
    )
    print(final.text)
```

For tool-enabled streaming, set `raw_events=True` and consume `StreamEvent` objects.

## Authentication and Storage

- If no valid token exists, login is triggered automatically
- Storage priority:
  - Keyring service: `oauth-codex`
  - File fallback: `~/.oauth_codex/auth.json`
- Legacy credentials are migrated from:
  - Keyring service: `codex-oauth-llm`
  - File path: `~/.codex_oauth_llm/auth.json`

## Environment Variables

- `CODEX_OAUTH_CLIENT_ID`
- `CODEX_OAUTH_SCOPE`
- `CODEX_OAUTH_AUDIENCE`
- `CODEX_OAUTH_REDIRECT_URI`
- `CODEX_OAUTH_DISCOVERY_URL`
- `CODEX_OAUTH_AUTHORIZATION_ENDPOINT`
- `CODEX_OAUTH_TOKEN_ENDPOINT`
- `CODEX_OAUTH_ORIGINATOR`

## Smoke Tests

Run from repository root after editable install:

```bash
python3 examples/login_smoke_test.py --model gpt-5.3-codex --prompt "hello"
python3 examples/request_options_smoke_test.py --model gpt-5.3-codex
```

## Development

```bash
python3 -m pip install -e ".[dev]"
pytest -q
```

## Release

1. Bump `project.version` in `pyproject.toml`.
2. Tag and push:

```bash
git tag v0.3.0
git push origin main
git push origin v0.3.0
```

3. Verify GitHub Actions publish and install:

```bash
pip install -U oauth-codex==0.3.0
```

## Notes

- This SDK supports only `api_mode="responses"` for the codex backend.
- `validate_model=True` is unsupported in codex-backend mode.
