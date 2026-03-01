class AeronError(RuntimeError):
    """Base class for pyaeron errors."""


class LibraryLoadError(AeronError):
    """Raised when libaeron cannot be found or loaded."""


class UnsupportedAeronVersionError(AeronError):
    """Raised when required Aeron symbols are unavailable."""


class AeronStateError(AeronError):
    """Raised for invalid wrapper state transitions."""


class ResourceClosedError(AeronStateError):
    """Raised when an operation is attempted on a closed resource."""

