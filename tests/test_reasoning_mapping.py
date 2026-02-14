from __future__ import annotations

from conftest import InMemoryTokenStore
from oauth_codex.client import CodexOAuthLLM
from oauth_codex.types import GenerateResult, OAuthTokens


def _llm() -> CodexOAuthLLM:
    store = InMemoryTokenStore(
        OAuthTokens(access_token="a", refresh_token="r", expires_at=9_999_999_999)
    )
    return CodexOAuthLLM(token_store=store)


def test_reasoning_delta_event_mapping() -> None:
    llm = _llm()

    events = llm._map_responses_stream(
        "response.reasoning.delta",
        {"type": "response.reasoning.delta", "delta": "step 1"},
    )

    assert any(e.type == "reasoning_delta" and e.delta == "step 1" for e in events)


def test_reasoning_fields_extracted_into_response() -> None:
    llm = _llm()

    generated = GenerateResult(
        text="ok",
        tool_calls=[],
        finish_reason="stop",
        raw_response={
            "id": "resp_1",
            "reasoning": {
                "summary": "brief",
                "encrypted_content": "enc",
            },
        },
        response_id="resp_1",
    )
    result = llm._generate_result_to_response(result=generated, previous_response_id=None)

    assert result.reasoning_summary == "brief"
    assert result.encrypted_reasoning_content == "enc"
    assert result.reasoning_items
