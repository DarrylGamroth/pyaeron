from __future__ import annotations

from typing import Any

import pytest
from cffi import FFI

from pyaeron.driver import MediaDriver, MediaDriverContext, ThreadingMode
from pyaeron.errors import AeronError, AeronStateError, ResourceClosedError


class _FakeDriverLib:
    def __init__(self, ffi: FFI) -> None:
        self._ffi = ffi
        self._errmsg = ffi.new("char[]", b"fake-driver-error")
        self._context_ptr = ffi.cast("aeron_driver_context_t *", 0x1001)
        self._driver_ptr = ffi.cast("aeron_driver_t *", 0x1002)

        self._dir_ptr = ffi.new("char[]", b"/tmp/fake-aeron")
        self._delete_on_start = False
        self._delete_on_shutdown = False
        self._threading_mode = 0
        self._context_closed = False
        self._driver_closed = False
        self.fail_init = False
        self.fail_start = False

    def aeron_errcode(self) -> int:
        return 0

    def aeron_errmsg(self) -> Any:
        return self._errmsg

    def aeron_driver_context_init(self, context_ptr: Any) -> int:
        context_ptr[0] = self._context_ptr
        return 0

    def aeron_driver_context_close(self, _context: Any) -> int:
        self._context_closed = True
        return 0

    def aeron_driver_context_set_dir(self, _context: Any, value: Any) -> int:
        self._dir_ptr = value
        return 0

    def aeron_driver_context_get_dir(self, _context: Any) -> Any:
        return self._dir_ptr

    def aeron_driver_context_set_dir_delete_on_start(self, _context: Any, value: bool) -> int:
        self._delete_on_start = bool(value)
        return 0

    def aeron_driver_context_get_dir_delete_on_start(self, _context: Any) -> bool:
        return self._delete_on_start

    def aeron_driver_context_set_dir_delete_on_shutdown(self, _context: Any, value: bool) -> int:
        self._delete_on_shutdown = bool(value)
        return 0

    def aeron_driver_context_get_dir_delete_on_shutdown(self, _context: Any) -> bool:
        return self._delete_on_shutdown

    def aeron_driver_context_set_threading_mode(self, _context: Any, mode: int) -> int:
        self._threading_mode = int(mode)
        return 0

    def aeron_driver_context_get_threading_mode(self, _context: Any) -> int:
        return self._threading_mode

    def aeron_driver_init(self, driver_ptr: Any, _context: Any) -> int:
        if self.fail_init:
            return -1
        driver_ptr[0] = self._driver_ptr
        return 0

    def aeron_driver_start(self, _driver: Any, _manual_main_loop: bool) -> int:
        if self.fail_start:
            return -1
        return 0

    def aeron_driver_main_do_work(self, _driver: Any) -> int:
        return 3

    def aeron_driver_main_idle_strategy(self, _driver: Any, _work_count: int) -> None:
        return None

    def aeron_driver_close(self, _driver: Any) -> int:
        self._driver_closed = True
        return 0

    def aeron_delete_directory(self, _dirname: Any) -> int:
        return 0


class _FakeDriverCapi:
    def __init__(self) -> None:
        ffi = FFI()
        ffi.cdef(
            """
            typedef _Bool bool;
            typedef signed int int32_t;
            typedef unsigned int uint32_t;
            typedef signed long int int64_t;
            typedef unsigned long int uint64_t;
            typedef unsigned long size_t;
            typedef struct aeron_driver_context_stct aeron_driver_context_t;
            typedef struct aeron_driver_stct aeron_driver_t;
            """
        )
        self.ffi = ffi
        self.lib = _FakeDriverLib(ffi)

    def c_string(self, value: str) -> Any:
        return self.ffi.new("char[]", value.encode())

    def string_from_ptr(self, ptr: Any) -> str | None:
        if ptr == self.ffi.NULL:
            return None
        return self.ffi.string(ptr).decode()


@pytest.fixture
def fake_driver_capi(monkeypatch: pytest.MonkeyPatch) -> _FakeDriverCapi:
    fake = _FakeDriverCapi()
    monkeypatch.setattr("pyaeron.driver.load_libaeron_driver", lambda: fake)
    return fake


def test_media_driver_context_configuration(fake_driver_capi: _FakeDriverCapi) -> None:
    ctx = MediaDriverContext(
        aeron_dir="/tmp/md-ctx",
        dir_delete_on_start=True,
        dir_delete_on_shutdown=True,
        threading_mode=ThreadingMode.SHARED,
    )

    assert ctx.aeron_dir == "/tmp/md-ctx"
    assert ctx.dir_delete_on_start is True
    assert ctx.dir_delete_on_shutdown is True
    assert ctx.threading_mode == ThreadingMode.SHARED

    ctx.close()
    assert ctx.closed is True


def test_media_driver_launch_and_close(fake_driver_capi: _FakeDriverCapi) -> None:
    driver = MediaDriver.launch_embedded(aeron_dir="/tmp/md-embedded")
    assert driver.is_open is True
    assert driver.aeron_dir == "/tmp/md-embedded"
    assert driver.do_work() == 3

    driver.idle_strategy(0)
    driver.close()
    assert driver.is_open is False
    with pytest.raises(ResourceClosedError):
        _ = driver.pointer


def test_context_cannot_mutate_after_launch(fake_driver_capi: _FakeDriverCapi) -> None:
    ctx = MediaDriverContext(aeron_dir="/tmp/md")
    driver = MediaDriver(ctx)
    with pytest.raises(AeronStateError):
        ctx.aeron_dir = "/tmp/changed"
    with pytest.raises(AeronStateError):
        ctx.close()
    driver.close()
    assert ctx.closed is True


def test_launch_embedded_defaults(fake_driver_capi: _FakeDriverCapi) -> None:
    driver = MediaDriver.launch_embedded()
    try:
        assert driver.aeron_dir is not None
        assert "pyaeron-md-" in (driver.aeron_dir or "")
        assert driver.context.dir_delete_on_start is True
        assert driver.context.dir_delete_on_shutdown is True
    finally:
        driver.close()


def test_start_failure_does_not_leave_context_bound(fake_driver_capi: _FakeDriverCapi) -> None:
    fake_driver_capi.lib.fail_start = True
    ctx = MediaDriverContext(aeron_dir="/tmp/md-fail")

    with pytest.raises(AeronError):
        MediaDriver(ctx)

    # Context remains mutable/closable after failed launch.
    ctx.aeron_dir = "/tmp/md-fail-2"
    ctx.close()
    assert ctx.closed is True
    assert fake_driver_capi.lib._driver_closed is True
