from __future__ import annotations

from typing import Any


class CountersReader:
    """Read-only view over Aeron counters."""

    def __init__(self, capi: Any, ptr: Any) -> None:
        self._capi = capi
        self._ptr = ptr

    @property
    def pointer(self) -> Any:
        return self._ptr

    @property
    def max_counter_id(self) -> int:
        return int(self._capi.lib.aeron_counters_reader_max_counter_id(self._ptr))

    def value(self, counter_id: int) -> int:
        addr = self._capi.lib.aeron_counters_reader_addr(self._ptr, counter_id)
        return int(addr[0])
