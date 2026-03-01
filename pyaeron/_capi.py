from __future__ import annotations

import ctypes
import ctypes.util
import os

from .errors import LibraryLoadError


def load_libaeron() -> ctypes.CDLL:
    """Load libaeron using the configured discovery order.

    Phase 1 exposes a loader skeleton. Full symbol definitions arrive in Phase 2.
    """

    explicit_path = os.environ.get("AERON_LIBRARY_PATH")
    if explicit_path:
        try:
            return ctypes.CDLL(explicit_path)
        except OSError as exc:
            raise LibraryLoadError(
                f"Failed to load libaeron from AERON_LIBRARY_PATH={explicit_path!r}: {exc}"
            ) from exc

    candidates = ("aeron", "libaeron")
    for name in candidates:
        resolved = ctypes.util.find_library(name) or name
        try:
            return ctypes.CDLL(resolved)
        except OSError:
            continue

    raise LibraryLoadError(
        "Unable to locate libaeron. Set AERON_LIBRARY_PATH or install libaeron on the system "
        "library path."
    )

