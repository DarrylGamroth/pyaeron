from __future__ import annotations

from .errors import ResourceClosedError

BufferLike = bytes | bytearray | memoryview


def ensure_open(closed: bool, resource_name: str) -> None:
    """Raise when operations are attempted on a closed resource."""
    if closed:
        raise ResourceClosedError(f"{resource_name} is closed")


def coerce_buffer(data: BufferLike) -> memoryview:
    """Normalize buffer-protocol inputs into a contiguous byte memoryview."""
    mv = memoryview(data)
    if mv.format != "B":
        mv = mv.cast("B")
    if not mv.c_contiguous:
        mv = memoryview(bytes(mv))
    return mv
