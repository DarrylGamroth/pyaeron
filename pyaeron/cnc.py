from __future__ import annotations

from typing import Any

from ._capi import load_libaeron
from .counters_reader import CountersReader
from .errors import check_rc
from .types import CncConstants, ErrorLogObservation
from .util import ensure_open


class CnC:
    """Wrapper for Aeron command-and-control (cnc.dat) monitoring APIs."""

    def __init__(self, aeron_dir: str, *, timeout_ms: int = 5_000) -> None:
        self._capi = load_libaeron()
        ptr = self._capi.ffi.new("aeron_cnc_t **")
        check_rc(
            self._capi.lib.aeron_cnc_init(ptr, self._capi.c_string(aeron_dir), timeout_ms),
            capi=self._capi,
        )
        self._ptr = ptr[0]
        self._closed = False

    @property
    def pointer(self) -> Any:
        ensure_open(self._closed, "CnC")
        return self._ptr

    @property
    def filename(self) -> str | None:
        ensure_open(self._closed, "CnC")
        return self._capi.string_from_ptr(self._capi.lib.aeron_cnc_filename(self._ptr))

    @property
    def to_driver_heartbeat_ms(self) -> int:
        ensure_open(self._closed, "CnC")
        return int(self._capi.lib.aeron_cnc_to_driver_heartbeat(self._ptr))

    @property
    def constants(self) -> CncConstants:
        ensure_open(self._closed, "CnC")
        constants = self._capi.ffi.new("aeron_cnc_constants_t *")
        check_rc(self._capi.lib.aeron_cnc_constants(self._ptr, constants), capi=self._capi)
        values = constants[0]
        return CncConstants(
            cnc_version=int(values.cnc_version),
            to_driver_buffer_length=int(values.to_driver_buffer_length),
            to_clients_buffer_length=int(values.to_clients_buffer_length),
            counter_metadata_buffer_length=int(values.counter_metadata_buffer_length),
            counter_values_buffer_length=int(values.counter_values_buffer_length),
            error_log_buffer_length=int(values.error_log_buffer_length),
            client_liveness_timeout=int(values.client_liveness_timeout),
            start_timestamp=int(values.start_timestamp),
            pid=int(values.pid),
            file_page_size=int(values.file_page_size),
        )

    @property
    def counters_reader(self) -> CountersReader:
        ensure_open(self._closed, "CnC")
        return CountersReader(self._capi, self._capi.lib.aeron_cnc_counters_reader(self._ptr))

    def read_error_log(self, *, since_timestamp: int = 0) -> list[ErrorLogObservation]:
        ensure_open(self._closed, "CnC")
        entries: list[ErrorLogObservation] = []

        @self._capi.ffi.callback("void(int32_t, int64_t, int64_t, const char *, size_t, void *)")
        def on_error(
            observation_count: int,
            first_observation_timestamp: int,
            last_observation_timestamp: int,
            error_ptr: Any,
            error_length: int,
            _clientd: Any,
        ) -> None:
            if error_ptr == self._capi.ffi.NULL:
                message = ""
            else:
                message = bytes(self._capi.ffi.buffer(error_ptr, error_length)).decode(
                    "utf-8", errors="replace"
                )
            entries.append(
                ErrorLogObservation(
                    observation_count=int(observation_count),
                    first_observation_timestamp=int(first_observation_timestamp),
                    last_observation_timestamp=int(last_observation_timestamp),
                    error=message,
                )
            )

        self._capi.lib.aeron_cnc_error_log_read(
            self._ptr, on_error, self._capi.ffi.NULL, since_timestamp
        )
        return entries

    def close(self) -> None:
        if self._closed:
            return
        self._capi.lib.aeron_cnc_close(self._ptr)
        self._ptr = self._capi.ffi.NULL
        self._closed = True

    def __enter__(self) -> CnC:
        ensure_open(self._closed, "CnC")
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()
