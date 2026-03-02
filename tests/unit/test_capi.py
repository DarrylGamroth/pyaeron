import pytest
from cffi import FFI

from pyaeron._capi import (
    _REQUIRED_SYMBOLS,
    _library_candidates,
    c_string_to_str,
    try_load_libaeron,
)
from pyaeron._generated_cdef import CDEF


def test_c_string_to_str_handles_null() -> None:
    ffi = FFI()
    ffi.cdef("typedef int int32_t;")
    assert c_string_to_str(ffi, ffi.NULL) is None


def test_c_string_to_str_decodes_utf8() -> None:
    ffi = FFI()
    ffi.cdef("typedef int int32_t;")
    ptr = ffi.new("char[]", b"hello")
    assert c_string_to_str(ffi, ptr) == "hello"


def test_library_candidates_prioritize_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AERON_LIBRARY_PATH", "/tmp/libaeron-test.so")
    candidates = _library_candidates()
    assert candidates[0] == "/tmp/libaeron-test.so"


def test_try_load_libaeron_is_optional() -> None:
    capi = try_load_libaeron()
    if capi is None:
        assert capi is None
    else:
        assert capi.library_path
        assert hasattr(capi.lib, "aeron_errcode")


def test_required_symbols_include_client_id_helpers() -> None:
    assert "aeron_client_id" in _REQUIRED_SYMBOLS
    assert "aeron_next_correlation_id" in _REQUIRED_SYMBOLS


def test_generated_cdef_uses_ll_for_64_bit_primitives() -> None:
    assert "typedef signed long long int64_t;" in CDEF
    assert "typedef unsigned long long uint64_t;" in CDEF
    assert "typedef unsigned long long size_t;" in CDEF
