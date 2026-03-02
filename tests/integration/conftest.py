from __future__ import annotations

import os
from dataclasses import dataclass

import pytest

from pyaeron import Client, Context
from pyaeron._capi import try_load_libaeron

from .support import MediaDriverHarness, find_aeronmd_binary


@dataclass(slots=True)
class ExternalMediaDriverHarness:
    aeron_dir: str

    def close(self) -> None:
        return None


@pytest.fixture
def media_driver() -> MediaDriverHarness | ExternalMediaDriverHarness:
    if try_load_libaeron() is None:
        pytest.skip("libaeron unavailable")

    external_dir = os.environ.get("AERON_EXTERNAL_MEDIA_DRIVER_DIR")
    if external_dir:
        if not os.path.exists(os.path.join(external_dir, "cnc.dat")):
            pytest.skip(f"AERON_EXTERNAL_MEDIA_DRIVER_DIR does not contain cnc.dat: {external_dir}")
        yield ExternalMediaDriverHarness(aeron_dir=external_dir)
        return

    binary = find_aeronmd_binary()
    if binary is None:
        pytest.skip(
            "aeronmd binary not found (set AERON_MD_BINARY or install /opt/aeron/bin/aeronmd)"
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
    if "AERON_DRIVER_LIBRARY_PATH" not in os.environ:
        candidate = "/opt/aeron/lib/libaeron_driver.so"
        if os.path.exists(candidate):
            os.environ["AERON_DRIVER_LIBRARY_PATH"] = candidate
