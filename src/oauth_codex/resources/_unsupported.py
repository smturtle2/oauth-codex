from __future__ import annotations

from typing import Any

from .._exceptions import NotSupportedError


def unsupported(feature: str) -> NotSupportedError:
    return NotSupportedError(
        f"{feature} is not supported in oauth-codex with the current backend",
        code="not_supported",
    )


def raise_unsupported(feature: str) -> None:
    raise unsupported(feature)


def unsupported_sync(*_: Any, feature: str = "operation", **__: Any) -> None:
    raise_unsupported(feature)


async def unsupported_async(*_: Any, feature: str = "operation", **__: Any) -> None:
    raise_unsupported(feature)
