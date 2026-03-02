# Integration Test Strategy

This project uses deterministic integration tests against a real Aeron media driver.

## Driver Modes in Tests
`tests/integration/conftest.py` supports two execution modes:
- External driver mode: set `AERON_EXTERNAL_MEDIA_DRIVER_DIR` to a directory containing `cnc.dat`.
  - In this mode, tests use the existing running driver and do not launch `aeronmd`.
- Managed driver mode: if `AERON_EXTERNAL_MEDIA_DRIVER_DIR` is not set, tests launch `aeronmd`.

## Runtime Discovery
- `AERON_LIBRARY_PATH` can point to a specific `libaeron` path.
- `AERON_DRIVER_LIBRARY_PATH` can point to a specific `libaeron_driver` path.
- `AERON_MD_BINARY` can point to a specific `aeronmd` executable for managed-driver mode.
- Local defaults include `/opt/aeron/lib/libaeron.so` and `/opt/aeron/lib/libaeron_driver.so`.

## Matrix Coverage
`tests/integration/test_pubsub_matrix.py` covers:
- IPC and UDP channels
- invoker mode off/on
- multi-message publish/poll validation
- retry-path behavior checks (`offer_with_retry`)

Additional integration coverage includes:
- embedded media driver roundtrip (`test_embedded_driver.py`)
- advanced APIs (`test_phase8_advanced.py`)

## CI Strategy
- PR/push lane:
  - lint, typecheck, unit tests
  - integration tests on Linux and Windows
- Scheduled/manual lane:
  - extended integration matrix

CI launches a Java media driver (`io.aeron.driver.MediaDriver`) and points tests at it via
`AERON_EXTERNAL_MEDIA_DRIVER_DIR`.

## Make Targets
- `make test-integration`
- `make test-integration-fast`
- `make test-integration-extended`
