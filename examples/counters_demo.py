from __future__ import annotations

import argparse
import time

from pyaeron import Client, Context


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and read Aeron counters")
    parser.add_argument("--type-id", type=int, default=1001)
    parser.add_argument("--label", default="pyaeron-example-counter")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--sleep-ms", type=float, default=250.0)
    args = parser.parse_args()

    with Context() as ctx, Client(ctx) as client:
        counter = client.add_counter(type_id=args.type_id, label=args.label, timeout=5.0)
        reader = client.counters_reader
        try:
            constants = counter.constants
            print(
                f"registered counter_id={constants.counter_id} "
                f"registration_id={constants.registration_id}"
            )

            for i in range(args.iterations):
                counter.value = i
                direct = counter.value
                via_reader = reader.value(constants.counter_id)
                print(f"i={i} direct={direct} via_reader={via_reader}")
                if args.sleep_ms > 0:
                    time.sleep(args.sleep_ms / 1000.0)
        finally:
            counter.close()


if __name__ == "__main__":
    main()
