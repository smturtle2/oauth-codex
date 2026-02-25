from __future__ import annotations

import asyncio
from collections.abc import Callable

import httpx

from oauth_codex._exceptions import AuthRequiredError, TokenRefreshError
from oauth_codex.auth import (
    build_authorize_url,
    discover_endpoints,
    discover_endpoints_async,
    exchange_code_for_tokens,
    generate_pkce_pair,
    generate_state,
    load_oauth_config,
    parse_callback_url,
    refresh_tokens,
    refresh_tokens_async,
)
from oauth_codex.auth.config import OAuthConfig
from oauth_codex.core_types import OAuthTokens, TokenStore
from oauth_codex.store import FallbackTokenStore

from ._provider import Headers


class OAuthProvider:
    def __init__(
        self,
        *,
        token_store: TokenStore | None = None,
        oauth_config: OAuthConfig | None = None,
        timeout: float = 30.0,
        refresh_leeway_seconds: int = 30,
        prompt_callback: Callable[[str], str] | None = None,
        output_callback: Callable[[str], None] | None = None,
    ) -> None:
        self._token_store = token_store or FallbackTokenStore()
        self._oauth_config = load_oauth_config(oauth_config)
        self._timeout = timeout
        self._refresh_leeway_seconds = max(0, refresh_leeway_seconds)
        self._prompt_callback = prompt_callback or input
        self._output_callback = output_callback or print

    def ensure_valid(self, *, interactive: bool = True) -> None:
        self._ensure_authenticated_sync(interactive=interactive)

    def get_headers(self) -> Headers:
        tokens = self._ensure_authenticated_sync(interactive=True)
        return self._auth_headers(tokens)

    async def aensure_valid(self, *, interactive: bool = True) -> None:
        await self._ensure_authenticated_async(interactive=interactive)

    async def aget_headers(self) -> Headers:
        tokens = await self._ensure_authenticated_async(interactive=True)
        return self._auth_headers(tokens)

    def login(self) -> OAuthTokens:
        with httpx.Client(timeout=self._timeout) as client:
            self._oauth_config = discover_endpoints(client, self._oauth_config)

            code_verifier, code_challenge = generate_pkce_pair()
            state = generate_state()
            authorize_url = build_authorize_url(
                self._oauth_config, state, code_challenge
            )

            self._output_callback("Open this URL in your browser and complete sign-in:")
            self._output_callback(authorize_url)
            callback_url = self._prompt_callback(
                "Paste the full localhost callback URL: "
            ).strip()

            code = parse_callback_url(callback_url, state)
            tokens = exchange_code_for_tokens(
                client=client,
                config=self._oauth_config,
                code=code,
                code_verifier=code_verifier,
            )

        self._save_tokens_sync(tokens)
        return tokens

    def _auth_headers(self, tokens: OAuthTokens) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {tokens.access_token}"}
        if tokens.account_id:
            headers["ChatGPT-Account-ID"] = tokens.account_id
        return headers

    def _load_tokens_sync(self) -> OAuthTokens | None:
        return self._token_store.load()

    async def _load_tokens_async(self) -> OAuthTokens | None:
        return await asyncio.to_thread(self._token_store.load)

    def _save_tokens_sync(self, tokens: OAuthTokens) -> None:
        self._token_store.save(tokens)

    async def _save_tokens_async(self, tokens: OAuthTokens) -> None:
        await asyncio.to_thread(self._token_store.save, tokens)

    def _delete_tokens_sync(self) -> None:
        self._token_store.delete()

    async def _delete_tokens_async(self) -> None:
        await asyncio.to_thread(self._token_store.delete)

    def _refresh_and_persist_sync(self, tokens: OAuthTokens) -> OAuthTokens:
        with httpx.Client(timeout=self._timeout) as client:
            self._oauth_config = discover_endpoints(client, self._oauth_config)
            refreshed = refresh_tokens(client, self._oauth_config, tokens)
        self._save_tokens_sync(refreshed)
        return refreshed

    async def _refresh_and_persist_async(self, tokens: OAuthTokens) -> OAuthTokens:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            self._oauth_config = await discover_endpoints_async(
                client, self._oauth_config
            )
            refreshed = await refresh_tokens_async(client, self._oauth_config, tokens)
        await self._save_tokens_async(refreshed)
        return refreshed

    def _ensure_authenticated_sync(self, *, interactive: bool) -> OAuthTokens:
        tokens = self._load_tokens_sync()
        if not tokens:
            if not interactive:
                raise AuthRequiredError("No stored OAuth credentials available")
            tokens = self.login()

        if tokens.is_expired(leeway_seconds=self._refresh_leeway_seconds):
            try:
                tokens = self._refresh_and_persist_sync(tokens)
            except TokenRefreshError as exc:
                self._delete_tokens_sync()
                if not interactive:
                    raise AuthRequiredError(
                        "OAuth refresh failed and interactive login is disabled"
                    ) from exc
                tokens = self.login()

        return tokens

    async def _ensure_authenticated_async(self, *, interactive: bool) -> OAuthTokens:
        tokens = await self._load_tokens_async()
        if not tokens:
            if not interactive:
                raise AuthRequiredError("No stored OAuth credentials available")
            tokens = await asyncio.to_thread(self.login)

        if tokens.is_expired(leeway_seconds=self._refresh_leeway_seconds):
            try:
                tokens = await self._refresh_and_persist_async(tokens)
            except TokenRefreshError as exc:
                await self._delete_tokens_async()
                if not interactive:
                    raise AuthRequiredError(
                        "OAuth refresh failed and interactive login is disabled"
                    ) from exc
                tokens = await asyncio.to_thread(self.login)

        return tokens
