from __future__ import annotations

import json
import os
import stat
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .types import OAuthTokens, TokenStore

DEFAULT_FILE_PATH = Path.home() / ".oauth_codex" / "auth.json"
LEGACY_FILE_PATH = Path.home() / ".codex_oauth_llm" / "auth.json"
DEFAULT_KEYRING_SERVICE = "oauth-codex"
LEGACY_KEYRING_SERVICE = "codex-oauth-llm"


def _tokens_from_payload(payload: dict[str, Any]) -> OAuthTokens:
    return OAuthTokens(
        access_token=payload["access_token"],
        api_key=payload.get("api_key"),
        refresh_token=payload.get("refresh_token"),
        id_token=payload.get("id_token"),
        token_type=payload.get("token_type", "Bearer"),
        scope=payload.get("scope"),
        expires_at=payload.get("expires_at"),
        account_id=payload.get("account_id"),
        last_refresh=payload.get("last_refresh"),
    )


def _tokens_to_payload(tokens: OAuthTokens) -> dict[str, Any]:
    payload = asdict(tokens)
    return payload


class FileTokenStore(TokenStore):
    def __init__(self, path: str | Path | None = None) -> None:
        if path is None:
            path = DEFAULT_FILE_PATH
        self.path = Path(path).expanduser()

    def load(self) -> OAuthTokens | None:
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "access_token" not in data:
                return None
            return _tokens_from_payload(data)
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def save(self, tokens: OAuthTokens) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        payload = _tokens_to_payload(tokens)
        serialized = json.dumps(payload, ensure_ascii=True, indent=2)

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(self.path.parent), delete=False
        ) as fp:
            tmp_path = Path(fp.name)
            fp.write(serialized)
            fp.flush()
            os.fsync(fp.fileno())

        os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_path, self.path)

    def delete(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            return


class KeyringTokenStore(TokenStore):
    def __init__(self, service_name: str = DEFAULT_KEYRING_SERVICE, username: str = "default") -> None:
        self.service_name = service_name
        self.username = username

    def _require_keyring(self):
        try:
            import keyring  # type: ignore
        except ImportError as exc:
            raise RuntimeError("keyring is not installed") from exc
        return keyring

    def load(self) -> OAuthTokens | None:
        keyring = self._require_keyring()
        raw = keyring.get_password(self.service_name, self.username)
        if not raw:
            return None
        payload = json.loads(raw)
        return _tokens_from_payload(payload)

    def save(self, tokens: OAuthTokens) -> None:
        keyring = self._require_keyring()
        payload = _tokens_to_payload(tokens)
        keyring.set_password(self.service_name, self.username, json.dumps(payload, ensure_ascii=True))

    def delete(self) -> None:
        keyring = self._require_keyring()
        try:
            keyring.delete_password(self.service_name, self.username)
        except Exception:
            return


class FallbackTokenStore(TokenStore):
    def __init__(
        self,
        keyring_store: TokenStore | None = None,
        file_store: TokenStore | None = None,
        legacy_keyring_store: TokenStore | None = None,
        legacy_file_store: TokenStore | None = None,
    ) -> None:
        self.keyring_store = keyring_store or KeyringTokenStore(service_name=DEFAULT_KEYRING_SERVICE)
        self.file_store = file_store or FileTokenStore(path=DEFAULT_FILE_PATH)
        self.legacy_keyring_store = legacy_keyring_store or KeyringTokenStore(
            service_name=LEGACY_KEYRING_SERVICE
        )
        self.legacy_file_store = legacy_file_store or FileTokenStore(path=LEGACY_FILE_PATH)

    def _safe_load(self, store: TokenStore) -> OAuthTokens | None:
        try:
            return store.load()
        except Exception:
            return None

    def _safe_delete(self, store: TokenStore) -> None:
        try:
            store.delete()
        except Exception:
            return

    def _migrate_legacy_tokens(self, tokens: OAuthTokens, legacy_store: TokenStore) -> OAuthTokens:
        migrated = False
        try:
            self.save(tokens)
            migrated = True
        except Exception:
            migrated = False

        if migrated:
            self._safe_delete(legacy_store)
        return tokens

    def load(self) -> OAuthTokens | None:
        tokens = self._safe_load(self.keyring_store)
        if tokens:
            return tokens

        tokens = self._safe_load(self.file_store)
        if tokens:
            return tokens

        tokens = self._safe_load(self.legacy_keyring_store)
        if tokens:
            return self._migrate_legacy_tokens(tokens, self.legacy_keyring_store)

        tokens = self._safe_load(self.legacy_file_store)
        if tokens:
            return self._migrate_legacy_tokens(tokens, self.legacy_file_store)

        return None

    def save(self, tokens: OAuthTokens) -> None:
        try:
            self.keyring_store.save(tokens)
            return
        except Exception:
            self.file_store.save(tokens)

    def delete(self) -> None:
        self._safe_delete(self.keyring_store)
        self._safe_delete(self.file_store)
        self._safe_delete(self.legacy_keyring_store)
        self._safe_delete(self.legacy_file_store)
