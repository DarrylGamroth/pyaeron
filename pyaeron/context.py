from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Any

from ._capi import load_libaeron
from .errors import AeronStateError, check_rc
from .util import ensure_open


class Context:
    """Configuration object for creating a Client.

    Phase 1 provides API shape and lifecycle semantics only.
    """

    def __init__(
        self,
        *,
        aeron_dir: str | None = None,
        driver_timeout_ms: int | None = None,
        keepalive_interval_ns: int | None = None,
        resource_linger_duration_ns: int | None = None,
        idle_sleep_duration_ns: int | None = None,
        pre_touch_mapped_memory: bool | None = None,
        use_conductor_agent_invoker: bool | None = None,
        client_name: str | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self._capi = load_libaeron()
        context_ptr = self._capi.ffi.new("aeron_context_t **")
        check_rc(self._capi.lib.aeron_context_init(context_ptr), capi=self._capi)
        self._ptr = context_ptr[0]

        self._closed = False
        self._bound = False

        self.on_error = on_error
        self._client_name: str | None = None

        if aeron_dir is not None:
            self.aeron_dir = aeron_dir
        if driver_timeout_ms is not None:
            self.driver_timeout_ms = driver_timeout_ms
        if keepalive_interval_ns is not None:
            self.keepalive_interval_ns = keepalive_interval_ns
        if resource_linger_duration_ns is not None:
            self.resource_linger_duration_ns = resource_linger_duration_ns
        if idle_sleep_duration_ns is not None:
            self.idle_sleep_duration_ns = idle_sleep_duration_ns
        if pre_touch_mapped_memory is not None:
            self.pre_touch_mapped_memory = pre_touch_mapped_memory
        if use_conductor_agent_invoker is not None:
            self.use_conductor_agent_invoker = use_conductor_agent_invoker
        if client_name is not None:
            self.client_name = client_name

    def __enter__(self) -> Context:
        ensure_open(self._closed, "Context")
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
        ensure_open(self._closed, "Context")
        return self._ptr

    @property
    def aeron_dir(self) -> str | None:
        ensure_open(self._closed, "Context")
        ptr = self._capi.lib.aeron_context_get_dir(self._ptr)
        return self._capi.string_from_ptr(ptr)

    @aeron_dir.setter
    def aeron_dir(self, value: str) -> None:
        ensure_open(self._closed, "Context")
        if self._bound:
            raise AeronStateError("Context configuration cannot be mutated after Client creation")
        cvalue = self._capi.c_string(value)
        check_rc(self._capi.lib.aeron_context_set_dir(self._ptr, cvalue), capi=self._capi)

    @property
    def driver_timeout_ms(self) -> int:
        ensure_open(self._closed, "Context")
        return int(self._capi.lib.aeron_context_get_driver_timeout_ms(self._ptr))

    @driver_timeout_ms.setter
    def driver_timeout_ms(self, value: int) -> None:
        ensure_open(self._closed, "Context")
        if self._bound:
            raise AeronStateError("Context configuration cannot be mutated after Client creation")
        check_rc(
            self._capi.lib.aeron_context_set_driver_timeout_ms(self._ptr, value),
            capi=self._capi,
        )

    @property
    def keepalive_interval_ns(self) -> int:
        ensure_open(self._closed, "Context")
        return int(self._capi.lib.aeron_context_get_keepalive_interval_ns(self._ptr))

    @keepalive_interval_ns.setter
    def keepalive_interval_ns(self, value: int) -> None:
        ensure_open(self._closed, "Context")
        if self._bound:
            raise AeronStateError("Context configuration cannot be mutated after Client creation")
        check_rc(
            self._capi.lib.aeron_context_set_keepalive_interval_ns(self._ptr, value),
            capi=self._capi,
        )

    @property
    def resource_linger_duration_ns(self) -> int:
        ensure_open(self._closed, "Context")
        return int(self._capi.lib.aeron_context_get_resource_linger_duration_ns(self._ptr))

    @resource_linger_duration_ns.setter
    def resource_linger_duration_ns(self, value: int) -> None:
        ensure_open(self._closed, "Context")
        if self._bound:
            raise AeronStateError("Context configuration cannot be mutated after Client creation")
        check_rc(
            self._capi.lib.aeron_context_set_resource_linger_duration_ns(self._ptr, value),
            capi=self._capi,
        )

    @property
    def idle_sleep_duration_ns(self) -> int:
        ensure_open(self._closed, "Context")
        return int(self._capi.lib.aeron_context_get_idle_sleep_duration_ns(self._ptr))

    @idle_sleep_duration_ns.setter
    def idle_sleep_duration_ns(self, value: int) -> None:
        ensure_open(self._closed, "Context")
        if self._bound:
            raise AeronStateError("Context configuration cannot be mutated after Client creation")
        check_rc(
            self._capi.lib.aeron_context_set_idle_sleep_duration_ns(self._ptr, value),
            capi=self._capi,
        )

    @property
    def pre_touch_mapped_memory(self) -> bool:
        ensure_open(self._closed, "Context")
        return bool(self._capi.lib.aeron_context_get_pre_touch_mapped_memory(self._ptr))

    @pre_touch_mapped_memory.setter
    def pre_touch_mapped_memory(self, value: bool) -> None:
        ensure_open(self._closed, "Context")
        if self._bound:
            raise AeronStateError("Context configuration cannot be mutated after Client creation")
        check_rc(
            self._capi.lib.aeron_context_set_pre_touch_mapped_memory(self._ptr, value),
            capi=self._capi,
        )

    @property
    def use_conductor_agent_invoker(self) -> bool:
        ensure_open(self._closed, "Context")
        return bool(self._capi.lib.aeron_context_get_use_conductor_agent_invoker(self._ptr))

    @use_conductor_agent_invoker.setter
    def use_conductor_agent_invoker(self, value: bool) -> None:
        ensure_open(self._closed, "Context")
        if self._bound:
            raise AeronStateError("Context configuration cannot be mutated after Client creation")
        check_rc(
            self._capi.lib.aeron_context_set_use_conductor_agent_invoker(self._ptr, value),
            capi=self._capi,
        )

    @property
    def client_name(self) -> str | None:
        ensure_open(self._closed, "Context")
        ptr = self._capi.lib.aeron_context_get_client_name(self._ptr)
        return self._capi.string_from_ptr(ptr)

    @client_name.setter
    def client_name(self, value: str) -> None:
        ensure_open(self._closed, "Context")
        if self._bound:
            raise AeronStateError("Context configuration cannot be mutated after Client creation")
        cvalue = self._capi.c_string(value)
        check_rc(self._capi.lib.aeron_context_set_client_name(self._ptr, cvalue), capi=self._capi)
        self._client_name = value

    def _mark_bound(self) -> None:
        ensure_open(self._closed, "Context")
        if self._bound:
            raise AeronStateError("Context instances are single-use for Client construction")
        self._bound = True

    def close(self) -> None:
        if self._closed:
            return
        check_rc(self._capi.lib.aeron_context_close(self._ptr), capi=self._capi)
        self._ptr = self._capi.ffi.NULL
        self._closed = True
