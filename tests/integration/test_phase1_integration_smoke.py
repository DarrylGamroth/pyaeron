from pathlib import Path

import pytest

from pyaeron import Client, Context
from pyaeron._capi import try_load_libaeron


@pytest.mark.integration
def test_phase1_repository_and_api_smoke() -> None:
    if try_load_libaeron() is None:
        pytest.skip("libaeron not available in current environment")

    root = Path(__file__).resolve().parents[2]
    assert (root / "README.md").exists()
    assert (root / "IMPLEMENTATION_PLAN.md").exists()
    assert (root / "docs" / "api-contract.md").exists()
    assert (root / "scripts").is_dir()

    with Context() as ctx, Client(ctx) as client:
        pub = client.add_publication("aeron:ipc", 1001)
        sub = client.add_subscription("aeron:ipc", 1001)
        assert pub.is_open is True
        assert sub.is_open is True
