from __future__ import annotations

import struct
import sys
from dataclasses import dataclass
from typing import Any

import pytest
from cffi import FFI

from pyaeron.client import Client
from pyaeron.cnc import CnC
from pyaeron.context import Context
from pyaeron.counter import Counter
from pyaeron.counters_reader import CountersReader
from pyaeron.errors import (
    AeronStateError,
    BackPressuredError,
    NotConnectedError,
    ResourceClosedError,
    TimedOutError,
)
from pyaeron.exclusive_publication import ExclusivePublication
from pyaeron.image import Image
from pyaeron.publication import Publication
from pyaeron.subscription import Subscription
from pyaeron.util import coerce_buffer

_ENDIAN = "<" if sys.byteorder == "little" else ">"
_HEADER_VALUES_FMT = f"{_ENDIAN}i b B h i i i i q i Q"


class FakeLib:
    def __init__(self, ffi: FFI) -> None:
        self._ffi = ffi
        self._errmsg = ffi.new("char[]", b"fake-error")
        self._cnc_filename = ffi.new("char[]", b"/tmp/aeron/cnc.dat")

        self.client_ptr = ffi.cast("aeron_t *", 0x101)
        self.publication_ptr = ffi.cast("aeron_publication_t *", 0x201)
        self.exclusive_publication_ptr = ffi.cast("aeron_exclusive_publication_t *", 0x301)
        self.subscription_ptr = ffi.cast("aeron_subscription_t *", 0x401)
        self.counter_ptr = ffi.cast("aeron_counter_t *", 0x501)
        self.reader_ptr = ffi.cast("aeron_counters_reader_t *", 0x601)
        self.image_ptr = ffi.cast("aeron_image_t *", 0x701)
        self.cnc_ptr = ffi.cast("aeron_cnc_t *", 0x801)

        self.client_closed = False
        self.publication_closed = False
        self.exclusive_publication_closed = False
        self.subscription_closed = False
        self.counter_closed = False
        self.image_closed = False

        self.counter_value = ffi.new("int64_t *", 0)
        self.reader_values: dict[int, int] = {7: 0}

        self.publication_poll_sequence: list[bool] = [True]
        self.exclusive_poll_sequence: list[bool] = [True]
        self.subscription_poll_sequence: list[bool] = [True]
        self.counter_poll_sequence: list[bool] = [True]
        self.destination_poll_sequence: list[int] = [1]
        self.last_counter_label_length: int | None = None

        self.publication_offer_sequence: list[int] = [1]
        self.exclusive_offer_sequence: list[int] = [1]

        self._claims: list[Any] = []
        self.emit_fragment = True

    def aeron_errcode(self) -> int:
        return 0

    def aeron_errmsg(self) -> Any:
        return self._errmsg

    def aeron_init(self, client_ptr: Any, _context: Any) -> int:
        client_ptr[0] = self.client_ptr
        return 0

    def aeron_start(self, _client: Any) -> int:
        return 0

    def aeron_close(self, _client: Any) -> int:
        self.client_closed = True
        return 0

    def aeron_is_closed(self, _client: Any) -> bool:
        return self.client_closed

    def aeron_main_do_work(self, _client: Any) -> int:
        return 1

    def aeron_client_id(self, _client: Any) -> int:
        return 77

    def aeron_next_correlation_id(self, _client: Any) -> int:
        return 88

    def aeron_async_add_publication(
        self, async_ptr: Any, _client: Any, _uri: Any, _stream_id: int
    ) -> int:
        async_ptr[0] = self._ffi.cast("aeron_async_add_publication_t *", 0x1001)
        return 0

    def aeron_async_add_publication_poll(self, publication_ptr: Any, _async: Any) -> int:
        complete = (
            self.publication_poll_sequence.pop(0) if self.publication_poll_sequence else False
        )
        publication_ptr[0] = self.publication_ptr if complete else self._ffi.NULL
        return 0

    def aeron_async_add_exclusive_publication(
        self,
        async_ptr: Any,
        _client: Any,
        _uri: Any,
        _stream_id: int,
    ) -> int:
        async_ptr[0] = self._ffi.cast("aeron_async_add_exclusive_publication_t *", 0x1002)
        return 0

    def aeron_async_add_exclusive_publication_poll(self, publication_ptr: Any, _async: Any) -> int:
        complete = self.exclusive_poll_sequence.pop(0) if self.exclusive_poll_sequence else False
        publication_ptr[0] = self.exclusive_publication_ptr if complete else self._ffi.NULL
        return 0

    def aeron_async_add_subscription(self, async_ptr: Any, _client: Any, *_rest: Any) -> int:
        async_ptr[0] = self._ffi.cast("aeron_async_add_subscription_t *", 0x1003)
        return 0

    def aeron_async_add_subscription_poll(self, subscription_ptr: Any, _async: Any) -> int:
        complete = (
            self.subscription_poll_sequence.pop(0) if self.subscription_poll_sequence else False
        )
        subscription_ptr[0] = self.subscription_ptr if complete else self._ffi.NULL
        return 0

    def aeron_async_add_counter(
        self,
        async_ptr: Any,
        _client: Any,
        _type_id: int,
        _key_buffer: Any,
        _key_length: int,
        _label_buffer: Any,
        label_length: int,
    ) -> int:
        self.last_counter_label_length = int(label_length)
        async_ptr[0] = self._ffi.cast("aeron_async_add_counter_t *", 0x1004)
        return 0

    def aeron_async_add_counter_poll(self, counter_ptr: Any, _async: Any) -> int:
        complete = self.counter_poll_sequence.pop(0) if self.counter_poll_sequence else False
        counter_ptr[0] = self.counter_ptr if complete else self._ffi.NULL
        return 0

    def aeron_counters_reader(self, _client: Any) -> Any:
        return self.reader_ptr

    def aeron_counters_reader_max_counter_id(self, _reader: Any) -> int:
        return 256

    def aeron_counters_reader_addr(self, _reader: Any, counter_id: int) -> Any:
        ptr = self._ffi.new("int64_t *", self.reader_values.get(counter_id, 0))
        self._claims.append(ptr)
        return ptr

    def aeron_publication_offer(self, _pub: Any, *_rest: Any) -> int:
        if self.publication_offer_sequence:
            return self.publication_offer_sequence.pop(0)
        return 1

    def aeron_publication_try_claim(self, _pub: Any, length: int, claim_ptr: Any) -> int:
        data = self._ffi.new("uint8_t[]", length)
        claim_ptr.data = data
        claim_ptr.length = length
        self._claims.append(data)
        return 42

    def aeron_publication_is_closed(self, _pub: Any) -> bool:
        return self.publication_closed

    def aeron_publication_is_connected(self, _pub: Any) -> bool:
        return True

    def aeron_publication_close(self, _pub: Any, _handler: Any, _clientd: Any) -> int:
        self.publication_closed = True
        return 0

    def aeron_publication_async_add_destination(self, async_ptr: Any, *_rest: Any) -> int:
        async_ptr[0] = self._ffi.cast("aeron_async_destination_t *", 0x1101)
        return 0

    def aeron_publication_async_remove_destination(self, async_ptr: Any, *_rest: Any) -> int:
        async_ptr[0] = self._ffi.cast("aeron_async_destination_t *", 0x1102)
        return 0

    def aeron_publication_async_destination_poll(self, _async: Any) -> int:
        return self.destination_poll_sequence.pop(0) if self.destination_poll_sequence else 1

    def aeron_exclusive_publication_offer(self, _pub: Any, *_rest: Any) -> int:
        if self.exclusive_offer_sequence:
            return self.exclusive_offer_sequence.pop(0)
        return 1

    def aeron_exclusive_publication_try_claim(self, _pub: Any, length: int, claim_ptr: Any) -> int:
        data = self._ffi.new("uint8_t[]", length)
        claim_ptr.data = data
        claim_ptr.length = length
        self._claims.append(data)
        return 99

    def aeron_exclusive_publication_is_closed(self, _pub: Any) -> bool:
        return self.exclusive_publication_closed

    def aeron_exclusive_publication_is_connected(self, _pub: Any) -> bool:
        return True

    def aeron_exclusive_publication_close(self, _pub: Any, _handler: Any, _clientd: Any) -> int:
        self.exclusive_publication_closed = True
        return 0

    def aeron_exclusive_publication_async_add_destination(self, async_ptr: Any, *_rest: Any) -> int:
        async_ptr[0] = self._ffi.cast("aeron_async_destination_t *", 0x1201)
        return 0

    def aeron_exclusive_publication_async_remove_destination(
        self, async_ptr: Any, *_rest: Any
    ) -> int:
        async_ptr[0] = self._ffi.cast("aeron_async_destination_t *", 0x1202)
        return 0

    def aeron_exclusive_publication_async_destination_poll(self, _async: Any) -> int:
        return self.destination_poll_sequence.pop(0) if self.destination_poll_sequence else 1

    def aeron_buffer_claim_commit(self, _claim_ptr: Any) -> int:
        return 0

    def aeron_buffer_claim_abort(self, _claim_ptr: Any) -> int:
        return 0

    def aeron_subscription_poll(
        self, _sub: Any, handler: Any, _clientd: Any, _fragment_limit: int
    ) -> int:
        if self.emit_fragment:
            payload = self._ffi.new("uint8_t[]", b"abc")
            header = self._ffi.cast("aeron_header_t *", 0x141)
            handler(self._ffi.NULL, payload, 3, header)
            self._claims.append(payload)
            return 1
        return 0

    def aeron_subscription_is_closed(self, _sub: Any) -> bool:
        return self.subscription_closed

    def aeron_subscription_is_connected(self, _sub: Any) -> bool:
        return True

    def aeron_subscription_close(self, _sub: Any, _handler: Any, _clientd: Any) -> int:
        self.subscription_closed = True
        return 0

    def aeron_subscription_async_add_destination(self, async_ptr: Any, *_rest: Any) -> int:
        async_ptr[0] = self._ffi.cast("aeron_async_destination_t *", 0x1301)
        return 0

    def aeron_subscription_async_remove_destination(self, async_ptr: Any, *_rest: Any) -> int:
        async_ptr[0] = self._ffi.cast("aeron_async_destination_t *", 0x1302)
        return 0

    def aeron_subscription_async_destination_poll(self, _async: Any) -> int:
        return self.destination_poll_sequence.pop(0) if self.destination_poll_sequence else 1

    def aeron_subscription_image_count(self, _sub: Any) -> int:
        return 1

    def aeron_subscription_image_by_session_id(self, _sub: Any, _session_id: int) -> Any:
        return self.image_ptr

    def aeron_subscription_image_release(self, _sub: Any, _image: Any) -> int:
        self.image_closed = True
        return 0

    def aeron_header_values(self, _header: Any, values_ptr: Any) -> int:
        raw = struct.pack(
            _HEADER_VALUES_FMT,
            36,
            0,
            0,
            1,
            64,
            11,
            22,
            33,
            44,
            55,
            6,
        )
        for i, value in enumerate(raw):
            values_ptr.data[i] = value
        return 0

    def aeron_header_position(self, _header: Any) -> int:
        return 4096

    def aeron_image_constants(self, _image: Any, constants_ptr: Any) -> int:
        constants_ptr.source_identity = self._ffi.new("char[]", b"source")
        constants_ptr.correlation_id = 123
        constants_ptr.join_position = 10
        constants_ptr.position_bits_to_shift = 6
        constants_ptr.term_buffer_length = 65_536
        constants_ptr.mtu_length = 1408
        constants_ptr.session_id = 11
        constants_ptr.initial_term_id = 1
        constants_ptr.subscriber_position_id = 7
        return 0

    def aeron_image_position(self, _image: Any) -> int:
        return 777

    def aeron_image_is_closed(self, _image: Any) -> bool:
        return self.image_closed

    def aeron_counter_constants(self, _counter: Any, constants_ptr: Any) -> int:
        constants_ptr.registration_id = 1001
        constants_ptr.counter_id = 7
        return 0

    def aeron_counter_addr(self, _counter: Any) -> Any:
        return self.counter_value

    def aeron_counter_close(self, _counter: Any, _handler: Any, _clientd: Any) -> int:
        self.counter_closed = True
        return 0

    def aeron_counter_is_closed(self, _counter: Any) -> bool:
        return self.counter_closed

    def aeron_cnc_init(self, cnc_ptr: Any, _base_path: Any, _timeout_ms: int) -> int:
        cnc_ptr[0] = self.cnc_ptr
        return 0

    def aeron_cnc_constants(self, _cnc: Any, constants_ptr: Any) -> int:
        constants_ptr.cnc_version = 42
        constants_ptr.to_driver_buffer_length = 1024
        constants_ptr.to_clients_buffer_length = 2048
        constants_ptr.counter_metadata_buffer_length = 128
        constants_ptr.counter_values_buffer_length = 256
        constants_ptr.error_log_buffer_length = 512
        constants_ptr.client_liveness_timeout = 1_000_000
        constants_ptr.start_timestamp = 2_000_000
        constants_ptr.pid = 1234
        constants_ptr.file_page_size = 4096
        return 0

    def aeron_cnc_filename(self, _cnc: Any) -> Any:
        return self._cnc_filename

    def aeron_cnc_to_driver_heartbeat(self, _cnc: Any) -> int:
        return 987654

    def aeron_cnc_error_log_read(self, _cnc: Any, callback: Any, _clientd: Any, _since: int) -> int:
        msg = self._ffi.new("char[]", b"boom")
        callback(3, 100, 200, msg, 4, self._ffi.NULL)
        self._claims.append(msg)
        return 1

    def aeron_cnc_counters_reader(self, _cnc: Any) -> Any:
        return self.reader_ptr

    def aeron_cnc_close(self, _cnc: Any) -> None:
        return None


