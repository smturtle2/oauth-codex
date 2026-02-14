from __future__ import annotations

from typing import Any

from .._resource import AsyncAPIResource, SyncAPIResource
from ._unsupported import raise_unsupported

class Webhooks(SyncAPIResource):
    def unwrap(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('webhooks.Webhooks.unwrap')

    def verify_signature(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('webhooks.Webhooks.verify_signature')

class AsyncWebhooks(AsyncAPIResource):
    async def unwrap(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('webhooks.AsyncWebhooks.unwrap')

    async def verify_signature(self, *args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
        raise_unsupported('webhooks.AsyncWebhooks.verify_signature')
