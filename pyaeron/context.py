from __future__ import annotations

from collections.abc import Callable
from types import TracebackType

from .errors import AeronStateError
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
        self._closed = False
        self._bound = False

        self._aeron_dir = aeron_dir
        self.driver_timeout_ms = driver_timeout_ms
        self.keepalive_interval_ns = keepalive_interval_ns
        self.resource_linger_duration_ns = resource_linger_duration_ns
        self.idle_sleep_duration_ns = idle_sleep_duration_ns
        self.pre_touch_mapped_memory = pre_touch_mapped_memory
        self.use_conductor_agent_invoker = use_conductor_agent_invoker
        self.client_name = client_name
        self.on_error = on_error

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
    def aeron_dir(self) -> str | None:
        return self._aeron_dir

    @aeron_dir.setter
    def aeron_dir(self, value: str) -> None:
        ensure_open(self._closed, "Context")
        if self._bound:
            raise AeronStateError("Context configuration cannot be mutated after Client creation")
        self._aeron_dir = value

    def _mark_bound(self) -> None:
        ensure_open(self._closed, "Context")
        if self._bound:
            raise AeronStateError("Context instances are single-use for Client construction")
        self._bound = True

    def close(self) -> None:
        self._closed = True
