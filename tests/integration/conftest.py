from __future__ import annotations

import os

import pytest

from pyaeron import Client, Context
from pyaeron._capi import try_load_libaeron

from .support import MediaDriverHarness, find_aeronmd_binary


@pytest.fixture
def media_driver() -> MediaDriverHarness:
    if try_load_libaeron() is None:
        pytest.skip("libaeron unavailable")

    binary = find_aeronmd_binary()
    if binary is None:
        pytest.skip(
            "aeronmd binary not found "
            "(set AERON_MD_BINARY or install /opt/aeron/bin/aeronmd)"
        )

    harness = MediaDriverHarness.launch(binary)
    try:
        yield harness
    finally:
        harness.close()


@pytest.fixture
def client_factory(media_driver: MediaDriverHarness):
    def factory(*, invoker: bool = False) -> tuple[Context, Client]:
        ctx = Context(aeron_dir=media_driver.aeron_dir)
        ctx.use_conductor_agent_invoker = invoker
        client = Client(ctx)
        return ctx, client

    return factory


@pytest.fixture(autouse=True)
def _default_libaeron_path() -> None:
    """Set a sensible default library path for local deterministic integration runs."""
    if "AERON_LIBRARY_PATH" not in os.environ:
        candidate = "/opt/aeron/lib/libaeron.so"
        if os.path.exists(candidate):
            os.environ["AERON_LIBRARY_PATH"] = candidate