@dataclass
class FakeCapi:
    ffi: FFI
    lib: FakeLib

    def c_string(self, value: str) -> Any:
        return self.ffi.new("char[]", value.encode())

    def string_from_ptr(self, ptr: Any) -> str | None:
        if ptr == self.ffi.NULL:
            return None
        return self.ffi.string(ptr).decode()


@dataclass
class FakeContext:
    _capi: FakeCapi
    _ptr: Any
    use_conductor_agent_invoker: bool = False
    bound: bool = False

    def _mark_bound(self) -> None:
        self.bound = True

    @property
    def pointer(self) -> Any:
        return self._ptr


@pytest.fixture
def fake_capi() -> FakeCapi:
    ffi = FFI()
    ffi.cdef(
        """
        typedef _Bool bool;
        typedef unsigned char uint8_t;
        typedef signed int int32_t;
        typedef signed long int int64_t;
        typedef unsigned long size_t;
        typedef struct aeron_context_stct aeron_context_t;
        typedef struct aeron_stct aeron_t;
        typedef struct aeron_publication_stct aeron_publication_t;
        typedef struct aeron_exclusive_publication_stct aeron_exclusive_publication_t;
        typedef struct aeron_subscription_stct aeron_subscription_t;
        typedef struct aeron_image_stct aeron_image_t;
        typedef struct aeron_counter_stct aeron_counter_t;
        typedef struct aeron_counters_reader_stct aeron_counters_reader_t;
        typedef struct aeron_cnc_stct aeron_cnc_t;
        typedef struct aeron_header_stct aeron_header_t;
        typedef struct aeron_client_registering_resource_stct aeron_async_add_publication_t;
        typedef struct aeron_client_registering_resource_stct
            aeron_async_add_exclusive_publication_t;
        typedef struct aeron_client_registering_resource_stct aeron_async_add_subscription_t;
        typedef struct aeron_client_registering_resource_stct aeron_async_add_counter_t;
        typedef struct aeron_client_registering_resource_stct aeron_async_destination_t;
        typedef struct aeron_header_values_stct { uint8_t data[44]; } aeron_header_values_t;
        typedef struct aeron_buffer_claim_stct
        {
            uint8_t *frame_header;
            uint8_t *data;
            size_t length;
        } aeron_buffer_claim_t;
        typedef struct aeron_counter_constants_stct
        {
            int64_t registration_id;
            int32_t counter_id;
        } aeron_counter_constants_t;
        typedef struct aeron_image_constants_stct
        {
            aeron_subscription_t *subscription;
            const char *source_identity;
            int64_t correlation_id;
            int64_t join_position;
            size_t position_bits_to_shift;
            size_t term_buffer_length;
            size_t mtu_length;
            int32_t session_id;
            int32_t initial_term_id;
            int32_t subscriber_position_id;
        } aeron_image_constants_t;
        typedef struct aeron_cnc_constants_stct
        {
            int32_t cnc_version;
            int32_t to_driver_buffer_length;
            int32_t to_clients_buffer_length;
            int32_t counter_metadata_buffer_length;
            int32_t counter_values_buffer_length;
            int32_t error_log_buffer_length;
            int64_t client_liveness_timeout;
            int64_t start_timestamp;
            int64_t pid;
            int32_t file_page_size;
        } aeron_cnc_constants_t;
        """
    )
    return FakeCapi(ffi=ffi, lib=FakeLib(ffi))


