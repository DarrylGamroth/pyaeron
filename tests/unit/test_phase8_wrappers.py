from __future__ import annotations

from cffi import FFI

from pyaeron.buffer_claim import BufferClaim
from pyaeron.types import CncConstants, CounterConstants, ErrorLogObservation, ImageConstants


class _FakeLib:
    def aeron_buffer_claim_commit(self, _claim_ptr):
        return 0

    def aeron_buffer_claim_abort(self, _claim_ptr):
        return 0


class _FakeCapi:
    def __init__(self) -> None:
        self.ffi = FFI()
        self.ffi.cdef(
            "typedef unsigned char uint8_t;"
            "typedef unsigned long size_t;"
            "typedef struct aeron_buffer_claim_stct"
            "{ uint8_t *frame_header; uint8_t *data; size_t length; } aeron_buffer_claim_t;"
        )
        self.lib = _FakeLib()


def test_buffer_claim_write_and_commit() -> None:
    capi = _FakeCapi()
    claim = capi.ffi.new("aeron_buffer_claim_t *")
    backing = bytearray(8)
    claim.data = capi.ffi.from_buffer(backing)
    claim.length = len(backing)

    wrapped = BufferClaim(capi, claim, position=42)
    wrapped.write(b"abc")
    wrapped.commit()

    assert bytes(backing[:3]) == b"abc"
    assert wrapped.position == 42
    assert wrapped.is_finalized is True


def test_phase8_dataclasses_construct() -> None:
    assert CounterConstants(registration_id=1, counter_id=2).counter_id == 2
    assert ImageConstants(None, 1, 2, 3, 4, 5, 6, 7, 8).session_id == 6
    assert CncConstants(1, 2, 3, 4, 5, 6, 7, 8, 9, 10).pid == 9
    assert ErrorLogObservation(1, 2, 3, "err").error == "err"
