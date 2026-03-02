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
typedef struct aeron_exclusive_publication_stct aeron_exclusive_publication_t;
typedef struct aeron_subscription_stct aeron_subscription_t;
typedef struct aeron_image_stct aeron_image_t;
typedef struct aeron_counter_stct aeron_counter_t;
typedef struct aeron_counters_reader_stct aeron_counters_reader_t;
typedef struct aeron_cnc_stct aeron_cnc_t;
typedef struct aeron_header_stct aeron_header_t;
typedef struct aeron_client_registering_resource_stct aeron_async_add_publication_t;
typedef struct aeron_client_registering_resource_stct aeron_async_add_exclusive_publication_t;
typedef struct aeron_client_registering_resource_stct aeron_async_add_subscription_t;
typedef struct aeron_client_registering_resource_stct aeron_async_add_counter_t;
typedef struct aeron_client_registering_resource_stct aeron_async_destination_t;
typedef struct aeron_header_values_stct
{
    uint8_t data[44];
}
aeron_header_values_t;
typedef struct aeron_buffer_claim_stct
{
    uint8_t *frame_header;
    uint8_t *data;
    size_t length;
}
aeron_buffer_claim_t;
typedef struct aeron_counter_constants_stct
{
    int64_t registration_id;
    int32_t counter_id;
}
aeron_counter_constants_t;
typedef struct aeron_image_constants_stct
{
    aeron_subscription_t *subscription;
    const char *source_identity;
    int64_t correlation_id;
    int64_t join_position;
    size_t position_bits_to_shift;
    size_t term_buffer_length;
    size_t mtu_length;
    int32_t session_id;
    int32_t initial_term_id;
    int32_t subscriber_position_id;
}
aeron_image_constants_t;
typedef struct aeron_cnc_constants_stct
{
    int32_t cnc_version;
    int32_t to_driver_buffer_length;
    int32_t to_clients_buffer_length;
    int32_t counter_metadata_buffer_length;
    int32_t counter_values_buffer_length;
    int32_t error_log_buffer_length;
    int64_t client_liveness_timeout;
    int64_t start_timestamp;
    int64_t pid;
    int32_t file_page_size;
}
aeron_cnc_constants_t;

typedef int64_t (*aeron_reserved_value_supplier_t)(
    void *clientd, uint8_t *buffer, size_t frame_length);
typedef void (*aeron_fragment_handler_t)(
    void *clientd, const uint8_t *buffer, size_t length, aeron_header_t *header);
typedef void (*aeron_error_log_reader_func_t)(
    int32_t observation_count,
    int64_t first_observation_timestamp,
    int64_t last_observation_timestamp,
    const char *error,
    size_t error_length,
    void *clientd);

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
int aeron_async_add_exclusive_publication(
    aeron_async_add_exclusive_publication_t **async,
    aeron_t *client,
    const char *uri,
    int32_t stream_id);
int aeron_async_add_exclusive_publication_poll(
    aeron_exclusive_publication_t **publication,
    aeron_async_add_exclusive_publication_t *async);

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
int aeron_async_add_counter(
    aeron_async_add_counter_t **async,
    aeron_t *client,
    int32_t type_id,
    const uint8_t *key_buffer,
    size_t key_buffer_length,
    const char *label_buffer,
    size_t label_buffer_length);
int aeron_async_add_counter_poll(
    aeron_counter_t **counter,
    aeron_async_add_counter_t *async);

int64_t aeron_publication_offer(
    aeron_publication_t *publication,
    const uint8_t *buffer,
    size_t length,
    aeron_reserved_value_supplier_t reserved_value_supplier,
    void *clientd);
bool aeron_publication_is_closed(aeron_publication_t *publication);
bool aeron_publication_is_connected(aeron_publication_t *publication);
int aeron_publication_close(aeron_publication_t *publication, void *handler, void *clientd);
int64_t aeron_publication_try_claim(
    aeron_publication_t *publication,
    size_t length,
    aeron_buffer_claim_t *buffer_claim);
int aeron_publication_async_add_destination(
    aeron_async_destination_t **async,
    aeron_t *client,
    aeron_publication_t *publication,
    const char *uri);
int aeron_publication_async_remove_destination(
    aeron_async_destination_t **async,
    aeron_t *client,
    aeron_publication_t *publication,
    const char *uri);
