from __future__ import annotations

import ctypes.util
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, cast

from cffi import FFI  # type: ignore[import-untyped]

from ._generated_cdef import CDEF
from .errors import LibraryLoadError, UnsupportedAeronVersionError

AERON_PUBLICATION_NOT_CONNECTED = -1
AERON_PUBLICATION_BACK_PRESSURED = -2
AERON_PUBLICATION_ADMIN_ACTION = -3
AERON_PUBLICATION_CLOSED = -4
AERON_PUBLICATION_MAX_POSITION_EXCEEDED = -5
AERON_PUBLICATION_ERROR = -6

AERON_CLIENT_ERROR_DRIVER_TIMEOUT = -1000
AERON_CLIENT_ERROR_CLIENT_TIMEOUT = -1001
AERON_CLIENT_ERROR_CONDUCTOR_SERVICE_TIMEOUT = -1002
AERON_CLIENT_ERROR_BUFFER_FULL = -1003

_REQUIRED_SYMBOLS = (
    "aeron_context_init",
    "aeron_context_close",
    "aeron_context_set_dir",
    "aeron_context_get_dir",
    "aeron_init",
    "aeron_start",
    "aeron_close",
    "aeron_is_closed",
    "aeron_main_do_work",
    "aeron_client_id",
    "aeron_next_correlation_id",
    "aeron_async_add_publication",
    "aeron_async_add_publication_poll",
    "aeron_async_add_exclusive_publication",
    "aeron_async_add_exclusive_publication_poll",
    "aeron_async_add_subscription",
    "aeron_async_add_subscription_poll",
    "aeron_async_add_counter",
    "aeron_async_add_counter_poll",
    "aeron_publication_offer",
    "aeron_publication_is_closed",
    "aeron_publication_is_connected",
    "aeron_publication_close",
    "aeron_publication_try_claim",
    "aeron_publication_async_add_destination",
    "aeron_publication_async_remove_destination",
    "aeron_publication_async_destination_poll",
    "aeron_exclusive_publication_offer",
    "aeron_exclusive_publication_try_claim",
    "aeron_exclusive_publication_is_closed",
    "aeron_exclusive_publication_is_connected",
    "aeron_exclusive_publication_close",
    "aeron_exclusive_publication_async_add_destination",
    "aeron_exclusive_publication_async_remove_destination",
    "aeron_exclusive_publication_async_destination_poll",
    "aeron_buffer_claim_commit",
    "aeron_buffer_claim_abort",
    "aeron_subscription_poll",
    "aeron_subscription_is_closed",
    "aeron_subscription_is_connected",
    "aeron_subscription_close",
    "aeron_subscription_async_add_destination",
    "aeron_subscription_async_remove_destination",
    "aeron_subscription_async_destination_poll",
    "aeron_subscription_image_count",
    "aeron_subscription_image_by_session_id",
    "aeron_subscription_image_release",
    "aeron_header_values",
    "aeron_header_position",
    "aeron_image_constants",
    "aeron_image_position",
    "aeron_image_is_closed",
    "aeron_counters_reader",
    "aeron_counters_reader_max_counter_id",
    "aeron_counters_reader_addr",
    "aeron_counter_constants",
    "aeron_counter_addr",
    "aeron_counter_close",
    "aeron_counter_is_closed",
    "aeron_cnc_init",
    "aeron_cnc_constants",
    "aeron_cnc_filename",
    "aeron_cnc_to_driver_heartbeat",
    "aeron_cnc_error_log_read",
    "aeron_cnc_counters_reader",
    "aeron_cnc_close",
    "aeron_errcode",
    "aeron_errmsg",
)

_FILENAME_CANDIDATES = (
    "libaeron.so",
    "libaeron.dylib",
    "aeron.dll",
)


@dataclass(frozen=True, slots=True)
class LoadedAeronCAPI:
    ffi: FFI
    lib: Any
    library_path: str

    def c_string(self, value: str) -> Any:
        return self.ffi.new("char[]", value.encode("utf-8"))

    def string_from_ptr(self, ptr: Any) -> str | None:
        return c_string_to_str(self.ffi, ptr)


def c_string_to_str(ffi: FFI, ptr: Any) -> str | None:
    if ptr == ffi.NULL:
        return None
    return cast(bytes, ffi.string(ptr)).decode("utf-8")


def _build_ffi() -> FFI:
    ffi = FFI()
    ffi.cdef(CDEF)
    return ffi


def _library_candidates() -> list[str]:
    candidates: list[str] = []

    explicit = os.environ.get("AERON_LIBRARY_PATH")
    if explicit:
        candidates.append(explicit)

    for name in ("aeron", "libaeron"):
        resolved = ctypes.util.find_library(name)
        if resolved:
            candidates.append(resolved)

    candidates.extend(_FILENAME_CANDIDATES)
    return candidates


def _load_first_available(ffi: FFI, candidates: list[str]) -> tuple[Any, str]:
    failures: list[str] = []
    for candidate in candidates:
        try:
            lib = ffi.dlopen(candidate)
            return lib, candidate
        except OSError as exc:
            failures.append(f"{candidate}: {exc}")

    detail = "\n".join(failures) if failures else "no candidates generated"
    raise LibraryLoadError(
        "Unable to load libaeron. Set AERON_LIBRARY_PATH to a valid shared library path.\n"
        f"Candidates attempted: {candidates}\n"
        f"Failures:\n{detail}"
    )


def _validate_required_symbols(capi: LoadedAeronCAPI) -> None:
    missing = [symbol for symbol in _REQUIRED_SYMBOLS if not hasattr(capi.lib, symbol)]
    if missing:
        raise UnsupportedAeronVersionError(
            "Loaded libaeron does not expose required symbols for current wrapper feature set: "
            + ", ".join(missing)
        )


@lru_cache(maxsize=1)
def load_libaeron() -> LoadedAeronCAPI:
    """Load and validate the Aeron C client shared library."""

    ffi = _build_ffi()
    lib, path = _load_first_available(ffi, _library_candidates())
    capi = LoadedAeronCAPI(ffi=ffi, lib=lib, library_path=path)
    _validate_required_symbols(capi)
    return capi


def try_load_libaeron() -> LoadedAeronCAPI | None:
    """Best-effort loading helper for tests and optional workflows."""

    try:
        return load_libaeron()
    except (LibraryLoadError, UnsupportedAeronVersionError):
        return None
