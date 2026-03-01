from __future__ import annotations

from .errors import AeronError
from .handlers import FragmentHandler
from .util import ensure_open


class Subscription:
    """High-level subscription wrapper.

    Phase 1 intentionally provides lifecycle/API shape only.
    """

    def __init__(self, channel: str, stream_id: int) -> None:
        self.channel = channel
        self.stream_id = stream_id
        self._closed = False

    def close(self) -> None:
        self._closed = True

    @property
    def is_open(self) -> bool:
        return not self._closed

    @property
    def is_connected(self) -> bool:
        ensure_open(self._closed, "Subscription")
        return False

    def poll(self, handler: FragmentHandler, *, fragment_limit: int = 10) -> int:
        ensure_open(self._closed, "Subscription")
        if fragment_limit <= 0:
            raise ValueError("fragment_limit must be greater than zero")
        del handler  # API placeholder for Phase 5.
        raise AeronError("Subscription.poll is not implemented until Phase 5")

