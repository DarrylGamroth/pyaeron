from __future__ import annotations

import argparse
import time

from pyaeron import Client, Context


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish Aeron messages with pyaeron")
    parser.add_argument("--channel", default="aeron:ipc")
    parser.add_argument("--stream-id", type=int, default=1001)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--prefix", default="msg")
    parser.add_argument("--sleep-ms", type=float, default=10.0)
    args = parser.parse_args()

    with Context() as ctx, Client(ctx) as client:
        pub = client.add_publication(args.channel, args.stream_id, timeout=5.0)
        try:
            for i in range(args.count):
                payload = f"{args.prefix}-{i}".encode()
                position = pub.offer_with_retry(payload, timeout=5.0, poll_interval=0.0005)
                print(f"sent={payload!r} position={position}")
                if args.sleep_ms > 0:
                    time.sleep(args.sleep_ms / 1000.0)
        finally:
            pub.close()


if __name__ == "__main__":
    main()