def test_client_add_resources_success(fake_capi: FakeCapi) -> None:
    ctx = FakeContext(_capi=fake_capi, _ptr=fake_capi.ffi.cast("aeron_context_t *", 0x42))
    client = Client(ctx)
    assert ctx.bound is True
    assert client.client_id() == 77
    assert client.next_correlation_id() == 88

    pub = client.add_publication("aeron:ipc", 10, timeout=0.1, poll_interval=0.0)
    xpub = client.add_exclusive_publication("aeron:ipc", 11, timeout=0.1, poll_interval=0.0)
    sub = client.add_subscription("aeron:ipc", 12, timeout=0.1, poll_interval=0.0)
    counter = client.add_counter(type_id=1, label="test", timeout=0.1, poll_interval=0.0)

    assert isinstance(pub, Publication)
    assert isinstance(xpub, ExclusivePublication)
    assert isinstance(sub, Subscription)
    assert isinstance(counter, Counter)
    assert isinstance(client.counters_reader, CountersReader)

    counter.close()
    sub.close()
    xpub.close()
    pub.close()
    client.close()
    assert client.is_open is False
    with pytest.raises(ResourceClosedError):
        _ = client.pointer


def test_client_add_publication_timeout(fake_capi: FakeCapi) -> None:
    fake_capi.lib.publication_poll_sequence = [False]
    ctx = FakeContext(_capi=fake_capi, _ptr=fake_capi.ffi.cast("aeron_context_t *", 0x43))
    client = Client(ctx)
    with pytest.raises(TimedOutError):
        client.add_publication("aeron:ipc", 10, timeout=0.0, poll_interval=0.0)


