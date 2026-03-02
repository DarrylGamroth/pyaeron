from __future__ import annotations

import time
from types import TracebackType
from typing import Any

from .context import Context
from .errors import TimedOutError, check_rc
from .publication import Publication
from .subscription import Subscription
from .util import ensure_open


class Client:
    """High-level client lifecycle wrapper.

    Phase 1 provides deterministic lifecycle behavior and API shape.
    """

    def __init__(self, context: Context) -> None:
        context._mark_bound()
        self._capi = context._capi
        client_ptr = self._capi.ffi.new("aeron_t **")
        try:
            check_rc(self._capi.lib.aeron_init(client_ptr, context.pointer), capi=self._capi)
            self._ptr = client_ptr[0]
            check_rc(self._capi.lib.aeron_start(self._ptr), capi=self._capi)
        except Exception:
            if client_ptr[0] != self._capi.ffi.NULL:
                # Best-effort cleanup for partially initialized clients.
                self._capi.lib.aeron_close(client_ptr[0])
            raise

        self._context = context
        self._closed = False

    def __enter__(self) -> Client:
        ensure_open(self._closed, "Client")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    @property
    def is_open(self) -> bool:
        if self._closed:
            return False
        return not bool(self._capi.lib.aeron_is_closed(self._ptr))

    def close(self) -> None:
        if self._closed:
            return
        check_rc(self._capi.lib.aeron_close(self._ptr), capi=self._capi)
        self._ptr = self._capi.ffi.NULL
        self._closed = True

    def do_work(self) -> int:
        ensure_open(self._closed, "Client")
        return int(check_rc(self._capi.lib.aeron_main_do_work(self._ptr), capi=self._capi))

    def client_id(self) -> int:
        ensure_open(self._closed, "Client")
        value = int(self._capi.lib.aeron_client_id(self._ptr))
        if value < 0:
            check_rc(-1, capi=self._capi)
        return value

    def next_correlation_id(self) -> int:
        ensure_open(self._closed, "Client")
        value = int(self._capi.lib.aeron_next_correlation_id(self._ptr))
        if value < 0:
            check_rc(-1, capi=self._capi)
        return value

    @property
    def pointer(self) -> Any:
        ensure_open(self._closed, "Client")
        return self._ptr

    def add_publication(
        self,
        channel: str,
        stream_id: int,
        *,
        timeout: float | None = 10.0,
        poll_interval: float = 0.001,
    ) -> Publication:
        ensure_open(self._closed, "Client")
        async_ptr = self._capi.ffi.new("aeron_async_add_publication_t **")
        check_rc(
            self._capi.lib.aeron_async_add_publication(
                async_ptr,
                self._ptr,
                self._capi.c_string(channel),
                stream_id,
            ),
            capi=self._capi,
        )

        deadline = None if timeout is None else time.monotonic() + timeout
        publication_ptr = self._capi.ffi.new("aeron_publication_t **")
        while True:
            check_rc(
                self._capi.lib.aeron_async_add_publication_poll(publication_ptr, async_ptr[0]),
                capi=self._capi,
            )
            if publication_ptr[0] != self._capi.ffi.NULL:
                return Publication(
                    capi=self._capi,
                    ptr=publication_ptr[0],
                    channel=channel,
                    stream_id=stream_id,
                )

            if deadline is not None and time.monotonic() >= deadline:
                raise TimedOutError(
                    f"Timed out waiting for publication: channel={channel!r}, stream_id={stream_id}"
                )

            self._wait_iteration(poll_interval)

    def add_subscription(
        self,
        channel: str,
        stream_id: int,
        *,
        timeout: float | None = 10.0,
        poll_interval: float = 0.001,
    ) -> Subscription:
        ensure_open(self._closed, "Client")
        async_ptr = self._capi.ffi.new("aeron_async_add_subscription_t **")
        check_rc(
            self._capi.lib.aeron_async_add_subscription(
                async_ptr,
                self._ptr,
                self._capi.c_string(channel),
                stream_id,
                self._capi.ffi.NULL,
                self._capi.ffi.NULL,
                self._capi.ffi.NULL,
                self._capi.ffi.NULL,
            ),
            capi=self._capi,
        )

        deadline = None if timeout is None else time.monotonic() + timeout
        subscription_ptr = self._capi.ffi.new("aeron_subscription_t **")
        while True:
            check_rc(
                self._capi.lib.aeron_async_add_subscription_poll(subscription_ptr, async_ptr[0]),
                capi=self._capi,
            )
            if subscription_ptr[0] != self._capi.ffi.NULL:
                return Subscription(
                    capi=self._capi,
                    ptr=subscription_ptr[0],
                    channel=channel,
                    stream_id=stream_id,
                )

            if deadline is not None and time.monotonic() >= deadline:
                raise TimedOutError(
                    "Timed out waiting for subscription: "
                    f"channel={channel!r}, stream_id={stream_id}"
                )

            self._wait_iteration(poll_interval)

    def _wait_iteration(self, poll_interval: float) -> None:
        if self._context.use_conductor_agent_invoker:
            self.do_work()
        if poll_interval > 0:
            time.sleep(poll_interval)
