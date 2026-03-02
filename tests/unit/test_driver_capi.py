import pytest

from pyaeron._driver_capi import _CDEF, _library_candidates, try_load_libaeron_driver


def test_driver_library_candidates_prioritize_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AERON_DRIVER_LIBRARY_PATH", "/tmp/libaeron_driver-test.so")
    candidates = _library_candidates()
    assert candidates[0] == "/tmp/libaeron_driver-test.so"


def test_try_load_libaeron_driver_is_optional() -> None:
    capi = try_load_libaeron_driver()
    if capi is None:
        assert capi is None
    else:
        assert capi.library_path
        assert hasattr(capi.lib, "aeron_driver_init")


def test_driver_cdef_uses_ll_for_64_bit_primitives() -> None:
    assert "typedef signed long long int64_t;" in _CDEF
    assert "typedef unsigned long long uint64_t;" in _CDEF
    assert "typedef unsigned long long size_t;" in _CDEF
