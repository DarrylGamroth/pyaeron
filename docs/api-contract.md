# pyaeron API Contract (Phase 0)

Status: Accepted
Contract version: 0.1
Date: 2026-03-01

## 1. Scope
This document defines the initial public API contract for `pyaeron` and the behavior users can rely on for the first implementation milestones.

The focus is the Aeron C client messaging path:
- context creation/configuration
- client lifecycle
- publication/subscription creation
- publish/poll loop
- deterministic cleanup

## 2. Runtime Support
### 2.1 Python Versions
`pyaeron` v0.1 targets:
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

### 2.2 OS/Architecture Targets
Tier 1 (fully supported and tested):
- Linux x86_64
- Linux aarch64

Tier 2 (best effort, limited CI coverage initially):
- macOS x86_64
- macOS arm64

Deferred:
- Windows support

### 2.3 Aeron Version Target
Primary API target:
- `aeronc.h` compatible with Aeron `1.51.x` (current source snapshot is `1.51.0-SNAPSHOT`).

Compatibility policy for early releases:
- Minimum intended compatibility floor: Aeron `1.48.x`.
- At runtime, required symbol checks are enforced.
- If required symbols are missing, raise `UnsupportedAeronVersionError`.

## 3. Public API Surface (v0.1)
`pyaeron` is Python-first and does not expose raw C pointers publicly.

### 3.1 Top-Level Exports
- `Context`
- `Client`
- `Publication`
- `Subscription`
- `Header`
- `AeronError` and typed subclasses

### 3.2 Type Aliases
```python
from collections.abc import Callable
from typing import Protocol, TypeAlias

BufferLike: TypeAlias = bytes | bytearray | memoryview
FragmentHandler: TypeAlias = Callable[[memoryview, "Header"], None]
```

### 3.3 `Context`
```python
class Context:
    def __init__(
        self,
        *,
        aeron_dir: str | None = None,
        driver_timeout_ms: int | None = None,
        keepalive_interval_ns: int | None = None,
        resource_linger_duration_ns: int | None = None,
        idle_sleep_duration_ns: int | None = None,
        pre_touch_mapped_memory: bool | None = None,
        use_conductor_agent_invoker: bool | None = None,
        client_name: str | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None: ...

    def close(self) -> None: ...
    def __enter__(self) -> "Context": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...

    @property
    def closed(self) -> bool: ...

    # Config properties remain mutable until bound to a Client.
    @property
    def aeron_dir(self) -> str | None: ...
    @aeron_dir.setter
    def aeron_dir(self, value: str) -> None: ...
```

Behavior:
- Context manager support is required.
- `close()` is idempotent.
- Mutating configuration after `Client` creation raises `AeronStateError`.

### 3.4 `Client`
```python
class Client:
    def __init__(self, context: Context) -> None: ...
    def close(self) -> None: ...
    def __enter__(self) -> "Client": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...

    @property
    def is_open(self) -> bool: ...

    def do_work(self) -> int: ...
    def client_id(self) -> int: ...
    def next_correlation_id(self) -> int: ...

    def add_publication(
        self,
        channel: str,
        stream_id: int,
        *,
        timeout: float | None = 10.0,
        poll_interval: float = 0.001,
    ) -> "Publication": ...

    def add_subscription(
        self,
        channel: str,
        stream_id: int,
        *,
        timeout: float | None = 10.0,
        poll_interval: float = 0.001,
    ) -> "Subscription": ...
```

Behavior:
- Client creation starts Aeron client conductor according to context config.
- `do_work()` is valid and useful when invoker mode is enabled.
- `close()` is idempotent.

### 3.5 `Publication`
```python
class Publication:
    def close(self) -> None: ...
    @property
    def is_open(self) -> bool: ...
    @property
    def is_connected(self) -> bool: ...

    def offer(self, data: BufferLike) -> int: ...
```

Behavior:
- `offer()` returns the new stream position on success.
- Negative C status codes are converted to typed Python exceptions.

### 3.6 `Subscription`
```python
class Subscription:
    def close(self) -> None: ...
    @property
    def is_open(self) -> bool: ...
    @property
    def is_connected(self) -> bool: ...

    def poll(
        self,
        handler: FragmentHandler,
        *,
        fragment_limit: int = 10,
    ) -> int: ...
```

Behavior:
- Returns number of fragments processed.
- `fragment_limit` must be positive (`ValueError` otherwise).

### 3.7 `Header`
`Header` is a lightweight value object exposing the subset needed for MVP callback use.

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Header:
    frame_length: int
    version: int
    flags: int
    type: int
    term_offset: int
    session_id: int
    stream_id: int
    term_id: int
    reserved_value: int
    position: int
    initial_term_id: int
    position_bits_to_shift: int
