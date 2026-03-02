from __future__ import annotations

import time
from typing import Any

from .buffer_claim import BufferClaim
from .errors import (
    AdminActionError,
    BackPressuredError,
    NotConnectedError,
    TimedOutError,
    check_position,
    check_rc,
)
from .util import BufferLike, coerce_buffer, ensure_open


class ExclusivePublication:
    """High-level wrapper for Aeron exclusive publications."""

    def __init__(
        self,
        capi: Any,
        ptr: Any,
        client_ptr: Any,
        channel: str,
        stream_id: int,
    ) -> None:
        self._capi = capi
        self._ptr = ptr
        self._client_ptr = client_ptr
        self.channel = channel
        self.stream_id = stream_id
        self._closed = False

    @property
    def pointer(self) -> Any:
        ensure_open(self._closed, "ExclusivePublication")
        return self._ptr

    @property
    def is_open(self) -> bool:
        if self._closed:
            return False
        return not bool(self._capi.lib.aeron_exclusive_publication_is_closed(self._ptr))

    @property
    def is_connected(self) -> bool:
        ensure_open(self._closed, "ExclusivePublication")
        return bool(self._capi.lib.aeron_exclusive_publication_is_connected(self._ptr))

    def close(self) -> None:
        if self._closed:
            return
        check_rc(
            self._capi.lib.aeron_exclusive_publication_close(
                self._ptr,
                self._capi.ffi.NULL,
                self._capi.ffi.NULL,
            ),
            capi=self._capi,
        )
        self._ptr = self._capi.ffi.NULL
        self._closed = True

    def offer(self, data: BufferLike) -> int:
        ensure_open(self._closed, "ExclusivePublication")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("offer() expects bytes, bytearray, or memoryview")

        mv = coerce_buffer(data)
        rc = self._capi.lib.aeron_exclusive_publication_offer(
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
        deadline = time.monotonic() + timeout
        while True:
            try:
                return self.offer(data)
            except (NotConnectedError, BackPressuredError, AdminActionError):
                if time.monotonic() >= deadline:
                    raise
                if poll_interval > 0:
                    time.sleep(poll_interval)

    def try_claim(self, length: int) -> BufferClaim:
        ensure_open(self._closed, "ExclusivePublication")
        if length <= 0:
            raise ValueError("length must be greater than zero")

        claim_ptr = self._capi.ffi.new("aeron_buffer_claim_t *")
        pos = self._capi.lib.aeron_exclusive_publication_try_claim(self._ptr, length, claim_ptr)
        return BufferClaim(self._capi, claim_ptr, int(check_position(int(pos), capi=self._capi)))

    def add_destination(
        self,
        uri: str,
        *,
        timeout: float | None = 10.0,
        poll_interval: float = 0.001,
    ) -> None:
        self._update_destination(uri, is_add=True, timeout=timeout, poll_interval=poll_interval)

    def remove_destination(
        self,
        uri: str,
        *,
        timeout: float | None = 10.0,
        poll_interval: float = 0.001,
    ) -> None:
        self._update_destination(uri, is_add=False, timeout=timeout, poll_interval=poll_interval)

    def _update_destination(
        self,
        uri: str,
        *,
        is_add: bool,
        timeout: float | None,
        poll_interval: float,
    ) -> None:
        ensure_open(self._closed, "ExclusivePublication")
        async_ptr = self._capi.ffi.new("aeron_async_destination_t **")
        call = (
            self._capi.lib.aeron_exclusive_publication_async_add_destination
            if is_add
            else self._capi.lib.aeron_exclusive_publication_async_remove_destination
        )
        check_rc(
            call(
                async_ptr,
                self._client_ptr,
                self._ptr,
                self._capi.c_string(uri),
            ),
            capi=self._capi,
        )

        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            rc = int(
                check_rc(
                    self._capi.lib.aeron_exclusive_publication_async_destination_poll(async_ptr[0]),
                    capi=self._capi,
                )
            )
            if rc == 1:
                return
            if deadline is not None and time.monotonic() >= deadline:
                raise TimedOutError(
                    f"Timed out waiting to {'add' if is_add else 'remove'} destination: {uri!r}"
                )
            if poll_interval > 0:
                time.sleep(poll_interval)
