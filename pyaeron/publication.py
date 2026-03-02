from __future__ import annotations

import time
from typing import Any

from .errors import (
    AdminActionError,
    BackPressuredError,
    NotConnectedError,
    check_position,
    check_rc,
)
from .util import ensure_open

BufferLike = bytes | bytearray | memoryview


def _coerce_buffer(data: BufferLike) -> memoryview:
    mv = memoryview(data)
    if mv.format != "B":
        mv = mv.cast("B")
    if not mv.c_contiguous:
        mv = memoryview(bytes(mv))
    return mv


class Publication:
    """High-level publication wrapper backed by a real Aeron publication pointer."""

    def __init__(self, capi: Any, ptr: Any, channel: str, stream_id: int) -> None:
        self._capi = capi
        self._ptr = ptr
        self.channel = channel
        self.stream_id = stream_id
        self._closed = False

    @property
    def pointer(self) -> Any:
        ensure_open(self._closed, "Publication")
        return self._ptr

    def close(self) -> None:
        if self._closed:
            return
        check_rc(
            self._capi.lib.aeron_publication_close(
                self._ptr,
                self._capi.ffi.NULL,
                self._capi.ffi.NULL,
            ),
            capi=self._capi,
        )
        self._ptr = self._capi.ffi.NULL
        self._closed = True

    @property
    def is_open(self) -> bool:
        if self._closed:
            return False
        return not bool(self._capi.lib.aeron_publication_is_closed(self._ptr))

    @property
    def is_connected(self) -> bool:
        ensure_open(self._closed, "Publication")
        return bool(self._capi.lib.aeron_publication_is_connected(self._ptr))

    def offer(self, data: BufferLike) -> int:
        ensure_open(self._closed, "Publication")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("offer() expects bytes, bytearray, or memoryview")

        mv = _coerce_buffer(data)
        rc = self._capi.lib.aeron_publication_offer(
            self._ptr,
            self._capi.ffi.from_buffer(mv),
            len(mv),
            self._capi.ffi.NULL,
            self._capi.ffi.NULL,
        )
        return int(check_position(int(rc), capi=self._capi))

    def offer_with_retry(
        self,
        data: BufferLike,
        *,
        timeout: float = 5.0,
        poll_interval: float = 0.0005,
    ) -> int:
        """Offer with retry on transient publication states.

        Retries when Aeron indicates `NOT_CONNECTED`, `BACK_PRESSURED`, or `ADMIN_ACTION`.
        Raises the original typed exception for non-transient failures or on timeout.
        """
        deadline = time.monotonic() + timeout
        while True:
            try:
                return self.offer(data)
            except (NotConnectedError, BackPressuredError, AdminActionError):
                if time.monotonic() >= deadline:
                    raise
                if poll_interval > 0:
                    time.sleep(poll_interval)
