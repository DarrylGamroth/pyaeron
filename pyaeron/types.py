from __future__ import annotations

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


@dataclass(frozen=True, slots=True)
class CounterConstants:
    registration_id: int
    counter_id: int


@dataclass(frozen=True, slots=True)
class ImageConstants:
    source_identity: str | None
    correlation_id: int
    join_position: int
    position_bits_to_shift: int
    term_buffer_length: int
    mtu_length: int
    session_id: int
    initial_term_id: int
    subscriber_position_id: int


@dataclass(frozen=True, slots=True)
class CncConstants:
    cnc_version: int
    to_driver_buffer_length: int
    to_clients_buffer_length: int
    counter_metadata_buffer_length: int
    counter_values_buffer_length: int
    error_log_buffer_length: int
    client_liveness_timeout: int
    start_timestamp: int
    pid: int
    file_page_size: int


@dataclass(frozen=True, slots=True)
class ErrorLogObservation:
    observation_count: int
    first_observation_timestamp: int
    last_observation_timestamp: int
    error: str
