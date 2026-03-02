import pytest

from pyaeron import AeronStateError, Client, Context, ResourceClosedError


@pytest.mark.integration
def test_client_lifecycle_real_runtime(media_driver) -> None:
    with Context(aeron_dir=media_driver.aeron_dir) as ctx:
        client = Client(ctx)
        assert client.is_open is True
        assert client.client_id() > 0
        cid1 = client.next_correlation_id()
        cid2 = client.next_correlation_id()
        assert cid2 > cid1

        with pytest.raises(AeronStateError):
            Client(ctx)

        client.close()
        client.close()
        assert client.is_open is False

        with pytest.raises(ResourceClosedError):
            client.next_correlation_id()
