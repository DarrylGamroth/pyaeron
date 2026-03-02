from __future__ import annotations

import struct
import sys
from typing import Any

from .errors import check_rc
from .handlers import FragmentHandler
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

    def __init__(self, capi: Any, ptr: Any, channel: str, stream_id: int) -> None:
        self._capi = capi
        self._ptr = ptr
        self.channel = channel
        self.stream_id = stream_id
        self._closed = False

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

        if pending_exc is not None:
            raise pending_exc

        return num_fragments
