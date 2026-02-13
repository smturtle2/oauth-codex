from __future__ import annotations

import os
import stat
from pathlib import Path

from oauth_codex.store import FallbackTokenStore, FileTokenStore
from oauth_codex.types import OAuthTokens


class MemoryStore:
    def __init__(
        self,
        tokens: OAuthTokens | None = None,
        *,
        fail_load: bool = False,
        fail_save: bool = False,
        fail_delete: bool = False,
    ) -> None:
        self.tokens = tokens
        self.fail_load = fail_load
        self.fail_save = fail_save
        self.fail_delete = fail_delete

    def load(self) -> OAuthTokens | None:
        if self.fail_load:
            raise RuntimeError("load failed")
        return self.tokens

    def save(self, tokens: OAuthTokens) -> None:
        if self.fail_save:
            raise RuntimeError("save failed")
        self.tokens = tokens

    def delete(self) -> None:
        if self.fail_delete:
            raise RuntimeError("delete failed")
        self.tokens = None


def _tokens(access_token: str = "a1") -> OAuthTokens:
    return OAuthTokens(access_token=access_token, refresh_token="r1", expires_at=9_999_999_999)


def test_file_store_save_load_with_secure_permissions(tmp_path: Path) -> None:
    path = tmp_path / "auth.json"
    store = FileTokenStore(path=path)

    tokens = _tokens()
    tokens.api_key = "sk-exchanged"
    store.save(tokens)
    loaded = store.load()

    assert loaded is not None
    assert loaded.access_token == "a1"
    assert loaded.api_key == "sk-exchanged"

    mode = stat.S_IMODE(os.stat(path).st_mode)
    assert mode == stat.S_IRUSR | stat.S_IWUSR


def test_fallback_load_prefers_keyring_store() -> None:
    keyring_store = MemoryStore(tokens=_tokens("from-keyring"))
    file_store = MemoryStore(tokens=_tokens("from-file"))
    store = FallbackTokenStore(
        keyring_store=keyring_store,
        file_store=file_store,
        legacy_keyring_store=MemoryStore(),
        legacy_file_store=MemoryStore(),
    )

    loaded = store.load()

    assert loaded is not None
    assert loaded.access_token == "from-keyring"


def test_fallback_save_uses_file_when_keyring_fails() -> None:
    keyring_store = MemoryStore(fail_save=True)
    file_store = MemoryStore()
    store = FallbackTokenStore(
        keyring_store=keyring_store,
        file_store=file_store,
        legacy_keyring_store=MemoryStore(),
        legacy_file_store=MemoryStore(),
    )

    store.save(_tokens("from-file"))

    assert file_store.tokens is not None
    assert file_store.tokens.access_token == "from-file"


def test_fallback_load_uses_file_when_keyring_fails() -> None:
    keyring_store = MemoryStore(fail_load=True)
    file_store = MemoryStore(tokens=_tokens("from-file"))
    store = FallbackTokenStore(
        keyring_store=keyring_store,
        file_store=file_store,
        legacy_keyring_store=MemoryStore(),
        legacy_file_store=MemoryStore(),
    )

    loaded = store.load()

    assert loaded is not None
    assert loaded.access_token == "from-file"


def test_fallback_migrates_legacy_keyring_tokens_to_primary_store() -> None:
    primary_keyring = MemoryStore()
    primary_file = MemoryStore()
    legacy_keyring = MemoryStore(tokens=_tokens("legacy-keyring"))
    legacy_file = MemoryStore()
    store = FallbackTokenStore(
        keyring_store=primary_keyring,
        file_store=primary_file,
        legacy_keyring_store=legacy_keyring,
        legacy_file_store=legacy_file,
    )

    loaded = store.load()

    assert loaded is not None
    assert loaded.access_token == "legacy-keyring"
    assert primary_keyring.tokens is not None
    assert primary_keyring.tokens.access_token == "legacy-keyring"
    assert legacy_keyring.tokens is None


def test_fallback_migrates_legacy_file_tokens_to_primary_store() -> None:
    primary_keyring = MemoryStore()
    primary_file = MemoryStore()
    legacy_keyring = MemoryStore()
    legacy_file = MemoryStore(tokens=_tokens("legacy-file"))
    store = FallbackTokenStore(
        keyring_store=primary_keyring,
        file_store=primary_file,
        legacy_keyring_store=legacy_keyring,
        legacy_file_store=legacy_file,
    )

    loaded = store.load()

    assert loaded is not None
    assert loaded.access_token == "legacy-file"
    assert primary_keyring.tokens is not None
    assert primary_keyring.tokens.access_token == "legacy-file"
    assert legacy_file.tokens is None


def test_fallback_returns_legacy_tokens_even_if_migration_save_fails() -> None:
    primary_keyring = MemoryStore(fail_save=True)
    primary_file = MemoryStore(fail_save=True)
    legacy_keyring = MemoryStore(tokens=_tokens("legacy-only"))
    store = FallbackTokenStore(
        keyring_store=primary_keyring,
        file_store=primary_file,
        legacy_keyring_store=legacy_keyring,
        legacy_file_store=MemoryStore(),
    )

    loaded = store.load()

    assert loaded is not None
    assert loaded.access_token == "legacy-only"
    assert legacy_keyring.tokens is not None
    assert legacy_keyring.tokens.access_token == "legacy-only"
