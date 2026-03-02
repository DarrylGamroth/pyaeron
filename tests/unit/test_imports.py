import pyaeron


def test_package_exports_version() -> None:
    assert isinstance(pyaeron.__version__, str)
    assert pyaeron.__version__


def test_phase8_exports_present() -> None:
    assert pyaeron.ExclusivePublication
    assert pyaeron.Counter
    assert pyaeron.CountersReader
    assert pyaeron.Image
    assert pyaeron.CnC
    assert pyaeron.MediaDriver
    assert pyaeron.MediaDriverContext
    assert pyaeron.ThreadingMode