def test_client_add_counter_uses_utf8_byte_length(fake_capi: FakeCapi) -> None:
    ctx = FakeContext(_capi=fake_capi, _ptr=fake_capi.ffi.cast("aeron_context_t *", 0x44))
    client = Client(ctx)
    counter = client.add_counter(type_id=1, label="naive-π", timeout=0.1, poll_interval=0.0)
    try:
        assert fake_capi.lib.last_counter_label_length == len("naive-π".encode())
    finally:
        counter.close()
        client.close()


def test_publication_offer_retry_try_claim_and_destinations(fake_capi: FakeCapi) -> None:
    pub = Publication(
        capi=fake_capi,
        ptr=fake_capi.lib.publication_ptr,
        client_ptr=fake_capi.lib.client_ptr,
        channel="aeron:ipc",
        stream_id=1,
    )
    fake_capi.lib.publication_offer_sequence = [-1, -2, 123]
    assert pub.offer_with_retry(b"abc", timeout=0.1, poll_interval=0.0) == 123

    with pub.try_claim(3) as claim:
        claim.write(b"xyz")
        assert bytes(claim.data) == b"xyz"

    fake_capi.lib.destination_poll_sequence = [0, 1]
    pub.add_destination("aeron:udp?endpoint=127.0.0.1:9999", timeout=0.1, poll_interval=0.0)
    fake_capi.lib.destination_poll_sequence = [0, 1]
    pub.remove_destination("aeron:udp?endpoint=127.0.0.1:9999", timeout=0.1, poll_interval=0.0)

    pub.close()
    assert pub.is_open is False
    with pytest.raises(ResourceClosedError):
        pub.offer(b"x")


