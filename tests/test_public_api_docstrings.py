from __future__ import annotations

import inspect

import oauth_codex
import oauth_codex.core_types as core_types
from conftest import InMemoryTokenStore
from oauth_codex.core_types import OAuthTokens


def test_client_classes_expose_modern_api_only() -> None:
    assert inspect.isclass(oauth_codex.Client)
    assert inspect.isclass(oauth_codex.AsyncClient)
    assert not hasattr(oauth_codex.Client, "generate")
    assert not hasattr(oauth_codex.Client, "stream")
    assert not hasattr(oauth_codex.AsyncClient, "agenerate")
    assert not hasattr(oauth_codex.AsyncClient, "astream")


def test_client_exposes_chat_and_responses_resources() -> None:
    client = oauth_codex.Client(
        token_store=InMemoryTokenStore(
            OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
        )
    )

    chat = getattr(client, "chat")
    completions = getattr(chat, "completions")
    responses = getattr(client, "responses")

    assert hasattr(client, "chat")
    assert hasattr(chat, "completions")
    assert callable(getattr(completions, "create"))
    assert hasattr(client, "responses")
    assert callable(getattr(responses, "create"))


def test_root_exported_exceptions_have_docstrings() -> None:
    for name in oauth_codex.__all__:
        exported = getattr(oauth_codex, name)
        if inspect.isclass(exported) and issubclass(exported, Exception):
            assert inspect.getdoc(exported), f"missing docstring for {name}"


def test_core_types_module_doc_mentions_list_message() -> None:
    doc = inspect.getdoc(core_types)
    assert doc is not None
    assert "Message" in doc
    assert "listMessage" in doc
