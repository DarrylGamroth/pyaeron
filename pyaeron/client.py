from __future__ import annotations

import time
from types import TracebackType
from typing import Any

from .context import Context
from .counter import Counter
from .counters_reader import CountersReader
from .errors import TimedOutError, check_rc
from .exclusive_publication import ExclusivePublication
from .publication import Publication
from .subscription import Subscription
from .util import ensure_open


class Client:
    """High-level client lifecycle wrapper."""

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
    def counters_reader(self) -> CountersReader:
        ensure_open(self._closed, "Client")
        return CountersReader(self._capi, self._capi.lib.aeron_counters_reader(self._ptr))

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
                    client_ptr=self._ptr,
                    channel=channel,
                    stream_id=stream_id,
                )

            if deadline is not None and time.monotonic() >= deadline:
                raise TimedOutError(
                    f"Timed out waiting for publication: channel={channel!r}, stream_id={stream_id}"
                )

            self._wait_iteration(poll_interval)

    def add_exclusive_publication(
        self,
        channel: str,
        stream_id: int,
        *,
        timeout: float | None = 10.0,
        poll_interval: float = 0.001,
    ) -> ExclusivePublication:
        ensure_open(self._closed, "Client")
        async_ptr = self._capi.ffi.new("aeron_async_add_exclusive_publication_t **")
        check_rc(
            self._capi.lib.aeron_async_add_exclusive_publication(
                async_ptr,
                self._ptr,
                self._capi.c_string(channel),
                stream_id,
            ),
            capi=self._capi,
        )

        deadline = None if timeout is None else time.monotonic() + timeout
        publication_ptr = self._capi.ffi.new("aeron_exclusive_publication_t **")
        while True:
            check_rc(
                self._capi.lib.aeron_async_add_exclusive_publication_poll(
                    publication_ptr,
                    async_ptr[0],
                ),
                capi=self._capi,
            )
            if publication_ptr[0] != self._capi.ffi.NULL:
                return ExclusivePublication(
                    capi=self._capi,
                    ptr=publication_ptr[0],
                    client_ptr=self._ptr,
                    channel=channel,
                    stream_id=stream_id,
                )

            if deadline is not None and time.monotonic() >= deadline:
                raise TimedOutError(
                    "Timed out waiting for exclusive publication: "
                    f"channel={channel!r}, stream_id={stream_id}"
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
                    client_ptr=self._ptr,
                    channel=channel,
                    stream_id=stream_id,
                )

            if deadline is not None and time.monotonic() >= deadline:
                raise TimedOutError(
                    "Timed out waiting for subscription: "
                    f"channel={channel!r}, stream_id={stream_id}"
                )

            self._wait_iteration(poll_interval)

    def add_counter(
        self,
        *,
        type_id: int,
        label: str,
        key: bytes | bytearray | memoryview = b"",
        timeout: float | None = 10.0,
        poll_interval: float = 0.001,
    ) -> Counter:
        ensure_open(self._closed, "Client")
        key_mv = memoryview(key)
        if key_mv.format != "B":
            key_mv = key_mv.cast("B")
        if not key_mv.c_contiguous:
            key_mv = memoryview(bytes(key_mv))
        label_bytes = label.encode("utf-8")
        label_c = self._capi.ffi.new("char[]", label_bytes)

        async_ptr = self._capi.ffi.new("aeron_async_add_counter_t **")
        check_rc(
            self._capi.lib.aeron_async_add_counter(
                async_ptr,
                self._ptr,
                type_id,
                self._capi.ffi.from_buffer(key_mv) if len(key_mv) > 0 else self._capi.ffi.NULL,
                len(key_mv),
                label_c,
                len(label_bytes),
            ),
            capi=self._capi,
        )

        deadline = None if timeout is None else time.monotonic() + timeout
        counter_ptr = self._capi.ffi.new("aeron_counter_t **")
        while True:
            check_rc(
                self._capi.lib.aeron_async_add_counter_poll(counter_ptr, async_ptr[0]),
                capi=self._capi,
            )
            if counter_ptr[0] != self._capi.ffi.NULL:
                return Counter(self._capi, counter_ptr[0])

            if deadline is not None and time.monotonic() >= deadline:
                raise TimedOutError(f"Timed out waiting for counter registration: label={label!r}")

            self._wait_iteration(poll_interval)

    def _wait_iteration(self, poll_interval: float) -> None:
        if self._context.use_conductor_agent_invoker:
            self.do_work()
        if poll_interval > 0:
            time.sleep(poll_interval)
