from __future__ import annotations

import warnings

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import OAuthCodexClient, ParameterValidationError
from oauth_codex.types import OAuthTokens, StreamEvent


def _client(validation_mode: str = "warn") -> OAuthCodexClient:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    return OAuthCodexClient(token_store=store, validation_mode=validation_mode)  # type: ignore[arg-type]


def test_validation_mode_warn_emits_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client("warn")

    def fake_sse(**kwargs):
        _ = kwargs
        yield StreamEvent(type="text_delta", delta="ok")
        yield StreamEvent(type="done")

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fake_sse)

    with pytest.warns(RuntimeWarning):
        client.responses.create(
            model="gpt-5.3-codex",
            input="hi",
            service_tier="priority",
            unsupported_field=True,
        )


def test_validation_mode_error_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client("error")

    def fake_sse(**kwargs):
        _ = kwargs
        yield StreamEvent(type="text_delta", delta="ok")
        yield StreamEvent(type="done")

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fake_sse)

    with pytest.raises(ParameterValidationError):
        client.responses.create(model="gpt-5.3-codex", input="hi", service_tier="priority")


def test_validation_mode_ignore_suppresses_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client("ignore")

    def fake_sse(**kwargs):
        _ = kwargs
        yield StreamEvent(type="text_delta", delta="ok")
        yield StreamEvent(type="done")

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fake_sse)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        client.responses.create(
            model="gpt-5.3-codex",
            input="hi",
            service_tier="priority",
            unsupported_field=True,
        )

    assert not captured
