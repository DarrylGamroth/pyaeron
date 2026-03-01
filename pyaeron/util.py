from __future__ import annotations

from .errors import ResourceClosedError


def ensure_open(closed: bool, resource_name: str) -> None:
    """Raise when operations are attempted on a closed resource."""
    if closed:
        raise ResourceClosedError(f"{resource_name} is closed")

