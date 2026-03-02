from __future__ import annotations

from typing import Any

from .errors import check_rc
from .types import CounterConstants
from .util import ensure_open


class Counter:
    """Client-owned Aeron counter wrapper."""

    def __init__(self, capi: Any, ptr: Any) -> None:
        self._capi = capi
        self._ptr = ptr
        self._closed = False

    @property
    def pointer(self) -> Any:
        ensure_open(self._closed, "Counter")
        return self._ptr

    @property
    def is_open(self) -> bool:
        if self._closed:
            return False
        return not bool(self._capi.lib.aeron_counter_is_closed(self._ptr))

    @property
    def constants(self) -> CounterConstants:
        ensure_open(self._closed, "Counter")
        constants = self._capi.ffi.new("aeron_counter_constants_t *")
        check_rc(self._capi.lib.aeron_counter_constants(self._ptr, constants), capi=self._capi)
        return CounterConstants(
            registration_id=int(constants[0].registration_id),
            counter_id=int(constants[0].counter_id),
        )

    @property
    def counter_id(self) -> int:
        return self.constants.counter_id

    @property
    def value(self) -> int:
        ensure_open(self._closed, "Counter")
        addr = self._capi.lib.aeron_counter_addr(self._ptr)
        return int(addr[0])

    @value.setter
    def value(self, value: int) -> None:
        ensure_open(self._closed, "Counter")
        addr = self._capi.lib.aeron_counter_addr(self._ptr)
        addr[0] = int(value)

    def close(self) -> None:
        if self._closed:
            return
        check_rc(
            self._capi.lib.aeron_counter_close(self._ptr, self._capi.ffi.NULL, self._capi.ffi.NULL),
            capi=self._capi,
        )
        self._ptr = self._capi.ffi.NULL
        self._closed = True
