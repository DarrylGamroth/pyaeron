from pyaeron import Client, Context, ResourceClosedError


def test_context_close_is_idempotent() -> None:
    ctx = Context(aeron_dir="/tmp/aeron")
    assert ctx.closed is False
    ctx.close()
    ctx.close()
    assert ctx.closed is True


def test_client_close_is_idempotent() -> None:
    with Context() as ctx:
        client = Client(ctx)
        assert client.is_open is True
        client.close()
        client.close()
        assert client.is_open is False


def test_context_is_single_use_for_client() -> None:
    with Context() as ctx:
        client = Client(ctx)
        assert client.is_open
        try:
            Client(ctx)
        except Exception as exc:  # noqa: BLE001
            assert exc.__class__.__name__ in {"AeronStateError"}
        else:
            raise AssertionError("Expected a state error for context reuse")


def test_client_methods_raise_when_closed() -> None:
    with Context() as ctx:
        client = Client(ctx)
        client.close()
        try:
            client.next_correlation_id()
        except ResourceClosedError:
            pass
        else:
            raise AssertionError("Expected ResourceClosedError")

