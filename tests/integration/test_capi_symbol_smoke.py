import pytest

from pyaeron._capi import load_libaeron, try_load_libaeron


@pytest.mark.integration
def test_libaeron_symbol_smoke() -> None:
    if try_load_libaeron() is None:
        pytest.skip("libaeron not available in current environment")

    capi = load_libaeron()
    assert hasattr(capi.lib, "aeron_context_init")
    assert hasattr(capi.lib, "aeron_async_add_publication")
    assert hasattr(capi.lib, "aeron_publication_offer")

    # Safe no-argument calls for smoke validation.
    assert isinstance(capi.lib.aeron_errcode(), int)
    msg_ptr = capi.lib.aeron_errmsg()
    assert msg_ptr == capi.ffi.NULL or isinstance(capi.string_from_ptr(msg_ptr), str)
