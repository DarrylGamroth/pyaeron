from __future__ import annotations

import argparse
import time

from pyaeron import Client, Context


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish using publication.try_claim")
    parser.add_argument("--channel", default="aeron:ipc")
    parser.add_argument("--stream-id", type=int, default=3001)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--prefix", default="claim")
    parser.add_argument("--sleep-ms", type=float, default=10.0)
    args = parser.parse_args()

    with Context() as ctx, Client(ctx) as client:
        pub = client.add_publication(args.channel, args.stream_id, timeout=5.0)
        try:
            for i in range(args.count):
                payload = f"{args.prefix}-{i}".encode()
                with pub.try_claim(len(payload)) as claim:
                    claim.write(payload)
                print(f"claimed+committed payload={payload!r}")
                if args.sleep_ms > 0:
                    time.sleep(args.sleep_ms / 1000.0)
        finally:
            pub.close()


if __name__ == "__main__":
    main()
