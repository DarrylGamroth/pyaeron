import errno

import pytest

from pyaeron.errors import (
    AdminActionError,
    AeronArgumentError,
    AeronError,
    AeronIOError,
    BackPressuredError,
    BufferFullError,
    ClientTimeoutError,
    ConductorServiceTimeoutError,
    DriverTimeoutError,
    IllegalStateError,
    MaxPositionExceededError,
    NotConnectedError,
    PublicationClosedError,
    PublicationOfferError,
    TimedOutError,
    check_position,
    check_rc,
    map_errcode_to_exception,
    map_publication_status_to_exception,
)


def test_map_errcode_to_exception_core_types() -> None:
    assert isinstance(map_errcode_to_exception(errno.EINVAL, "bad arg"), AeronArgumentError)
    assert isinstance(map_errcode_to_exception(errno.EPERM, "bad state"), IllegalStateError)
    assert isinstance(map_errcode_to_exception(errno.EIO, "io"), AeronIOError)
    assert isinstance(map_errcode_to_exception(errno.ENOENT, "missing"), AeronIOError)
    assert isinstance(map_errcode_to_exception(errno.ETIMEDOUT, "timeout"), TimedOutError)


def test_map_errcode_to_exception_aeron_client_codes() -> None:
    assert isinstance(map_errcode_to_exception(-1000, "driver timeout"), DriverTimeoutError)
    assert isinstance(map_errcode_to_exception(-1001, "client timeout"), ClientTimeoutError)
    assert isinstance(
        map_errcode_to_exception(-1002, "conductor timeout"), ConductorServiceTimeoutError
    )
    assert isinstance(map_errcode_to_exception(-1003, "buffer full"), BufferFullError)


def test_map_errcode_unknown_falls_back_to_aeron_error() -> None:
    err = map_errcode_to_exception(123456, "unknown")
    assert isinstance(err, AeronError)


def test_map_publication_status_to_exception() -> None:
    assert isinstance(map_publication_status_to_exception(-1, "msg"), NotConnectedError)
    assert isinstance(map_publication_status_to_exception(-2, "msg"), BackPressuredError)
    assert isinstance(map_publication_status_to_exception(-3, "msg"), AdminActionError)
    assert isinstance(map_publication_status_to_exception(-4, "msg"), PublicationClosedError)
    assert isinstance(map_publication_status_to_exception(-5, "msg"), MaxPositionExceededError)
    assert isinstance(map_publication_status_to_exception(-99, "msg"), PublicationOfferError)


def test_check_rc_passthrough_and_raise() -> None:
    assert check_rc(0, errcode=0, errmsg="ok") == 0
    assert check_rc(2, errcode=0, errmsg="ok") == 2
    with pytest.raises(DriverTimeoutError):
        check_rc(-1, errcode=-1000, errmsg="driver timeout")


def test_check_position_passthrough_and_raise() -> None:
    assert check_position(1, errmsg="ok") == 1
    with pytest.raises(BackPressuredError):
        check_position(-2, errmsg="back pressured")
