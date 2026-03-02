from __future__ import annotations

from typing import Any

from .errors import check_position, check_rc
from .types import ImageConstants
from .util import ensure_open


class Image:
    """Retained subscription image wrapper."""

    def __init__(self, capi: Any, ptr: Any, subscription_ptr: Any) -> None:
        self._capi = capi
        self._ptr = ptr
        self._subscription_ptr = subscription_ptr
        self._released = False

    @property
    def pointer(self) -> Any:
        ensure_open(self._released, "Image")
        return self._ptr

    @property
    def is_open(self) -> bool:
        if self._released:
            return False
        return not bool(self._capi.lib.aeron_image_is_closed(self._ptr))

    @property
    def position(self) -> int:
        ensure_open(self._released, "Image")
        return int(
            check_position(int(self._capi.lib.aeron_image_position(self._ptr)), capi=self._capi)
        )

    @property
    def constants(self) -> ImageConstants:
        ensure_open(self._released, "Image")
        constants = self._capi.ffi.new("aeron_image_constants_t *")
        check_rc(self._capi.lib.aeron_image_constants(self._ptr, constants), capi=self._capi)
        values = constants[0]
        return ImageConstants(
            source_identity=self._capi.string_from_ptr(values.source_identity),
            correlation_id=int(values.correlation_id),
            join_position=int(values.join_position),
            position_bits_to_shift=int(values.position_bits_to_shift),
            term_buffer_length=int(values.term_buffer_length),
            mtu_length=int(values.mtu_length),
            session_id=int(values.session_id),
            initial_term_id=int(values.initial_term_id),
            subscriber_position_id=int(values.subscriber_position_id),
        )

    def release(self) -> None:
        if self._released:
            return
        check_rc(
            self._capi.lib.aeron_subscription_image_release(self._subscription_ptr, self._ptr),
            capi=self._capi,
        )
        self._ptr = self._capi.ffi.NULL
        self._released = True