def test_exclusive_publication_try_claim_and_destinations(fake_capi: FakeCapi) -> None:
    pub = ExclusivePublication(
        capi=fake_capi,
        ptr=fake_capi.lib.exclusive_publication_ptr,
        client_ptr=fake_capi.lib.client_ptr,
        channel="aeron:ipc",
        stream_id=2,
    )

    assert pub.offer(b"abc") == 1
    with pub.try_claim(4) as claim:
        claim.write(b"wxyz")
        assert claim.position == 99

    fake_capi.lib.destination_poll_sequence = [1]
    pub.add_destination("aeron:udp?endpoint=127.0.0.1:8888", timeout=0.1, poll_interval=0.0)
    fake_capi.lib.destination_poll_sequence = [1]
    pub.remove_destination("aeron:udp?endpoint=127.0.0.1:8888", timeout=0.1, poll_interval=0.0)
    pub.close()
    assert pub.is_open is False


def test_subscription_poll_and_images(fake_capi: FakeCapi) -> None:
    sub = Subscription(
        capi=fake_capi,
        ptr=fake_capi.lib.subscription_ptr,
        client_ptr=fake_capi.lib.client_ptr,
        channel="aeron:ipc",
        stream_id=3,
    )

    received: list[tuple[bytes, int]] = []

    def handler(fragment: memoryview, header: Any) -> None:
        received.append((bytes(fragment), header.session_id))

    assert sub.poll(handler, fragment_limit=1) == 1
    assert received == [(b"abc", 11)]
    assert sub.image_count == 1

    image = sub.image_by_session_id(11)
    assert isinstance(image, Image)
    assert image is not None
    constants = image.constants
    assert constants.source_identity == "source"
    assert image.position == 777
    image.release()

    fake_capi.lib.destination_poll_sequence = [1]
    sub.add_destination("aeron:udp?endpoint=127.0.0.1:7777", timeout=0.1, poll_interval=0.0)
    fake_capi.lib.destination_poll_sequence = [1]
    sub.remove_destination("aeron:udp?endpoint=127.0.0.1:7777", timeout=0.1, poll_interval=0.0)
    sub.close()
    assert sub.is_open is False


