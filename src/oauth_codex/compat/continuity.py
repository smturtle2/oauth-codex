from __future__ import annotations

from ..compat_store import LocalCompatStore


def get_continuity(store: LocalCompatStore, response_id: str) -> dict[str, object]:
    return store.get_response_continuity(response_id)


def upsert_continuity(
    store: LocalCompatStore,
    *,
    response_id: str,
    model: str,
    continuation_input: list[dict[str, object]],
    previous_response_id: str | None,
) -> dict[str, object]:
    return store.upsert_response_continuity(
        response_id=response_id,
        model=model,
        continuation_input=continuation_input,
        previous_response_id=previous_response_id,
    )
