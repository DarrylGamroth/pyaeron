from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Header:
    """Callback-scoped Aeron fragment metadata."""

    frame_length: int
    version: int
    flags: int
    type: int
    term_offset: int
    session_id: int
    stream_id: int
    term_id: int
    reserved_value: int
    position: int
    initial_term_id: int
    position_bits_to_shift: int

