from __future__ import annotations

import struct
import sys
import time
from typing import Any

from .errors import TimedOutError, check_rc
from .handlers import FragmentCallbackAdapter, FragmentHandler
from .image import Image
from .types import Header
from .util import ensure_open

_ENDIAN = "<" if sys.byteorder == "little" else ">"
_HEADER_VALUES_FMT = f"{_ENDIAN}i b B h i i i i q i Q"


def _decode_header_values(
    raw: bytes,
) -> tuple[int, int, int, int, int, int, int, int, int, int, int]:
    return struct.unpack(_HEADER_VALUES_FMT, raw)


class Subscription:
    """High-level subscription wrapper backed by a real Aeron subscription pointer."""

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
        self._active_fragment_callback: Any = None

    @property
    def pointer(self) -> Any:
        ensure_open(self._closed, "Subscription")
        return self._ptr

    def close(self) -> None:
        if self._closed:
            return
        check_rc(
            self._capi.lib.aeron_subscription_close(
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
        return not bool(self._capi.lib.aeron_subscription_is_closed(self._ptr))

    @property
    def is_connected(self) -> bool:
        ensure_open(self._closed, "Subscription")
        return bool(self._capi.lib.aeron_subscription_is_connected(self._ptr))

    @property
    def image_count(self) -> int:
        ensure_open(self._closed, "Subscription")
        return int(
            check_rc(self._capi.lib.aeron_subscription_image_count(self._ptr), capi=self._capi)
        )

    def image_by_session_id(self, session_id: int) -> Image | None:
        ensure_open(self._closed, "Subscription")
        image_ptr = self._capi.lib.aeron_subscription_image_by_session_id(self._ptr, session_id)
        if image_ptr == self._capi.ffi.NULL:
            return None
        return Image(self._capi, image_ptr, self._ptr)

    def poll(self, handler: FragmentHandler, *, fragment_limit: int = 10) -> int:
        ensure_open(self._closed, "Subscription")
        if fragment_limit <= 0:
            raise ValueError("fragment_limit must be greater than zero")

        pending_exc: BaseException | None = None

        @self._capi.ffi.callback("void(void *, const uint8_t *, size_t, aeron_header_t *)")
        def on_fragment(_clientd: Any, buffer: Any, length: int, header_ptr: Any) -> None:
            nonlocal pending_exc
            if pending_exc is not None:
                return

            try:
                values = self._capi.ffi.new("aeron_header_values_t *")
                check_rc(self._capi.lib.aeron_header_values(header_ptr, values), capi=self._capi)

                position = int(self._capi.lib.aeron_header_position(header_ptr))
                if position < 0:
                    check_rc(-1, capi=self._capi)

                # Support both historic compact layout (`data[44]`) and current
                # expanded frame layout from aeron_header_values_t.
                if hasattr(values[0], "data"):
                    raw = bytes(self._capi.ffi.buffer(values[0].data, 44))
                    (
                        frame_length,
                        version,
                        flags,
                        frame_type,
                        term_offset,
                        session_id,
                        stream_id,
                        term_id,
                        reserved_value,
                        initial_term_id,
                        position_bits_to_shift,
                    ) = _decode_header_values(raw)
                else:
                    frame = values[0].frame
                    frame_length = int(frame.frame_length)
                    version = int(frame.version)
                    flags = int(frame.flags)
                    frame_type = int(frame.type)
                    term_offset = int(frame.term_offset)
                    session_id = int(frame.session_id)
                    stream_id = int(frame.stream_id)
                    term_id = int(frame.term_id)
                    reserved_value = int(frame.reserved_value)
                    initial_term_id = int(values[0].initial_term_id)
                    position_bits_to_shift = int(values[0].position_bits_to_shift)

                header = Header(
                    frame_length=frame_length,
                    version=version,
                    flags=flags,
                    type=frame_type,
                    term_offset=term_offset,
                    session_id=session_id,
                    stream_id=stream_id,
                    term_id=term_id,
                    reserved_value=reserved_value,
                    position=position,
                    initial_term_id=initial_term_id,
                    position_bits_to_shift=position_bits_to_shift,
                )

                fragment = memoryview(self._capi.ffi.buffer(buffer, length))
                handler(fragment, header)
            except BaseException as exc:  # noqa: BLE001
                pending_exc = exc

        # Retain callback reference for the lifetime of the native poll call.
        self._active_fragment_callback = on_fragment
        try:
            num_fragments = int(
                check_rc(
                    self._capi.lib.aeron_subscription_poll(
                        self._ptr,
                        on_fragment,
                        self._capi.ffi.NULL,
                        fragment_limit,
                    ),
                    capi=self._capi,
                )
            )
        finally:
            self._active_fragment_callback = None

        if pending_exc is not None:
            raise pending_exc

        return num_fragments

    def poll_until(
        self,
        handler: FragmentHandler,
        *,
        fragment_limit: int = 10,
        min_fragments: int = 1,
        timeout: float = 5.0,
        poll_interval: float = 0.001,
        copy_payload: bool = False,
    ) -> int:
        """Poll repeatedly until `min_fragments` are consumed or timeout is reached."""
        if min_fragments <= 0:
            raise ValueError("min_fragments must be greater than zero")

        adapter = FragmentCallbackAdapter(handler, copy_payload=copy_payload)
        deadline = time.monotonic() + timeout
        total = 0
        while total < min_fragments:
            total += self.poll(adapter, fragment_limit=fragment_limit)
            if total >= min_fragments:
                return total
            if time.monotonic() >= deadline:
                raise TimedOutError(
                    "Timed out polling subscription "
                    f"channel={self.channel!r} stream_id={self.stream_id}"
                )
            if poll_interval > 0:
                time.sleep(poll_interval)
        return total

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
        ensure_open(self._closed, "Subscription")
        async_ptr = self._capi.ffi.new("aeron_async_destination_t **")
        call = (
            self._capi.lib.aeron_subscription_async_add_destination
            if is_add
            else self._capi.lib.aeron_subscription_async_remove_destination
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
                    self._capi.lib.aeron_subscription_async_destination_poll(async_ptr[0]),
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
