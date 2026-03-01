from __future__ import annotations

from .errors import AeronError
from .util import ensure_open

BufferLike = bytes | bytearray | memoryview


class Publication:
    """High-level publication wrapper.

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
        ensure_open(self._closed, "Publication")
        return False

    def offer(self, data: BufferLike) -> int:
        ensure_open(self._closed, "Publication")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("offer() expects bytes, bytearray, or memoryview")
        raise AeronError("Publication.offer is not implemented until Phase 5")

