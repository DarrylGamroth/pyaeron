from __future__ import annotations

from typing import Any

from .errors import check_rc

BufferLike = bytes | bytearray | memoryview


class BufferClaim:
    """Writable claim returned by publication `try_claim` calls."""

    def __init__(self, capi: Any, claim_ptr: Any, position: int) -> None:
        self._capi = capi
        self._claim_ptr = claim_ptr
        self.position = position
        self._finalized = False

    @property
    def is_finalized(self) -> bool:
        return self._finalized

    @property
    def length(self) -> int:
        return int(self._claim_ptr.length)

    @property
    def data(self) -> memoryview:
        return memoryview(self._capi.ffi.buffer(self._claim_ptr.data, self.length))

    def write(self, payload: BufferLike, *, offset: int = 0) -> None:
        if self._finalized:
            raise RuntimeError("BufferClaim has already been finalized")

        mv = memoryview(payload)
        if mv.format != "B":
            mv = mv.cast("B")

        end = offset + len(mv)
        if offset < 0 or end > self.length:
            raise ValueError("payload does not fit in claim buffer")

        self.data[offset:end] = mv

    def commit(self) -> None:
        if self._finalized:
            return
        check_rc(self._capi.lib.aeron_buffer_claim_commit(self._claim_ptr), capi=self._capi)
        self._finalized = True

    def abort(self) -> None:
        if self._finalized:
            return
        check_rc(self._capi.lib.aeron_buffer_claim_abort(self._claim_ptr), capi=self._capi)
        self._finalized = True

    def __enter__(self) -> BufferClaim:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._finalized:
            return
        if exc is None:
            self.commit()
        else:
            self.abort()
