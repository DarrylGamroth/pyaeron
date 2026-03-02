from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

from .types import Header

FragmentHandler: TypeAlias = Callable[[memoryview, Header], None]


def copy_fragment(fragment: memoryview) -> bytes:
    """Return a stable copy of callback-scoped fragment payload bytes."""
    return bytes(fragment)


@dataclass(slots=True)
class FragmentCallbackAdapter:
    """Adapter that optionally copies fragment payload before invoking a callback."""

    handler: FragmentHandler
    copy_payload: bool = False

    def __call__(self, fragment: memoryview, header: Header) -> None:
        payload = memoryview(copy_fragment(fragment)) if self.copy_payload else fragment
        self.handler(payload, header)
