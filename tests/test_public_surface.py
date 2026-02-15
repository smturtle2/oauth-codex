from __future__ import annotations

import pytest

import oauth_codex


def test_public_client_exports() -> None:
    assert oauth_codex.OAuthCodexClient is not None
    assert oauth_codex.AsyncOAuthCodexClient is not None
    assert oauth_codex.Client is oauth_codex.OAuthCodexClient
    assert oauth_codex.AsyncClient is oauth_codex.AsyncOAuthCodexClient


def test_module_level_resource_proxies_exist() -> None:
    for name in ["responses", "files", "vector_stores", "models"]:
        assert hasattr(oauth_codex, name)


def test_removed_resources_absent() -> None:
    for name in [
        "completions",
        "chat",
        "embeddings",
        "images",
        "audio",
        "moderations",
        "fine_tuning",
        "beta",
        "batches",
        "uploads",
        "realtime",
        "conversations",
        "evals",
        "containers",
        "videos",
        "webhooks",
    ]:
        assert not hasattr(oauth_codex, name)


def test_legacy_modules_removed() -> None:
    with pytest.raises(ModuleNotFoundError):
        import oauth_codex.legacy_types  # noqa: F401

    with pytest.raises(ModuleNotFoundError):
        import oauth_codex.legacy_auth  # noqa: F401
