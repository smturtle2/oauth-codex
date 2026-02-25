from __future__ import annotations

from typing import Any

from .chat import AsyncBetaChat, BetaChat


class Beta:
    def __init__(self, client: Any) -> None:
        self.chat = BetaChat(client)


class AsyncBeta:
    def __init__(self, client: Any) -> None:
        self.chat = AsyncBetaChat(client)
