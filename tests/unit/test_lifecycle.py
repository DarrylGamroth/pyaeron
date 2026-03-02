import pytest

from pyaeron import Context
from pyaeron._capi import try_load_libaeron

pytestmark = pytest.mark.skipif(try_load_libaeron() is None, reason="libaeron unavailable")


def test_context_close_is_idempotent() -> None:
    ctx = Context(aeron_dir="/tmp/aeron")
    assert ctx.closed is False
    ctx.close()
    ctx.close()
    assert ctx.closed is True


def test_context_configuration_round_trip() -> None:
    with Context() as ctx:
        ctx.aeron_dir = "/tmp/aeron-ctx-roundtrip"
        assert ctx.aeron_dir == "/tmp/aeron-ctx-roundtrip"

        ctx.driver_timeout_ms = 11_000
        assert ctx.driver_timeout_ms == 11_000

        ctx.keepalive_interval_ns = 222_000_000
        assert ctx.keepalive_interval_ns == 222_000_000

        ctx.resource_linger_duration_ns = 333_000_000
        assert ctx.resource_linger_duration_ns == 333_000_000

        ctx.idle_sleep_duration_ns = 1_000
        assert ctx.idle_sleep_duration_ns == 1_000

        ctx.pre_touch_mapped_memory = True
        assert ctx.pre_touch_mapped_memory is True

        ctx.use_conductor_agent_invoker = True
        assert ctx.use_conductor_agent_invoker is True
