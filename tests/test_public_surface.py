from __future__ import annotations

import pytest

import oauth_codex


def test_single_client_public_surface() -> None:
    assert oauth_codex.Client is oauth_codex.OAuthCodexClient
    assert oauth_codex.Client is not None


def test_removed_async_and_module_level_exports() -> None:
    assert not hasattr(oauth_codex, "AsyncOAuthCodexClient")
    assert not hasattr(oauth_codex, "AsyncClient")

    for name in ["responses", "files", "vector_stores", "models"]:
        assert not hasattr(oauth_codex, name)


def test_legacy_modules_removed() -> None:
    with pytest.raises(ModuleNotFoundError):
        import oauth_codex.legacy_types  # noqa: F401

    with pytest.raises(ModuleNotFoundError):
        import oauth_codex.legacy_auth  # noqa: F401


def test_compat_module_removed() -> None:
    with pytest.raises(ModuleNotFoundError):
        import oauth_codex.compat  # noqa: F401