```

## 4. Exception Contract
### 4.1 Base Hierarchy
```python
class AeronError(RuntimeError): ...
class AeronStateError(AeronError): ...
class AeronIOError(AeronError): ...
class AeronTimeoutError(AeronError): ...
class ResourceClosedError(AeronStateError): ...
class UnsupportedAeronVersionError(AeronError): ...
```

### 4.2 Client Timeout/Error Mapping
C client errors map to typed Python exceptions:
- `AERON_CLIENT_ERROR_DRIVER_TIMEOUT` -> `DriverTimeoutError`
- `AERON_CLIENT_ERROR_CLIENT_TIMEOUT` -> `ClientTimeoutError`
- `AERON_CLIENT_ERROR_CONDUCTOR_SERVICE_TIMEOUT` -> `ConductorServiceTimeoutError`
- `AERON_CLIENT_ERROR_BUFFER_FULL` -> `BufferFullError`

### 4.3 Publication Offer Status Mapping
`Publication.offer()` maps negative statuses to exceptions:
- `AERON_PUBLICATION_NOT_CONNECTED` -> `NotConnectedError`
- `AERON_PUBLICATION_BACK_PRESSURED` -> `BackPressuredError`
- `AERON_PUBLICATION_ADMIN_ACTION` -> `AdminActionError`
- `AERON_PUBLICATION_CLOSED` -> `PublicationClosedError`
- `AERON_PUBLICATION_MAX_POSITION_EXCEEDED` -> `MaxPositionExceededError`
- `AERON_PUBLICATION_ERROR` and other unknown negatives -> `PublicationOfferError`

Each raised exception includes:
- original Aeron error code if available
- `aeron_errmsg()` text when available

## 5. Buffer and Memory Contract
### 5.1 Accepted Input for `offer`
`Publication.offer` accepts any contiguous buffer-protocol payload, including:
- `bytes`
- `bytearray`
- `memoryview`

If a supplied `memoryview` is non-contiguous, it is copied into a contiguous temporary buffer before the C call.

### 5.2 Zero-Copy Expectations
- For contiguous buffers, wrapper passes pointers without extra copy where possible.
- Data only needs to remain valid for the duration of the call.

### 5.3 Fragment Callback Lifetime
In `Subscription.poll(handler=...)`:
- Fragment `memoryview` is only valid for the callback invocation.
- `Header` value is callback-scoped and must be treated as immutable.
- Users must copy payload (`bytes(fragment)`) if they need persistence beyond callback return.

## 6. Callback Contract
### 6.1 Poll Handler Signature
```python
def handler(fragment: memoryview, header: Header) -> None:
    ...
```

### 6.2 Error Handling in Callback
- Exceptions raised by user handlers must not cross the C callback boundary directly.
- Wrapper captures callback exceptions, stops/returns from poll safely, then re-raises in Python after control returns from C.

### 6.3 Callback Retention
- Wrapper retains internal C callback references for the owner object lifetime.
- Users do not need to manually pin handlers.

## 7. Lifecycle and Ownership Contract
### 7.1 Ownership
- `Client` owns Aeron client handle created from `Context`.
- `Publication` and `Subscription` are owned by `Client`.

### 7.2 Close Semantics
- `close()` is idempotent for all wrapper objects.
- Methods called after close raise `ResourceClosedError`.

### 7.3 Context Reuse
- A `Context` instance is single-use for `Client` construction.
- Creating a second `Client` from the same `Context` raises `AeronStateError`.

### 7.4 Context Managers
All public resource types support context-manager usage and guarantee cleanup on block exit.

## 8. Threading Contract
- `Context` configuration is single-threaded.
- `Publication.offer` and `Subscription.poll` are not guaranteed thread-safe for concurrent calls on the same instance.
- Distinct publication/subscription instances may be used from separate threads at user discretion.
- Invoker mode users are responsible for calling `Client.do_work()` from their own loop/thread model.

## 9. Library Discovery Strategy
`libaeron` loading order:
1. `AERON_LIBRARY_PATH` if set (file path to shared library).
2. Platform loader resolution by library name (`aeron` / `libaeron`).
3. Standard dynamic library paths (`LD_LIBRARY_PATH`, `DYLD_LIBRARY_PATH`, system defaults).

Failure behavior:
- Raise `LibraryLoadError` with searched paths and remediation steps.

## 10. Public API Naming Rules
- Public Python API uses snake_case names.
- C-style `aeron_*` function names remain internal to private FFI modules.
- Raw pointer values are not exposed in public docs.

## 11. Deferred Decisions (Explicit)
The following are intentionally deferred beyond Phase 0:
- Public async resource-add API objects (`AsyncAddPublication`, `AsyncAddSubscription`) as first-class user API.
- Controlled poll action API parity (`ABORT/BREAK/COMMIT/CONTINUE`) in MVP.
- Exclusive publication, counters, image, destination management APIs.
- `asyncio`-native wrappers.
- Windows support.

## 12. Acceptance Criteria for Phase 0
Phase 0 is complete when:
- This contract is present and approved.
- All Phase 0 checklist items in `IMPLEMENTATION_PLAN.md` are marked complete.
- Deferred items are explicit in this document.
