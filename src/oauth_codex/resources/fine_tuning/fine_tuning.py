from __future__ import annotations

from ..._resource import AsyncAPIResource, SyncAPIResource
from .alpha.alpha import Alpha, AsyncAlpha
from .checkpoints.checkpoints import AsyncCheckpoints, Checkpoints
from .jobs.jobs import AsyncJobs, Jobs


class FineTuning(SyncAPIResource):
    @property
    def jobs(self) -> Jobs:
        return Jobs(self._client)

    @property
    def checkpoints(self) -> Checkpoints:
        return Checkpoints(self._client)

    @property
    def alpha(self) -> Alpha:
        return Alpha(self._client)


class AsyncFineTuning(AsyncAPIResource):
    @property
    def jobs(self) -> AsyncJobs:
        return AsyncJobs(self._client)

    @property
    def checkpoints(self) -> AsyncCheckpoints:
        return AsyncCheckpoints(self._client)

    @property
    def alpha(self) -> AsyncAlpha:
        return AsyncAlpha(self._client)
