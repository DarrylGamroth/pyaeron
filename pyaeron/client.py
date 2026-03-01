from __future__ import annotations

from types import TracebackType

from .context import Context
from .publication import Publication
from .subscription import Subscription
from .util import ensure_open


class Client:
    """High-level client lifecycle wrapper.

    Phase 1 provides deterministic lifecycle behavior and API shape.
    """

    def __init__(self, context: Context) -> None:
        if context.closed:
            raise ValueError("Context is closed")
        context._mark_bound()
        self._context = context
        self._closed = False
        self._next_correlation = 1

    def __enter__(self) -> Client:
        ensure_open(self._closed, "Client")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    @property
    def is_open(self) -> bool:
        return not self._closed

    def close(self) -> None:
        self._closed = True

    def do_work(self) -> int:
        ensure_open(self._closed, "Client")
        return 0

    def client_id(self) -> int:
        ensure_open(self._closed, "Client")
        return 1

    def next_correlation_id(self) -> int:
        ensure_open(self._closed, "Client")
        value = self._next_correlation
        self._next_correlation += 1
        return value

    def add_publication(
        self,
        channel: str,
        stream_id: int,
        *,
        timeout: float | None = 10.0,
        poll_interval: float = 0.001,
    ) -> Publication:
        ensure_open(self._closed, "Client")
        del timeout, poll_interval
        return Publication(channel=channel, stream_id=stream_id)

    def add_subscription(
        self,
        channel: str,
        stream_id: int,
        *,
        timeout: float | None = 10.0,
        poll_interval: float = 0.001,
    ) -> Subscription:
        ensure_open(self._closed, "Client")
        del timeout, poll_interval
        return Subscription(channel=channel, stream_id=stream_id)
