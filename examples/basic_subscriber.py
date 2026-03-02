from __future__ import annotations

import argparse

from pyaeron import Client, Context


def main() -> None:
    parser = argparse.ArgumentParser(description="Subscribe to Aeron messages with pyaeron")
    parser.add_argument("--channel", default="aeron:ipc")
    parser.add_argument("--stream-id", type=int, default=1001)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    received = 0

    def on_fragment(fragment: memoryview, header) -> None:
        nonlocal received
        received += 1
        print(
            f"received={bytes(fragment)!r} session_id={header.session_id} "
            f"stream_id={header.stream_id} position={header.position}"
        )

    with Context() as ctx, Client(ctx) as client:
        sub = client.add_subscription(args.channel, args.stream_id, timeout=5.0)
        try:
            sub.poll_until(
                on_fragment,
                min_fragments=args.count,
                timeout=args.timeout,
                poll_interval=0.001,
                copy_payload=True,
            )
        finally:
            sub.close()


if __name__ == "__main__":
    main()
