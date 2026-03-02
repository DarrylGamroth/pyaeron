from __future__ import annotations

import errno
from dataclasses import dataclass
from typing import Any


class AeronError(RuntimeError):
    """Base class for pyaeron errors."""


class LibraryLoadError(AeronError):
    """Raised when libaeron cannot be found or loaded."""


class UnsupportedAeronVersionError(AeronError):
    """Raised when required Aeron symbols are unavailable."""


class AeronStateError(AeronError):
    """Raised for invalid wrapper state transitions."""


class AeronArgumentError(AeronError):
    """Raised for invalid Aeron argument usage."""


class IllegalStateError(AeronStateError):
    """Raised when Aeron reports an illegal state transition."""


class ResourceClosedError(AeronStateError):
    """Raised when an operation is attempted on a closed resource."""


class AeronIOError(AeronError):
    """Raised for I/O failures reported by Aeron."""


class AeronTimeoutError(AeronError):
    """Base class for timeout-related Aeron failures."""


class DriverTimeoutError(AeronTimeoutError):
    """Raised when the media driver times out."""


class ClientTimeoutError(AeronTimeoutError):
    """Raised when the Aeron client times out."""


class ConductorServiceTimeoutError(AeronTimeoutError):
    """Raised when the conductor service times out."""


class TimedOutError(AeronTimeoutError):
    """Raised for generic timed out operations."""


class BufferFullError(IllegalStateError):
    """Raised when Aeron reports the client buffer is full."""


class PublicationOfferError(AeronError):
    """Base class for negative publication offer/claim statuses."""


class NotConnectedError(PublicationOfferError):
    """Raised when publication is not connected."""


class BackPressuredError(PublicationOfferError):
    """Raised when publication is back pressured."""


class AdminActionError(PublicationOfferError):
    """Raised when publication fails due to admin action."""


class PublicationClosedError(PublicationOfferError):
    """Raised when publication is closed."""


class MaxPositionExceededError(PublicationOfferError):
    """Raised when publication reaches max stream position."""


@dataclass(frozen=True, slots=True)
class AeronFailureContext:
    errcode: int
    message: str


def _suffix(ctx: AeronFailureContext) -> str:
    return f"(errcode={ctx.errcode}) {ctx.message}"


def map_errcode_to_exception(errcode: int, message: str) -> AeronError:
    """Map Aeron/client errno codes to typed exceptions."""
    from ._capi import (
        AERON_CLIENT_ERROR_BUFFER_FULL,
        AERON_CLIENT_ERROR_CLIENT_TIMEOUT,
        AERON_CLIENT_ERROR_CONDUCTOR_SERVICE_TIMEOUT,
        AERON_CLIENT_ERROR_DRIVER_TIMEOUT,
    )

    ctx = AeronFailureContext(errcode=errcode, message=message)

    if errcode == 0:
        return AeronError(message or "Aeron operation failed without an error code")
    if errcode == errno.EINVAL:
        return AeronArgumentError(_suffix(ctx))
    if errcode == errno.EPERM:
        return IllegalStateError(_suffix(ctx))
    if errcode in (errno.EIO, errno.ENOENT):
        return AeronIOError(_suffix(ctx))
    if errcode == errno.ETIMEDOUT:
        return TimedOutError(_suffix(ctx))
    if errcode == AERON_CLIENT_ERROR_DRIVER_TIMEOUT:
        return DriverTimeoutError(_suffix(ctx))
    if errcode == AERON_CLIENT_ERROR_CLIENT_TIMEOUT:
        return ClientTimeoutError(_suffix(ctx))
    if errcode == AERON_CLIENT_ERROR_CONDUCTOR_SERVICE_TIMEOUT:
        return ConductorServiceTimeoutError(_suffix(ctx))
    if errcode == AERON_CLIENT_ERROR_BUFFER_FULL:
        return BufferFullError(_suffix(ctx))
    return AeronError(_suffix(ctx))


def map_publication_status_to_exception(status: int, message: str) -> AeronError:
    """Map negative publication/claim statuses to typed exceptions."""

    if status == -1:
        return NotConnectedError(message or "Publication is not connected")
    if status == -2:
        return BackPressuredError(message or "Publication is back pressured")
    if status == -3:
        return AdminActionError(message or "Publication failed due to admin action")
    if status == -4:
        return PublicationClosedError(message or "Publication is closed")
    if status == -5:
        return MaxPositionExceededError(message or "Publication max position exceeded")
    return PublicationOfferError(message or f"Publication offer failed with status {status}")


def last_error_code(*, capi: Any | None = None) -> int:
    """Return current Aeron error code, or 0 if unavailable."""
    if capi is None:
        try:
            from ._capi import load_libaeron

            capi = load_libaeron()
        except (LibraryLoadError, UnsupportedAeronVersionError):
            return 0
    return int(capi.lib.aeron_errcode())


def last_error_message(*, capi: Any | None = None) -> str:
    """Return current Aeron error message, or a fallback string."""
    if capi is None:
        try:
            from ._capi import load_libaeron

            capi = load_libaeron()
        except (LibraryLoadError, UnsupportedAeronVersionError):
            return "Aeron error unavailable: libaeron is not loaded"

    ptr = capi.lib.aeron_errmsg()
    message = capi.string_from_ptr(ptr)
    return message or "Aeron returned no error message"


def check_rc(
    rc: int,
    *,
    capi: Any | None = None,
    errcode: int | None = None,
    errmsg: str | None = None,
) -> int:
    """Validate rc values from functions that return 0 on success and -1 on failure."""
    if rc >= 0:
        return rc

    code = last_error_code(capi=capi) if errcode is None else errcode
    message = last_error_message(capi=capi) if errmsg is None else errmsg
    raise map_errcode_to_exception(code, message)


def check_position(
    position: int,
    *,
    capi: Any | None = None,
    errmsg: str | None = None,
) -> int:
    """Validate position values from offer/claim style calls."""
    if position >= 0:
        return position

    message = last_error_message(capi=capi) if errmsg is None else errmsg
    raise map_publication_status_to_exception(position, message)
