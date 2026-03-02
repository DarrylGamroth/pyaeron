import time

import pytest

from pyaeron import Client, Context, TimedOutError
from pyaeron._capi import try_load_libaeron


def _await_connected(pub, sub, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pub.is_connected and sub.is_connected:
            return
        time.sleep(0.001)
    raise TimedOutError("Timed out waiting for publication/subscription connection")


def _offer_and_poll_once(client: Client, channel: str, stream_id: int) -> None:
    sub = None
    pub = None
    try:
        sub = client.add_subscription(channel, stream_id, timeout=3.0, poll_interval=0.001)
        pub = client.add_publication(channel, stream_id, timeout=3.0, poll_interval=0.001)
        _await_connected(pub, sub, timeout=5.0)

        payload = b"hello pyaeron phase5"
        position = pub.offer_with_retry(payload, timeout=5.0, poll_interval=0.0005)
        assert position > 0

        received: list[bytes] = []
        received_stream_ids: list[int] = []

        def on_fragment(fragment: memoryview, header) -> None:
            received.append(bytes(fragment))
            received_stream_ids.append(header.stream_id)

        sub.poll_until(
            on_fragment,
            fragment_limit=10,
            min_fragments=1,
            timeout=5.0,
            poll_interval=0.001,
            copy_payload=True,
        )

        assert received == [payload]
        assert received_stream_ids == [stream_id]
    finally:
        if pub is not None:
            pub.close()
        if sub is not None:
            sub.close()


@pytest.mark.integration
def test_pubsub_ipc_mvp() -> None:
    if try_load_libaeron() is None:
        pytest.skip("libaeron unavailable")

    try:
        with Context() as ctx, Client(ctx) as client:
            _offer_and_poll_once(client, "aeron:ipc", 3001)
    except TimedOutError as exc:
        pytest.skip(f"media driver/runtime unavailable for IPC test: {exc}")


@pytest.mark.integration
def test_pubsub_udp_mvp() -> None:
    if try_load_libaeron() is None:
        pytest.skip("libaeron unavailable")

    try:
        with Context() as ctx, Client(ctx) as client:
            _offer_and_poll_once(client, "aeron:udp?endpoint=localhost:20121", 3002)
    except TimedOutError as exc:
        pytest.skip(f"media driver/runtime unavailable for UDP test: {exc}")
