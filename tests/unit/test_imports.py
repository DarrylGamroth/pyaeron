import pyaeron


def test_package_exports_version() -> None:
    assert isinstance(pyaeron.__version__, str)
    assert pyaeron.__version__