def test_subscription_poll_exception_propagates(fake_capi: FakeCapi) -> None:
    sub = Subscription(
        capi=fake_capi,
        ptr=fake_capi.lib.subscription_ptr,
        client_ptr=fake_capi.lib.client_ptr,
        channel="aeron:ipc",
        stream_id=4,
    )

    def handler(_fragment: memoryview, _header: Any) -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        sub.poll(handler, fragment_limit=1)


def test_subscription_poll_until_timeout(fake_capi: FakeCapi) -> None:
    sub = Subscription(
        capi=fake_capi,
        ptr=fake_capi.lib.subscription_ptr,
        client_ptr=fake_capi.lib.client_ptr,
        channel="aeron:ipc",
        stream_id=5,
    )
    fake_capi.lib.emit_fragment = False
    with pytest.raises(TimedOutError):
        sub.poll_until(lambda _f, _h: None, timeout=0.0, poll_interval=0.0)
    with pytest.raises(ValueError):
        sub.poll(lambda _f, _h: None, fragment_limit=0)
    with pytest.raises(ValueError):
        sub.poll_until(lambda _f, _h: None, min_fragments=0)


def test_counter_reader_and_close(fake_capi: FakeCapi) -> None:
    counter = Counter(fake_capi, fake_capi.lib.counter_ptr)
    constants = counter.constants
    assert constants.counter_id == 7

    counter.value = 15
    assert counter.value == 15

    reader = CountersReader(fake_capi, fake_capi.lib.reader_ptr)
    fake_capi.lib.reader_values[7] = 15
    assert reader.max_counter_id == 256
    assert reader.value(7) == 15

    counter.close()
    with pytest.raises(ResourceClosedError):
        _ = counter.value


