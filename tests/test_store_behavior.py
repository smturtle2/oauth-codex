from __future__ import annotations

import pytest

from conftest import InMemoryTokenStore
from oauth_codex import OAuthCodexClient, ParameterValidationError
from oauth_codex.types import OAuthTokens, StreamEvent


def _client(store_behavior: str = "auto_disable") -> OAuthCodexClient:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    return OAuthCodexClient(token_store=store, store_behavior=store_behavior)  # type: ignore[arg-type]


def test_store_auto_disable(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client("auto_disable")
    captured: dict[str, object] = {}

    def fake_sse(**kwargs):
        captured["payload"] = kwargs["payload"]
        yield StreamEvent(type="text_delta", delta="ok")
        yield StreamEvent(type="done")

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fake_sse)

    with pytest.warns(RuntimeWarning):
        client.responses.create(model="gpt-5.3-codex", input="hi", store=True)

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["store"] is False


def test_store_error_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client("error")

    def fake_sse(**kwargs):
        _ = kwargs
        yield StreamEvent(type="text_delta", delta="ok")
        yield StreamEvent(type="done")

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fake_sse)

    with pytest.raises(ParameterValidationError):
        client.responses.create(model="gpt-5.3-codex", input="hi", store=True)


def test_store_passthrough_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client("passthrough")
    captured: dict[str, object] = {}

    def fake_sse(**kwargs):
        captured["payload"] = kwargs["payload"]
        yield StreamEvent(type="text_delta", delta="ok")
        yield StreamEvent(type="done")

    monkeypatch.setattr(client._engine, "_stream_sse_sync", fake_sse)

    client.responses.create(model="gpt-5.3-codex", input="hi", store=True)

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["store"] is True
