from __future__ import annotations

import ctypes.util
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, cast

from cffi import FFI  # type: ignore[import-untyped]

from .errors import LibraryLoadError, UnsupportedAeronVersionError

_CDEF = r"""
typedef _Bool bool;
typedef signed int int32_t;
typedef unsigned int uint32_t;
typedef signed long long int64_t;
typedef unsigned long long uint64_t;
typedef unsigned long long size_t;

typedef struct aeron_driver_context_stct aeron_driver_context_t;
typedef struct aeron_driver_stct aeron_driver_t;

typedef enum aeron_threading_mode_enum
{
    AERON_THREADING_MODE_DEDICATED,
    AERON_THREADING_MODE_SHARED_NETWORK,
    AERON_THREADING_MODE_SHARED,
    AERON_THREADING_MODE_INVOKER
}
aeron_threading_mode_t;

int aeron_driver_context_init(aeron_driver_context_t **context);
int aeron_driver_context_close(aeron_driver_context_t *context);

int aeron_driver_context_set_dir(aeron_driver_context_t *context, const char *value);
const char *aeron_driver_context_get_dir(aeron_driver_context_t *context);

int aeron_driver_context_set_dir_delete_on_start(aeron_driver_context_t *context, bool value);
bool aeron_driver_context_get_dir_delete_on_start(aeron_driver_context_t *context);

int aeron_driver_context_set_dir_delete_on_shutdown(aeron_driver_context_t *context, bool value);
bool aeron_driver_context_get_dir_delete_on_shutdown(aeron_driver_context_t *context);

int aeron_driver_context_set_threading_mode(
    aeron_driver_context_t *context,
    aeron_threading_mode_t mode);
aeron_threading_mode_t aeron_driver_context_get_threading_mode(aeron_driver_context_t *context);

int aeron_driver_init(aeron_driver_t **driver, aeron_driver_context_t *context);
int aeron_driver_start(aeron_driver_t *driver, bool manual_main_loop);
int aeron_driver_main_do_work(aeron_driver_t *driver);
void aeron_driver_main_idle_strategy(aeron_driver_t *driver, int work_count);
int aeron_driver_close(aeron_driver_t *driver);

int aeron_delete_directory(const char *dirname);

int aeron_errcode(void);
const char *aeron_errmsg(void);
"""

_REQUIRED_SYMBOLS = (
    "aeron_driver_context_init",
    "aeron_driver_context_close",
    "aeron_driver_context_set_dir",
    "aeron_driver_context_get_dir",
    "aeron_driver_context_set_dir_delete_on_start",
    "aeron_driver_context_get_dir_delete_on_start",
    "aeron_driver_context_set_dir_delete_on_shutdown",
    "aeron_driver_context_get_dir_delete_on_shutdown",
    "aeron_driver_context_set_threading_mode",
    "aeron_driver_context_get_threading_mode",
    "aeron_driver_init",
    "aeron_driver_start",
    "aeron_driver_main_do_work",
    "aeron_driver_main_idle_strategy",
    "aeron_driver_close",
    "aeron_delete_directory",
    "aeron_errcode",
    "aeron_errmsg",
)

_FILENAME_CANDIDATES = (
    "libaeron_driver.so",
    "libaeron_driver.dylib",
    "aeron_driver.dll",
)


@dataclass(frozen=True, slots=True)
class LoadedAeronDriverCAPI:
    ffi: FFI
    lib: Any
    library_path: str

    def c_string(self, value: str) -> Any:
        return self.ffi.new("char[]", value.encode("utf-8"))

    def string_from_ptr(self, ptr: Any) -> str | None:
        if ptr == self.ffi.NULL:
            return None
        return cast(bytes, self.ffi.string(ptr)).decode("utf-8")


def _build_ffi() -> FFI:
    ffi = FFI()
    ffi.cdef(_CDEF)
    return ffi


def _library_candidates() -> list[str]:
    candidates: list[str] = []

    explicit = os.environ.get("AERON_DRIVER_LIBRARY_PATH")
    if explicit:
        candidates.append(explicit)

    for name in ("aeron_driver", "libaeron_driver"):
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
        "Unable to load libaeron_driver. "
        "Set AERON_DRIVER_LIBRARY_PATH to a valid shared library path.\n"
        f"Candidates attempted: {candidates}\n"
        f"Failures:\n{detail}"
    )


def _validate_required_symbols(capi: LoadedAeronDriverCAPI) -> None:
    missing = [symbol for symbol in _REQUIRED_SYMBOLS if not hasattr(capi.lib, symbol)]
    if missing:
        raise UnsupportedAeronVersionError(
            "Loaded libaeron_driver does not expose required symbols for embedded driver: "
            + ", ".join(missing)
        )


@lru_cache(maxsize=1)
def load_libaeron_driver() -> LoadedAeronDriverCAPI:
    ffi = _build_ffi()
    lib, path = _load_first_available(ffi, _library_candidates())
    capi = LoadedAeronDriverCAPI(ffi=ffi, lib=lib, library_path=path)
    _validate_required_symbols(capi)
    return capi


def try_load_libaeron_driver() -> LoadedAeronDriverCAPI | None:
    try:
        return load_libaeron_driver()
    except (LibraryLoadError, UnsupportedAeronVersionError):
        return None
