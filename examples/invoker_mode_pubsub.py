from __future__ import annotations

import argparse

from pyaeron import Client, Context


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Single-process pub/sub using conductor invoker mode"
    )
    parser.add_argument("--channel", default="aeron:ipc")
    parser.add_argument("--stream-id", type=int, default=2001)
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()

    with Context(use_conductor_agent_invoker=True) as ctx, Client(ctx) as client:
        sub = client.add_subscription(
            args.channel,
            args.stream_id,
            timeout=5.0,
            poll_interval=0.0,
        )
        pub = client.add_publication(
            args.channel,
            args.stream_id,
            timeout=5.0,
            poll_interval=0.0,
        )

        received: list[bytes] = []

        def on_fragment(fragment: memoryview, _header) -> None:
            received.append(bytes(fragment))

        try:
            for i in range(args.count):
                payload = f"invoker-{i}".encode()
                pub.offer_with_retry(payload, timeout=5.0, poll_interval=0.0)
                while len(received) <= i:
                    client.do_work()
                    sub.poll(on_fragment, fragment_limit=10)

            print(f"received_count={len(received)}")
            for payload in received:
                print(payload)
        finally:
            pub.close()
            sub.close()


if __name__ == "__main__":
    main()
