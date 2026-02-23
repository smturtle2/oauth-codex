from __future__ import annotations

import inspect

import oauth_codex
import oauth_codex.core_types as core_types


def test_client_class_docstring_exists() -> None:
    doc = inspect.getdoc(oauth_codex.Client)
    assert doc is not None
    assert "default_model" in doc
    assert "max_tool_rounds" in doc


def test_generate_docstring_includes_key_sections() -> None:
    doc = inspect.getdoc(oauth_codex.Client.generate)
    assert doc is not None
    for keyword in ("messages", "tools", "output_schema", "Returns", "Raises"):
        assert keyword in doc


def test_agenerate_docstring_includes_key_sections() -> None:
    doc = inspect.getdoc(oauth_codex.Client.agenerate)
    assert doc is not None
    for keyword in ("messages", "tools", "output_schema", "Returns", "Raises"):
        assert keyword in doc


def test_stream_docstring_includes_streaming_context() -> None:
    doc = inspect.getdoc(oauth_codex.Client.stream)
    assert doc is not None
    for keyword in ("messages", "tools", "output_schema", "Yields", "Raises"):
        assert keyword in doc


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
