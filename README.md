# oauth-codex

Python SDK for Codex OAuth authentication with manual localhost callback paste flow.

## Features

- OAuth login with PKCE:
  - Prints authorize URL
  - Waits for callback URL via `input()`
- Token persistence:
  - Keychain first (`keyring`)
  - File fallback: `~/.oauth_codex/auth.json`
  - Auto-migrates legacy credentials from `codex-oauth-llm` / `~/.codex_oauth_llm/auth.json`
- Lazy login on first generation request
- Automatic token refresh with one retry
- Model pass-through support (e.g. `gpt-5.3-codex`)
- Text generation and streaming
- Manual function-calling workflow
- Calls `https://chatgpt.com/backend-api/codex/responses` directly

## Install

```bash
pip install -e .
```

## Automated PyPI publish (GitHub Actions)

This repository includes `.github/workflows/publish-pypi.yml`.

- Trigger: push a tag matching `v*` (example: `v0.2.1`)
- Build: `python -m build` and `twine check`
- Publish: `pypa/gh-action-pypi-publish@release/v1` with OIDC Trusted Publishing

### One-time PyPI setup

1. Create your package on PyPI once, or add a pending publisher for a new package.
2. In PyPI project settings, add a Trusted Publisher (GitHub Actions):
   - Owner: your GitHub user or org
   - Repository name: `oauth-codex`
   - Workflow name: `publish-pypi.yml`
   - Environment name: `pypi`

### Release flow

1. Bump the version in `pyproject.toml`.
2. Push a version tag (must match `pyproject.toml` version):

```bash
git tag v0.2.1
git push origin v0.2.1
```

3. Check the GitHub Actions run. After success, install from PyPI:

```bash
python3 -m pip install oauth-codex==0.2.1
```

## Quickstart

```python
from oauth_codex import CodexOAuthLLM

llm = CodexOAuthLLM()

text = llm.generate(
    model="gpt-5.3-codex",
    prompt="Explain OAuth PKCE in 3 bullets.",
)
print(text)
```

On first run, SDK prints an OAuth login URL. Complete auth in browser, then paste redirected localhost URL.

## Smoke example

After editable install, run:

```bash
python examples/login_smoke_test.py --model gpt-5.3-codex --prompt "hello"
```

## Manual function calling

```python
from oauth_codex import CodexOAuthLLM

llm = CodexOAuthLLM()

def get_weather(city: str) -> str:
    """Return weather summary for a city."""
    return f"Sunny in {city}"

result = llm.generate(
    model="gpt-5.3-codex",
    messages=[{"role": "user", "content": "What is the weather in Seoul?"}],
    tools=[get_weather],
    return_details=True,
)

if result.finish_reason == "tool_calls":
    tool_results = []
    for tc in result.tool_calls:
        if tc.name == "get_weather":
            city = (tc.arguments or {}).get("city", "Seoul")
            tool_results.append({
                "tool_call_id": tc.id,
                "name": tc.name,
                "output": get_weather(city),
            })

    final_result = llm.generate(
        model="gpt-5.3-codex",
        messages=[{"role": "user", "content": "What is the weather in Seoul?"}],
        tools=[get_weather],
        tool_results=tool_results,
        return_details=True,
    )
    print(final_result.text)
```

## Environment variables

- `CODEX_OAUTH_CLIENT_ID`
- `CODEX_OAUTH_SCOPE`
- `CODEX_OAUTH_AUDIENCE`
- `CODEX_OAUTH_REDIRECT_URI`
- `CODEX_OAUTH_DISCOVERY_URL`
- `CODEX_OAUTH_AUTHORIZATION_ENDPOINT`
- `CODEX_OAUTH_TOKEN_ENDPOINT`
- `CODEX_OAUTH_ORIGINATOR`

## Troubleshooting

- This SDK is codex-backend only:
  - Requests go to `https://chatgpt.com/backend-api/codex/responses`.
  - `chat_completions` mode and `/models` validation are not supported.
