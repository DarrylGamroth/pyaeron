# pyaeron API Contract

Status: active
Contract version: 0.2
Last updated: 2026-03-02

## 1. Scope
This contract defines the public behavior of `pyaeron`.

`pyaeron` wraps:
- `libaeron` for client/pub/sub/counters/image/CnC flows
- `libaeron_driver` for embedded media driver control

## 2. Runtime Support
### 2.1 Python Versions
Supported:
- Python 3.10+

### 2.2 Platform Coverage
CI-validated:
- Linux
- Windows (MSVC-built Aeron libraries)

Best effort:
- macOS (not currently covered by CI)

### 2.3 Aeron Compatibility
- C declarations are generated from `aeronc.h`.
- Required runtime symbols are validated at load time.
- Missing required symbols raise `UnsupportedAeronVersionError`.

## 3. Public API Surface
Top-level exports include:
- `Context`, `Client`
- `Publication`, `ExclusivePublication`, `Subscription`, `BufferClaim`
- `Counter`, `CountersReader`, `Image`, `CnC`
- `MediaDriverContext`, `MediaDriver`, `ThreadingMode`
- `Header` and related dataclasses
- `AeronError` and typed subclasses

API naming is Python-first (`snake_case`), while C function names remain private.

## 4. Lifecycle and Ownership Contract
- Resource wrappers are deterministic and support `close()`.
- `close()` is idempotent.
- Public operations on closed resources raise `ResourceClosedError`.
- All resource wrappers support context-manager usage where implemented.
- `Context` is single-use for `Client` construction.
- `MediaDriverContext` is single-use for `MediaDriver` construction.

## 5. Buffer and Callback Contract
### 5.1 Input Buffers
`offer()` and related APIs accept:
- `bytes`
- `bytearray`
- `memoryview`

Non-contiguous views are copied to contiguous temporary buffers.

### 5.2 Fragment Callback
Expected callback signature:

```python
def handler(fragment: memoryview, header: Header) -> None:
    ...
```

Behavioral guarantees:
- `fragment` is callback-scoped.
- If data must outlive callback scope, copy it (`bytes(fragment)` or `copy_payload=True` via helper paths).
- Callback exceptions are captured and re-raised in Python after native poll returns.

## 6. Error Contract
### 6.1 Return-code mapping
- `check_rc(...)` validates C APIs that return `0/-1` style results.
- `check_position(...)` validates `offer`/`try_claim` style results.

### 6.2 Typed errors
Common mappings include:
- driver/client/conductor timeouts
- buffer-full and invalid-state errors
- publication offer status errors (`NotConnectedError`, `BackPressuredError`, etc.)

`AeronError` is the base type for all wrapper errors.

## 7. Driver Interaction Contract
`pyaeron` supports two operational modes:
- External driver mode (existing `aeronmd` or Java media driver)
- Embedded driver mode (`MediaDriver.launch_embedded(...)`)

For external mode, client and driver must share the same `aeron_dir`.

For embedded mode:
- `libaeron_driver` must be loadable.
- `MediaDriver.close()` owns driver shutdown and context release.
- In `manual_main_loop=True`, caller is responsible for `do_work()`/`idle_strategy(...)` duty cycle.

## 8. Threading Contract
- `Context` and `MediaDriverContext` configuration is single-threaded.
- Wrapper instances are not guaranteed safe for concurrent method calls on the same object.
- If using conductor invoker mode, caller must progress work via `Client.do_work()`.

## 9. Library Discovery Contract
### 9.1 `libaeron`
Load order:
1. `AERON_LIBRARY_PATH`
2. system loader (`find_library`)
3. common names (`libaeron.so`, `libaeron.dylib`, `aeron.dll`)

### 9.2 `libaeron_driver`
Load order:
1. `AERON_DRIVER_LIBRARY_PATH`
2. system loader (`find_library`)
3. common names (`libaeron_driver.so`, `libaeron_driver.dylib`, `aeron_driver.dll`)

Load failures raise `LibraryLoadError` with candidate path diagnostics.
