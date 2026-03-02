from __future__ import annotations

import os
import time

import pytest

from pyaeron import Client, CnC

from .support import free_udp_port


def _await_connected(client: Client, pub, sub, *, invoker: bool, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if invoker:
            client.do_work()
        if pub.is_connected and sub.is_connected:
            return
        time.sleep(0.001)
    raise TimeoutError("timed out waiting for publication/subscription connectivity")


@pytest.mark.integration
@pytest.mark.integration_extended
def test_exclusive_publication_offer_and_try_claim(client_factory) -> None:
    ctx, client = client_factory(invoker=False)
    sub = client.add_subscription("aeron:ipc", 6101, timeout=3.0)
    pub = client.add_exclusive_publication("aeron:ipc", 6101, timeout=3.0)

    try:
        _await_connected(client, pub, sub, invoker=False)

        assert pub.offer_with_retry(b"exclusive-offer", timeout=5.0) > 0

        with pub.try_claim(len(b"claimed")) as claim:
            claim.write(b"claimed")

        received: list[bytes] = []

        def on_fragment(fragment: memoryview, _header) -> None:
            received.append(bytes(fragment))

        sub.poll_until(on_fragment, min_fragments=2, timeout=8.0, copy_payload=True)
        assert received == [b"exclusive-offer", b"claimed"]
    finally:
        pub.close()
        sub.close()
        client.close()
        ctx.close()


@pytest.mark.integration
@pytest.mark.integration_extended
def test_counter_and_counters_reader(client_factory) -> None:
    ctx, client = client_factory(invoker=False)
    try:
        counter = client.add_counter(type_id=101, label="phase8-test-counter", timeout=3.0)
        try:
            constants = counter.constants
            counter.value = 1234
            assert counter.value == 1234

            reader = client.counters_reader
            assert reader.max_counter_id >= constants.counter_id
            assert reader.value(constants.counter_id) == 1234
        finally:
            counter.close()
    finally:
        client.close()
        ctx.close()


@pytest.mark.integration
@pytest.mark.integration_extended
def test_subscription_image_metadata(client_factory) -> None:
    ctx, client = client_factory(invoker=False)
    sub = client.add_subscription("aeron:ipc", 6102, timeout=3.0)
    pub = client.add_publication("aeron:ipc", 6102, timeout=3.0)

    try:
        _await_connected(client, pub, sub, invoker=False)

        assert pub.offer_with_retry(b"image-test", timeout=5.0) > 0

        session_ids: list[int] = []

        def on_fragment(_fragment: memoryview, header) -> None:
            session_ids.append(header.session_id)

        sub.poll_until(on_fragment, min_fragments=1, timeout=8.0)
        image = sub.image_by_session_id(session_ids[0])
        assert image is not None
        try:
            constants = image.constants
            assert constants.session_id == session_ids[0]
            assert constants.term_buffer_length > 0
            assert image.position >= 0
        finally:
            image.release()
    finally:
        pub.close()
        sub.close()
        client.close()
        ctx.close()


@pytest.mark.integration
@pytest.mark.integration_extended
def test_cnc_helpers(media_driver) -> None:
    with CnC(media_driver.aeron_dir, timeout_ms=5_000) as cnc:
        constants = cnc.constants
        assert constants.cnc_version > 0
        assert constants.to_driver_buffer_length > 0

        filename = cnc.filename
        assert filename is not None
        assert os.path.basename(filename) == "cnc.dat"

        assert cnc.to_driver_heartbeat_ms >= 0
        entries = cnc.read_error_log()
        assert isinstance(entries, list)

        reader = cnc.counters_reader
        assert reader.max_counter_id >= 0


@pytest.mark.integration
@pytest.mark.integration_extended
def test_destination_add_remove_api(client_factory) -> None:
    ctx, client = client_factory(invoker=False)
    control_port = free_udp_port()
    dest_port = free_udp_port()

    channel = f"aeron:udp?control-mode=manual|control=127.0.0.1:{control_port}"
    destination = f"aeron:udp?endpoint=127.0.0.1:{dest_port}"

    sub = client.add_subscription(channel, 6103, timeout=3.0)
    pub = client.add_publication(channel, 6103, timeout=3.0)
    xpub = client.add_exclusive_publication(channel, 6104, timeout=3.0)

    try:
        sub.add_destination(destination, timeout=3.0)
        sub.remove_destination(destination, timeout=3.0)

        pub.add_destination(destination, timeout=3.0)
        pub.remove_destination(destination, timeout=3.0)

        xpub.add_destination(destination, timeout=3.0)
        xpub.remove_destination(destination, timeout=3.0)
    finally:
        xpub.close()
        pub.close()
        sub.close()
        client.close()
        ctx.close()
