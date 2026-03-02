from pyaeron.handlers import FragmentCallbackAdapter, copy_fragment
from pyaeron.types import Header


def _header() -> Header:
    return Header(
        frame_length=1,
        version=0,
        flags=0,
        type=0,
        term_offset=0,
        session_id=1,
        stream_id=2,
        term_id=3,
        reserved_value=0,
        position=0,
        initial_term_id=0,
        position_bits_to_shift=0,
    )


def test_copy_fragment_returns_bytes_copy() -> None:
    src = memoryview(b"abc")
    copied = copy_fragment(src)
    assert copied == b"abc"
    assert isinstance(copied, bytes)


def test_fragment_callback_adapter_copy_mode() -> None:
    received: list[bytes] = []

    def handler(fragment: memoryview, _header: Header) -> None:
        received.append(bytes(fragment))

    adapter = FragmentCallbackAdapter(handler, copy_payload=True)
    adapter(memoryview(b"payload"), _header())
    assert received == [b"payload"]
