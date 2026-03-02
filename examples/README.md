# Examples

These examples assume:
- `libaeron` is installed and discoverable (or `AERON_LIBRARY_PATH` is set)
- an Aeron media driver is already running in the same `aeron.dir` as your client context

Note: the example scripts use external driver mode. For embedded mode usage, see `docs/embedded-driver.md`.

## Basic publisher

```bash
python examples/basic_publisher.py --channel aeron:ipc --stream-id 1001 --count 10
```

## Basic subscriber

```bash
python examples/basic_subscriber.py --channel aeron:ipc --stream-id 1001 --count 10
```

## Invoker mode pub/sub

```bash
python examples/invoker_mode_pubsub.py --channel aeron:ipc --stream-id 2001 --count 5
```

## Try-claim publisher

```bash
python examples/try_claim_publisher.py --channel aeron:ipc --stream-id 3001 --count 10
```

## Counters demo

```bash
python examples/counters_demo.py --type-id 1001 --label demo-counter --iterations 5
```
