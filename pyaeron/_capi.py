from __future__ import annotations

import ctypes.util
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, cast

from cffi import FFI  # type: ignore[import-untyped]

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

_CDEF = r"""
typedef _Bool bool;
typedef long int ssize_t;
typedef unsigned char uint8_t;
typedef signed short int16_t;
typedef unsigned short uint16_t;
typedef signed int int32_t;
typedef unsigned int uint32_t;
typedef signed long int int64_t;
typedef unsigned long int uint64_t;
typedef unsigned long size_t;

typedef struct aeron_context_stct aeron_context_t;
typedef struct aeron_stct aeron_t;
typedef struct aeron_publication_stct aeron_publication_t;
typedef struct aeron_subscription_stct aeron_subscription_t;
typedef struct aeron_header_stct aeron_header_t;
typedef struct aeron_client_registering_resource_stct aeron_async_add_publication_t;
typedef struct aeron_client_registering_resource_stct aeron_async_add_subscription_t;

typedef int64_t (*aeron_reserved_value_supplier_t)(
    void *clientd, uint8_t *buffer, size_t frame_length);
typedef void (*aeron_fragment_handler_t)(
    void *clientd, const uint8_t *buffer, size_t length, aeron_header_t *header);

int aeron_context_init(aeron_context_t **context);
int aeron_context_close(aeron_context_t *context);
int aeron_context_set_dir(aeron_context_t *context, const char *value);
const char *aeron_context_get_dir(aeron_context_t *context);
int aeron_context_set_driver_timeout_ms(aeron_context_t *context, uint64_t value);
uint64_t aeron_context_get_driver_timeout_ms(aeron_context_t *context);
int aeron_context_set_keepalive_interval_ns(aeron_context_t *context, uint64_t value);
uint64_t aeron_context_get_keepalive_interval_ns(aeron_context_t *context);
int aeron_context_set_resource_linger_duration_ns(aeron_context_t *context, uint64_t value);
uint64_t aeron_context_get_resource_linger_duration_ns(aeron_context_t *context);
int aeron_context_set_idle_sleep_duration_ns(aeron_context_t *context, uint64_t value);
uint64_t aeron_context_get_idle_sleep_duration_ns(aeron_context_t *context);
int aeron_context_set_pre_touch_mapped_memory(aeron_context_t *context, bool value);
bool aeron_context_get_pre_touch_mapped_memory(aeron_context_t *context);
int aeron_context_set_client_name(aeron_context_t *context, const char *value);
const char *aeron_context_get_client_name(aeron_context_t *context);
int aeron_context_set_use_conductor_agent_invoker(aeron_context_t *context, bool value);
bool aeron_context_get_use_conductor_agent_invoker(aeron_context_t *context);

int aeron_init(aeron_t **client, aeron_context_t *context);
int aeron_start(aeron_t *client);
int aeron_main_do_work(aeron_t *client);
void aeron_main_idle_strategy(aeron_t *client, int work_count);
int aeron_close(aeron_t *client);
bool aeron_is_closed(aeron_t *client);
int64_t aeron_client_id(aeron_t *client);
int64_t aeron_next_correlation_id(aeron_t *client);

int aeron_async_add_publication(
    aeron_async_add_publication_t **async,
    aeron_t *client,
    const char *uri,
    int32_t stream_id);
int aeron_async_add_publication_poll(
    aeron_publication_t **publication,
    aeron_async_add_publication_t *async);

int aeron_async_add_subscription(
    aeron_async_add_subscription_t **async,
    aeron_t *client,
    const char *uri,
    int32_t stream_id,
    void *on_available_image_handler,
    void *on_available_image_clientd,
    void *on_unavailable_image_handler,
    void *on_unavailable_image_clientd);
int aeron_async_add_subscription_poll(
    aeron_subscription_t **subscription,
    aeron_async_add_subscription_t *async);

int64_t aeron_publication_offer(
    aeron_publication_t *publication,
    const uint8_t *buffer,
    size_t length,
    aeron_reserved_value_supplier_t reserved_value_supplier,
    void *clientd);

int aeron_subscription_poll(
    aeron_subscription_t *subscription,
    aeron_fragment_handler_t handler,
    void *clientd,
    size_t fragment_limit);

int aeron_errcode(void);
const char *aeron_errmsg(void);
"""

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
    "aeron_async_add_publication",
    "aeron_async_add_publication_poll",
    "aeron_async_add_subscription",
    "aeron_async_add_subscription_poll",
    "aeron_publication_offer",
    "aeron_subscription_poll",
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
    ffi.cdef(_CDEF)
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
            "Loaded libaeron does not expose required symbols for Phase 2 MVP: "
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
