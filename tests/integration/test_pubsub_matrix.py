import time

import pytest

from pyaeron import (
    AdminActionError,
    BackPressuredError,
    Client,
    NotConnectedError,
    TimedOutError,
)

from .support import free_udp_port


def _await_connected(client: Client, pub, sub, *, invoker: bool, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if invoker:
            client.do_work()
        if pub.is_connected and sub.is_connected:
            return
        time.sleep(0.001)
    raise TimeoutError(
        f"Timed out waiting for publication/subscription connectivity after {timeout:.3f}s"
    )


def _send_and_receive_messages(
    client: Client,
    channel: str,
    stream_id: int,
    *,
    count: int,
    invoker: bool,
) -> list[bytes]:
    sub = client.add_subscription(channel, stream_id, timeout=3.0, poll_interval=0.001)
    pub = client.add_publication(channel, stream_id, timeout=3.0, poll_interval=0.001)

    try:
        _await_connected(client, pub, sub, invoker=invoker, timeout=5.0)
        sent = [f"msg-{i}".encode() for i in range(count)]
        for payload in sent:
            pos = pub.offer_with_retry(payload, timeout=5.0, poll_interval=0.0005)
            assert pos > 0

        received: list[bytes] = []

        def on_fragment(fragment: memoryview, _header) -> None:
            received.append(bytes(fragment))

        sub.poll_until(
            on_fragment,
            min_fragments=count,
            fragment_limit=20,
            timeout=8.0,
            poll_interval=0.001,
            copy_payload=True,
        )
        return received
    finally:
        pub.close()
        sub.close()


@pytest.mark.integration
@pytest.mark.integration_extended
@pytest.mark.parametrize("invoker", [False, True], ids=["threaded", "invoker"])
@pytest.mark.parametrize("channel_kind", ["ipc", "udp"], ids=["ipc", "udp"])
def test_pubsub_matrix(client_factory, channel_kind: str, invoker: bool) -> None:
    if channel_kind == "ipc":
        channel = "aeron:ipc"
    else:
        port = free_udp_port()
        channel = f"aeron:udp?endpoint=127.0.0.1:{port}"

    stream_id = 5000 + (100 if invoker else 0) + (1 if channel_kind == "udp" else 0)
    ctx, client = client_factory(invoker=invoker)
    try:
        received = _send_and_receive_messages(client, channel, stream_id, count=32, invoker=invoker)
        assert received == [f"msg-{i}".encode() for i in range(32)]
    finally:
        client.close()
        ctx.close()


@pytest.mark.integration
@pytest.mark.integration_extended
def test_offer_with_retry_timeout_without_subscriber(client_factory) -> None:
    ctx, client = client_factory(invoker=False)
    try:
        pub = client.add_publication("aeron:ipc", 5999, timeout=3.0, poll_interval=0.001)
        try:
            with pytest.raises((NotConnectedError, BackPressuredError, AdminActionError)):
                pub.offer_with_retry(
                    b"no-subscriber-yet",
                    timeout=0.05,
                    poll_interval=0.001,
                )
        finally:
            pub.close()
    except TimedOutError as exc:
        pytest.skip(f"runtime not ready for retry timeout test: {exc}")
    finally:
        client.close()
        ctx.close()