def test_cnc_wrappers(fake_capi: FakeCapi, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pyaeron.cnc.load_libaeron", lambda: fake_capi)
    with CnC("/tmp/aeron", timeout_ms=1_000) as cnc:
        assert cnc.filename == "/tmp/aeron/cnc.dat"
        assert cnc.to_driver_heartbeat_ms == 987654
        assert cnc.constants.cnc_version == 42

        errors = cnc.read_error_log()
        assert len(errors) == 1
        assert errors[0].error == "boom"

        reader = cnc.counters_reader
        assert reader.max_counter_id == 256


def test_buffer_claim_abort_and_finalize_state(fake_capi: FakeCapi) -> None:
    pub = Publication(
        capi=fake_capi,
        ptr=fake_capi.lib.publication_ptr,
        client_ptr=fake_capi.lib.client_ptr,
        channel="aeron:ipc",
        stream_id=6,
    )
    claim = pub.try_claim(4)
    claim.abort()
    assert claim.is_finalized is True
    with pytest.raises(RuntimeError):
        claim.write(b"a")


def test_destination_timeout_branches(fake_capi: FakeCapi) -> None:
    pub = Publication(
        capi=fake_capi,
        ptr=fake_capi.lib.publication_ptr,
        client_ptr=fake_capi.lib.client_ptr,
        channel="aeron:ipc",
        stream_id=7,
    )
    fake_capi.lib.destination_poll_sequence = [0]
    with pytest.raises(TimedOutError):
        pub.add_destination("aeron:udp?endpoint=127.0.0.1:10000", timeout=0.0, poll_interval=0.0)

    xpub = ExclusivePublication(
        capi=fake_capi,
        ptr=fake_capi.lib.exclusive_publication_ptr,
        client_ptr=fake_capi.lib.client_ptr,
        channel="aeron:ipc",
        stream_id=8,
    )
    fake_capi.lib.destination_poll_sequence = [0]
    with pytest.raises(TimedOutError):
        xpub.remove_destination(
            "aeron:udp?endpoint=127.0.0.1:10001",
            timeout=0.0,
            poll_interval=0.0,
        )

    sub = Subscription(
        capi=fake_capi,
        ptr=fake_capi.lib.subscription_ptr,
        client_ptr=fake_capi.lib.client_ptr,
        channel="aeron:ipc",
        stream_id=9,
    )
    fake_capi.lib.destination_poll_sequence = [0]
    with pytest.raises(TimedOutError):
        sub.add_destination("aeron:udp?endpoint=127.0.0.1:10002", timeout=0.0, poll_interval=0.0)


def test_offer_with_retry_timeout(fake_capi: FakeCapi) -> None:
    pub = Publication(
        capi=fake_capi,
        ptr=fake_capi.lib.publication_ptr,
        client_ptr=fake_capi.lib.client_ptr,
        channel="aeron:ipc",
        stream_id=10,
    )
    fake_capi.lib.publication_offer_sequence = [-1]
    with pytest.raises(NotConnectedError):
        pub.offer_with_retry(b"x", timeout=0.0, poll_interval=0.0)

    xpub = ExclusivePublication(
        capi=fake_capi,
        ptr=fake_capi.lib.exclusive_publication_ptr,
        client_ptr=fake_capi.lib.client_ptr,
        channel="aeron:ipc",
        stream_id=11,
    )
    fake_capi.lib.exclusive_offer_sequence = [-2]
    with pytest.raises(BackPressuredError):
        xpub.offer_with_retry(b"x", timeout=0.0, poll_interval=0.0)


def test_coerce_buffer_non_contiguous_path() -> None:
    src = memoryview(bytearray(b"abcd"))[::2]
    mv = coerce_buffer(src)
    assert bytes(mv) == b"ac"


@dataclass
class FakeContextState:
    dir_ptr: Any
    driver_timeout_ms: int = 10_000
    keepalive_interval_ns: int = 500_000_000
    resource_linger_duration_ns: int = 3_000_000_000
    idle_sleep_duration_ns: int = 16_000_000
    pre_touch_mapped_memory: bool = False
    use_conductor_agent_invoker: bool = False
    client_name_ptr: Any = None
    closed: bool = False


class FakeContextLib:
    def __init__(self, ffi: FFI) -> None:
        self._ffi = ffi
        self._state = FakeContextState(
            dir_ptr=ffi.new("char[]", b"/tmp/aeron"),
            client_name_ptr=ffi.new("char[]", b"default"),
        )
        self._context_ptr = ffi.cast("aeron_context_t *", 0x9901)

    def aeron_errcode(self) -> int:
        return 0

    def aeron_errmsg(self) -> Any:
        return self._ffi.new("char[]", b"fake-error")

    def aeron_context_init(self, ptr: Any) -> int:
        ptr[0] = self._context_ptr
        return 0

    def aeron_context_close(self, _ptr: Any) -> int:
        self._state.closed = True
        return 0

    def aeron_context_set_dir(self, _ptr: Any, value: Any) -> int:
        self._state.dir_ptr = value
        return 0

    def aeron_context_get_dir(self, _ptr: Any) -> Any:
        return self._state.dir_ptr

    def aeron_context_set_driver_timeout_ms(self, _ptr: Any, value: int) -> int:
        self._state.driver_timeout_ms = value
        return 0

    def aeron_context_get_driver_timeout_ms(self, _ptr: Any) -> int:
        return self._state.driver_timeout_ms

    def aeron_context_set_keepalive_interval_ns(self, _ptr: Any, value: int) -> int:
        self._state.keepalive_interval_ns = value
        return 0

    def aeron_context_get_keepalive_interval_ns(self, _ptr: Any) -> int:
        return self._state.keepalive_interval_ns

    def aeron_context_set_resource_linger_duration_ns(self, _ptr: Any, value: int) -> int:
        self._state.resource_linger_duration_ns = value
        return 0

    def aeron_context_get_resource_linger_duration_ns(self, _ptr: Any) -> int:
        return self._state.resource_linger_duration_ns

    def aeron_context_set_idle_sleep_duration_ns(self, _ptr: Any, value: int) -> int:
        self._state.idle_sleep_duration_ns = value
        return 0

    def aeron_context_get_idle_sleep_duration_ns(self, _ptr: Any) -> int:
        return self._state.idle_sleep_duration_ns

    def aeron_context_set_pre_touch_mapped_memory(self, _ptr: Any, value: bool) -> int:
        self._state.pre_touch_mapped_memory = value
        return 0

    def aeron_context_get_pre_touch_mapped_memory(self, _ptr: Any) -> bool:
        return self._state.pre_touch_mapped_memory

    def aeron_context_set_use_conductor_agent_invoker(self, _ptr: Any, value: bool) -> int:
        self._state.use_conductor_agent_invoker = value
        return 0

    def aeron_context_get_use_conductor_agent_invoker(self, _ptr: Any) -> bool:
        return self._state.use_conductor_agent_invoker

    def aeron_context_set_client_name(self, _ptr: Any, value: Any) -> int:
        self._state.client_name_ptr = value
        return 0

    def aeron_context_get_client_name(self, _ptr: Any) -> Any:
        return self._state.client_name_ptr


def _fake_context_capi() -> Any:
    ffi = FFI()
    ffi.cdef(
        """
        typedef _Bool bool;
        typedef unsigned long int uint64_t;
        typedef struct aeron_context_stct aeron_context_t;
        """
    )
    lib = FakeContextLib(ffi)
    return type(
        "FakeContextCapi",
        (),
        {
            "ffi": ffi,
            "lib": lib,
            "c_string": staticmethod(lambda v: ffi.new("char[]", v.encode())),
            "string_from_ptr": staticmethod(
                lambda p: None if p == ffi.NULL else ffi.string(p).decode()
            ),
        },
    )()


def test_context_unit_behavior_without_real_libaeron(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _fake_context_capi()
    monkeypatch.setattr("pyaeron.context.load_libaeron", lambda: fake)

    with Context(
        aeron_dir="/tmp/ctx",
        driver_timeout_ms=11_000,
        keepalive_interval_ns=222_000_000,
        resource_linger_duration_ns=333_000_000,
        idle_sleep_duration_ns=1_000,
        pre_touch_mapped_memory=True,
        use_conductor_agent_invoker=True,
        client_name="unit-test",
    ) as ctx:
        assert ctx.aeron_dir == "/tmp/ctx"
        assert ctx.driver_timeout_ms == 11_000
        assert ctx.keepalive_interval_ns == 222_000_000
        assert ctx.resource_linger_duration_ns == 333_000_000
        assert ctx.idle_sleep_duration_ns == 1_000
        assert ctx.pre_touch_mapped_memory is True
        assert ctx.use_conductor_agent_invoker is True
        assert ctx.client_name == "unit-test"

        ctx._mark_bound()
        with pytest.raises(AeronStateError):
            ctx.aeron_dir = "/tmp/blocked"

    assert ctx.closed is True
