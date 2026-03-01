from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

from .types import Header

FragmentHandler: TypeAlias = Callable[[memoryview, Header], None]

