# pyaeron

`pyaeron` is a Python wrapper for the Aeron C libraries.

It provides high-level APIs for:
- Aeron client lifecycle (`libaeron`)
- pub/sub messaging
- counters, images, and CnC inspection
- embedded media driver control (`libaeron_driver`)

## Status
Current version: `0.1.0`

## Requirements
- Python `>=3.10`
- `libaeron` installed and discoverable on the host
- For pub/sub flows, either:
  - an external media driver running (`aeronmd` or Java `MediaDriver`), or
  - embedded driver mode using `MediaDriver` (`libaeron_driver` required)

## Installation
From GitHub Actions artifact (recommended):

1. Open a successful CI run in GitHub Actions.
2. Download the `pyaeron-dist` artifact.
3. Extract it and install the wheel (or sdist).

Linux/macOS:

```bash
unzip pyaeron-dist.zip -d dist
python -m pip install dist/pyaeron-*.whl
```

Windows PowerShell:

```powershell
Expand-Archive .\pyaeron-dist.zip -DestinationPath .\dist
python -m pip install .\dist\pyaeron-*.whl
```

With GitHub CLI:

```bash
gh run download <run-id> -n pyaeron-dist -D dist
python -m pip install dist/pyaeron-*.whl
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
### Client library (`libaeron`)
Load order:
1. `AERON_LIBRARY_PATH`
2. system loader resolution (`find_library`)
3. common names (`libaeron.so`, `libaeron.dylib`, `aeron.dll`)

Linux example:

```bash
export AERON_LIBRARY_PATH=/opt/aeron/lib/libaeron.so
```

Windows PowerShell example:

```powershell
$env:AERON_LIBRARY_PATH = "C:\\aeron\\lib\\aeron.dll"
```

### Embedded driver library (`libaeron_driver`)
Load order:
1. `AERON_DRIVER_LIBRARY_PATH`
2. system loader resolution (`find_library`)
3. common names (`libaeron_driver.so`, `libaeron_driver.dylib`, `aeron_driver.dll`)

Linux example:

```bash
export AERON_DRIVER_LIBRARY_PATH=/opt/aeron/lib/libaeron_driver.so
```

Windows PowerShell example:

```powershell
$env:AERON_DRIVER_LIBRARY_PATH = "C:\\aeron\\lib\\aeron_driver.dll"
```

## Quick Start
### External driver mode
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

### Embedded driver mode

```python
from pyaeron import Client, Context, MediaDriver

with MediaDriver.launch_embedded() as driver:
    with Context(aeron_dir=driver.aeron_dir) as ctx:
        with Client(ctx) as client:
            pub = client.add_publication("aeron:ipc", 1001)
            sub = client.add_subscription("aeron:ipc", 1001)
            try:
                pub.offer_with_retry(b"embedded")
                sub.poll_until(lambda f, h: print(bytes(f)), min_fragments=1, timeout=5.0)
            finally:
                pub.close()
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
- Docs index: `docs/README.md`
- API reference: `docs/api-reference.md`
- API contract: `docs/api-contract.md`
- Callback notes: `docs/callbacks.md`
- Integration strategy: `docs/integration.md`
- Advanced features: `docs/advanced.md`
- Embedded media driver: `docs/embedded-driver.md`
- Troubleshooting: `docs/troubleshooting.md`
- Versioning and release policy: `docs/versioning.md`