int aeron_publication_async_destination_poll(aeron_async_destination_t *async);

int64_t aeron_exclusive_publication_offer(
    aeron_exclusive_publication_t *publication,
    const uint8_t *buffer,
    size_t length,
    aeron_reserved_value_supplier_t reserved_value_supplier,
    void *clientd);
int64_t aeron_exclusive_publication_try_claim(
    aeron_exclusive_publication_t *publication,
    size_t length,
    aeron_buffer_claim_t *buffer_claim);
bool aeron_exclusive_publication_is_closed(aeron_exclusive_publication_t *publication);
bool aeron_exclusive_publication_is_connected(aeron_exclusive_publication_t *publication);
int aeron_exclusive_publication_close(
    aeron_exclusive_publication_t *publication,
    void *handler,
    void *clientd);
int aeron_exclusive_publication_async_add_destination(
    aeron_async_destination_t **async,
    aeron_t *client,
    aeron_exclusive_publication_t *publication,
    const char *uri);
int aeron_exclusive_publication_async_remove_destination(
    aeron_async_destination_t **async,
    aeron_t *client,
    aeron_exclusive_publication_t *publication,
    const char *uri);
int aeron_exclusive_publication_async_destination_poll(aeron_async_destination_t *async);

int aeron_buffer_claim_commit(aeron_buffer_claim_t *buffer_claim);
int aeron_buffer_claim_abort(aeron_buffer_claim_t *buffer_claim);

int aeron_subscription_poll(
    aeron_subscription_t *subscription,
    aeron_fragment_handler_t handler,
    void *clientd,
    size_t fragment_limit);
bool aeron_subscription_is_closed(aeron_subscription_t *subscription);
bool aeron_subscription_is_connected(aeron_subscription_t *subscription);
int aeron_subscription_close(aeron_subscription_t *subscription, void *handler, void *clientd);
int aeron_subscription_async_add_destination(
    aeron_async_destination_t **async,
    aeron_t *client,
    aeron_subscription_t *subscription,
    const char *uri);
int aeron_subscription_async_remove_destination(
    aeron_async_destination_t **async,
    aeron_t *client,
    aeron_subscription_t *subscription,
    const char *uri);
int aeron_subscription_async_destination_poll(aeron_async_destination_t *async);
int aeron_subscription_image_count(aeron_subscription_t *subscription);
aeron_image_t *aeron_subscription_image_by_session_id(
    aeron_subscription_t *subscription,
    int32_t session_id);
int aeron_subscription_image_release(aeron_subscription_t *subscription, aeron_image_t *image);

int aeron_header_values(aeron_header_t *header, aeron_header_values_t *values);
int64_t aeron_header_position(aeron_header_t *header);
int aeron_image_constants(aeron_image_t *image, aeron_image_constants_t *constants);
int64_t aeron_image_position(aeron_image_t *image);
bool aeron_image_is_closed(aeron_image_t *image);

aeron_counters_reader_t *aeron_counters_reader(aeron_t *client);
int32_t aeron_counters_reader_max_counter_id(aeron_counters_reader_t *reader);
int64_t *aeron_counters_reader_addr(aeron_counters_reader_t *counters_reader, int32_t counter_id);
int aeron_counter_constants(aeron_counter_t *counter, aeron_counter_constants_t *constants);
int64_t *aeron_counter_addr(aeron_counter_t *counter);
int aeron_counter_close(aeron_counter_t *counter, void *handler, void *clientd);
bool aeron_counter_is_closed(aeron_counter_t *counter);

int aeron_cnc_init(aeron_cnc_t **aeron_cnc, const char *base_path, int64_t timeout_ms);
int aeron_cnc_constants(aeron_cnc_t *aeron_cnc, aeron_cnc_constants_t *constants);
const char *aeron_cnc_filename(aeron_cnc_t *aeron_cnc);
int64_t aeron_cnc_to_driver_heartbeat(aeron_cnc_t *aeron_cnc);
size_t aeron_cnc_error_log_read(
    aeron_cnc_t *aeron_cnc,
    aeron_error_log_reader_func_t callback,
    void *clientd,
    int64_t since_timestamp);
aeron_counters_reader_t *aeron_cnc_counters_reader(aeron_cnc_t *aeron_cnc);
void aeron_cnc_close(aeron_cnc_t *aeron_cnc);

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
