from __future__ import annotations

import tempfile
import uuid
from enum import IntEnum
from types import TracebackType
from typing import Any

from ._driver_capi import load_libaeron_driver
from .errors import AeronStateError, check_rc
from .util import ensure_open


class ThreadingMode(IntEnum):
    DEDICATED = 0
    SHARED_NETWORK = 1
    SHARED = 2
    INVOKER = 3


class MediaDriverContext:
    """Configuration context for embedded Aeron media driver launch."""

    def __init__(
        self,
        *,
        aeron_dir: str | None = None,
        dir_delete_on_start: bool | None = None,
        dir_delete_on_shutdown: bool | None = None,
        threading_mode: ThreadingMode | None = None,
    ) -> None:
        self._capi = load_libaeron_driver()
        context_ptr = self._capi.ffi.new("aeron_driver_context_t **")
        check_rc(self._capi.lib.aeron_driver_context_init(context_ptr), capi=self._capi)
        self._ptr = context_ptr[0]

        self._closed = False
        self._bound = False

        if aeron_dir is not None:
            self.aeron_dir = aeron_dir
        if dir_delete_on_start is not None:
            self.dir_delete_on_start = dir_delete_on_start
        if dir_delete_on_shutdown is not None:
            self.dir_delete_on_shutdown = dir_delete_on_shutdown
        if threading_mode is not None:
            self.threading_mode = threading_mode

    def __enter__(self) -> MediaDriverContext:
        ensure_open(self._closed, "MediaDriverContext")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def pointer(self) -> Any:
        ensure_open(self._closed, "MediaDriverContext")
        return self._ptr

    @property
    def aeron_dir(self) -> str | None:
        ensure_open(self._closed, "MediaDriverContext")
        return self._capi.string_from_ptr(self._capi.lib.aeron_driver_context_get_dir(self._ptr))

    @aeron_dir.setter
    def aeron_dir(self, value: str) -> None:
        self._ensure_mutable()
        check_rc(
            self._capi.lib.aeron_driver_context_set_dir(self._ptr, self._capi.c_string(value)),
            capi=self._capi,
        )

    @property
    def dir_delete_on_start(self) -> bool:
        ensure_open(self._closed, "MediaDriverContext")
        return bool(self._capi.lib.aeron_driver_context_get_dir_delete_on_start(self._ptr))

    @dir_delete_on_start.setter
    def dir_delete_on_start(self, value: bool) -> None:
        self._ensure_mutable()
        check_rc(
            self._capi.lib.aeron_driver_context_set_dir_delete_on_start(self._ptr, value),
            capi=self._capi,
        )

    @property
    def dir_delete_on_shutdown(self) -> bool:
        ensure_open(self._closed, "MediaDriverContext")
        return bool(self._capi.lib.aeron_driver_context_get_dir_delete_on_shutdown(self._ptr))

    @dir_delete_on_shutdown.setter
    def dir_delete_on_shutdown(self, value: bool) -> None:
        self._ensure_mutable()
        check_rc(
            self._capi.lib.aeron_driver_context_set_dir_delete_on_shutdown(self._ptr, value),
            capi=self._capi,
        )

    @property
    def threading_mode(self) -> ThreadingMode:
        ensure_open(self._closed, "MediaDriverContext")
        raw = int(self._capi.lib.aeron_driver_context_get_threading_mode(self._ptr))
        return ThreadingMode(raw)

    @threading_mode.setter
    def threading_mode(self, value: ThreadingMode) -> None:
        self._ensure_mutable()
        check_rc(
            self._capi.lib.aeron_driver_context_set_threading_mode(self._ptr, int(value)),
            capi=self._capi,
        )

    def _mark_bound(self) -> None:
        ensure_open(self._closed, "MediaDriverContext")
        if self._bound:
            raise AeronStateError(
                "MediaDriverContext instances are single-use for MediaDriver launch"
            )
        self._bound = True

    def _ensure_mutable(self) -> None:
        ensure_open(self._closed, "MediaDriverContext")
        if self._bound:
            raise AeronStateError("MediaDriverContext cannot be mutated after MediaDriver launch")

    def _adopted_by_driver(self) -> None:
        self._bound = True

    def _mark_closed_by_driver(self) -> None:
        self._ptr = self._capi.ffi.NULL
        self._closed = True

    def close(self) -> None:
        if self._closed:
            return
        if self._bound:
            raise AeronStateError(
                "MediaDriverContext is owned by MediaDriver; close the driver instead"
            )
        check_rc(self._capi.lib.aeron_driver_context_close(self._ptr), capi=self._capi)
        self._ptr = self._capi.ffi.NULL
        self._closed = True


class MediaDriver:
    """Embedded Aeron media driver wrapper."""

    def __init__(self, context: MediaDriverContext, *, manual_main_loop: bool = False) -> None:
        context._mark_bound()
        self._capi = context._capi
        driver_ptr = self._capi.ffi.new("aeron_driver_t **")
        try:
            check_rc(self._capi.lib.aeron_driver_init(driver_ptr, context.pointer), capi=self._capi)
            self._ptr = driver_ptr[0]
            check_rc(
                self._capi.lib.aeron_driver_start(self._ptr, manual_main_loop),
                capi=self._capi,
            )
        except Exception:
            if driver_ptr[0] != self._capi.ffi.NULL:
                self._capi.lib.aeron_driver_close(driver_ptr[0])
            raise

        self._context = context
        self._context._adopted_by_driver()
        self._closed = False
        self._manual_main_loop = manual_main_loop

    @classmethod
    def launch_embedded(
        cls,
        *,
        aeron_dir: str | None = None,
        manual_main_loop: bool = False,
        threading_mode: ThreadingMode | None = None,
        dir_delete_on_start: bool = True,
        dir_delete_on_shutdown: bool = True,
    ) -> MediaDriver:
        if aeron_dir is None:
            base = tempfile.gettempdir()
            aeron_dir = f"{base}/pyaeron-md-{uuid.uuid4()}"

        ctx = MediaDriverContext(
            aeron_dir=aeron_dir,
            threading_mode=threading_mode,
            dir_delete_on_start=dir_delete_on_start,
            dir_delete_on_shutdown=dir_delete_on_shutdown,
        )
        return cls(ctx, manual_main_loop=manual_main_loop)

    def __enter__(self) -> MediaDriver:
        ensure_open(self._closed, "MediaDriver")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    @property
    def pointer(self) -> Any:
        ensure_open(self._closed, "MediaDriver")
        return self._ptr

    @property
    def is_open(self) -> bool:
        return not self._closed

    @property
    def manual_main_loop(self) -> bool:
        return self._manual_main_loop

    @property
    def aeron_dir(self) -> str | None:
        return self._context.aeron_dir

    @property
    def context(self) -> MediaDriverContext:
        return self._context

    def do_work(self) -> int:
        ensure_open(self._closed, "MediaDriver")
        return int(check_rc(self._capi.lib.aeron_driver_main_do_work(self._ptr), capi=self._capi))

    def idle_strategy(self, work_count: int) -> None:
        ensure_open(self._closed, "MediaDriver")
        self._capi.lib.aeron_driver_main_idle_strategy(self._ptr, work_count)

    def close(self) -> None:
        if self._closed:
            return
        check_rc(self._capi.lib.aeron_driver_close(self._ptr), capi=self._capi)
        self._ptr = self._capi.ffi.NULL
        self._closed = True
        self._context._mark_closed_by_driver()
