# Integration Test Strategy

This project uses a deterministic integration harness for Aeron runtime tests.

## Media Driver Harness
- Integration tests launch a dedicated `aeronmd` process per test function.
- Each run uses a unique temporary `AERON_DIR` so tests are isolated.
- The harness waits for `cnc.dat` before yielding control to tests.
- Teardown always terminates the process (and escalates to kill if needed).

Implementation:
- `tests/integration/conftest.py`
- `tests/integration/support.py`

## Runtime Discovery
- `AERON_LIBRARY_PATH` can be supplied explicitly.
- `AERON_MD_BINARY` can point to a specific `aeronmd` executable.
- Defaults support `/opt/aeron/lib/libaeron.so` and `/opt/aeron/bin/aeronmd`.

## Matrix Coverage
`tests/integration/test_pubsub_matrix.py` covers:
- IPC and UDP channels
- invoker mode off/on
- multi-message publish/poll validation
- retry/backpressure-style behavior checks (`offer_with_retry` timeout path)

## CI Lanes
- Fast lane (PR/push): lint, typecheck, unit tests, and non-extended integration tests.
- Extended lane (schedule/workflow_dispatch): integration matrix tests marked `integration_extended`.

Make targets:
- `make test-integration-fast`
- `make test-integration-extended`

