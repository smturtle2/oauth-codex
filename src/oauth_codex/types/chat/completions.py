from __future__ import annotations

from typing import Any

from oauth_codex._models import BaseModel


class ChatCompletionMessage(BaseModel):
    role: str
    content: str | None = None
    refusal: str | None = None


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatCompletionMessage
    finish_reason: str | None = None


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletion(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage | None = None
    system_fingerprint: str | None = None
    raw_response: dict[str, Any] | None = None
