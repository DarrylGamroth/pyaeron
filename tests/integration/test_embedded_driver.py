from __future__ import annotations

import time

import pytest

from pyaeron import Client, Context, MediaDriver
from pyaeron._capi import try_load_libaeron
from pyaeron._driver_capi import try_load_libaeron_driver

pytestmark = pytest.mark.skipif(
    try_load_libaeron() is None or try_load_libaeron_driver() is None,
    reason="libaeron or libaeron_driver unavailable",
)


def _await_connected(client: Client, pub, sub, *, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pub.is_connected and sub.is_connected:
            return
        time.sleep(0.001)
    raise TimeoutError("timed out waiting for publication/subscription connectivity")


@pytest.mark.integration
@pytest.mark.integration_extended
def test_embedded_media_driver_pubsub_roundtrip() -> None:
    with MediaDriver.launch_embedded() as driver:
        aeron_dir = driver.aeron_dir
        assert aeron_dir is not None

        with Context(aeron_dir=aeron_dir) as ctx, Client(ctx) as client:
            sub = client.add_subscription("aeron:ipc", 6201, timeout=3.0)
            pub = client.add_publication("aeron:ipc", 6201, timeout=3.0)
            try:
                _await_connected(client, pub, sub)

                expected = [f"embedded-{i}".encode() for i in range(4)]
                for payload in expected:
                    assert pub.offer_with_retry(payload, timeout=5.0) > 0

                received: list[bytes] = []

                def on_fragment(fragment: memoryview, _header) -> None:
                    received.append(bytes(fragment))

                sub.poll_until(
                    on_fragment,
                    min_fragments=len(expected),
                    timeout=8.0,
                    copy_payload=True,
                )
                assert received == expected
            finally:
                pub.close()
                sub.close()
