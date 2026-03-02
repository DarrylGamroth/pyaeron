# pyaeron

`pyaeron` is an idiomatic Python wrapper around the Aeron C client (`libaeron`).

## Status
Current version: `0.1.0`

Implemented:
- Context and client lifecycle wrappers (`Context`, `Client`)
- Publication/subscription APIs (`Publication`, `Subscription`)
- Callback ergonomics (`FragmentCallbackAdapter`, `Subscription.poll_until`)
- Advanced APIs: `ExclusivePublication`, `BufferClaim`, destination add/remove, counters, image metadata, and CnC access
- Unit and integration test coverage (IPC + UDP, invoker on/off)

## Requirements
- Python `>=3.10`
- A compatible `libaeron` already installed on the target machine
- Aeron Media Driver (`aeronmd`) running for publish/subscribe flows

## Installation
From PyPI:

```bash
python -m pip install pyaeron
```

From source:

```bash
git clone <repo-url>
cd pyaeron
python -m pip install -e .
```

Development setup:

```bash
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Library Discovery
`pyaeron` tries to load Aeron in this order:
1. `AERON_LIBRARY_PATH`
2. System loader resolution (`find_library`)
3. Common library names (`libaeron.so`, `libaeron.dylib`, `aeron.dll`)

Linux example:

```bash
export AERON_LIBRARY_PATH=/opt/aeron/lib/libaeron.so
```

Windows PowerShell example:

```powershell
$env:AERON_LIBRARY_PATH = "C:\\aeron\\lib\\aeron.dll"
```

## Quick Start
Publisher:

```python
from pyaeron import Client, Context

channel = "aeron:ipc"
stream_id = 1001

with Context() as ctx:
    with Client(ctx) as client:
        pub = client.add_publication(channel, stream_id)
        try:
            pub.offer_with_retry(b"hello")
        finally:
            pub.close()
```

Subscriber:

```python
from pyaeron import Client, Context

channel = "aeron:ipc"
stream_id = 1001

received = []

def on_fragment(fragment, header):
    received.append((bytes(fragment), header.session_id))

with Context() as ctx:
    with Client(ctx) as client:
        sub = client.add_subscription(channel, stream_id)
        try:
            sub.poll_until(on_fragment, min_fragments=1, timeout=5.0, copy_payload=True)
        finally:
            sub.close()
```

## Examples
Runnable examples are in `examples/`:
- `examples/basic_publisher.py`
- `examples/basic_subscriber.py`
- `examples/invoker_mode_pubsub.py`
- `examples/try_claim_publisher.py`
- `examples/counters_demo.py`

## Development Commands
```bash
make lint
make typecheck
make test
make test-integration
make check
```

Generate cffi declarations from Aeron header:

```bash
make generate-cdef
```

Default header path is `../aeron/aeron-client/src/main/c/aeronc.h`.

## Documentation
- API contract: `docs/api-contract.md`
- API reference: `docs/api-reference.md`
- Callback notes: `docs/callbacks.md`
- Integration strategy: `docs/integration.md`
- Advanced features: `docs/advanced.md`
- Troubleshooting: `docs/troubleshooting.md`
- Versioning and release policy: `docs/versioning.md`
