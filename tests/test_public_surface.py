from __future__ import annotations

import pytest

import oauth_codex


def test_public_client_exports() -> None:
    assert oauth_codex.OAuthCodexClient is not None
    assert oauth_codex.AsyncOAuthCodexClient is not None
    assert oauth_codex.Client is oauth_codex.OAuthCodexClient
    assert oauth_codex.AsyncClient is oauth_codex.AsyncOAuthCodexClient


def test_module_level_resource_proxies_exist() -> None:
    for name in [
        "responses",
        "files",
        "vector_stores",
        "models",
        "chat",
        "images",
        "audio",
        "embeddings",
        "batches",
        "uploads",
        "realtime",
        "beta",
        "fine_tuning",
        "moderations",
        "evals",
        "containers",
        "videos",
        "webhooks",
    ]:
        assert hasattr(oauth_codex, name)


def test_legacy_alias_removed() -> None:
    with pytest.raises(ImportError):
        from oauth_codex import CodexOAuthLLM  # type: ignore[attr-defined]  # noqa: F401
