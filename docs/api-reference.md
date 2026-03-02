# API Reference

This document lists the public `pyaeron` API as of `0.1.0`.

## Core Lifecycle

### `Context`
- `Context(...)`
- `Context.close() -> None`
- `Context.closed -> bool`
- `Context.aeron_dir -> str | None`
- `Context.driver_timeout_ms -> int`
- `Context.keepalive_interval_ns -> int`
- `Context.resource_linger_duration_ns -> int`
- `Context.idle_sleep_duration_ns -> int`
- `Context.pre_touch_mapped_memory -> bool`
- `Context.use_conductor_agent_invoker -> bool`
- `Context.client_name -> str | None`

### `Client`
- `Client(context: Context)`
- `Client.close() -> None`
- `Client.is_open -> bool`
- `Client.do_work() -> int`
- `Client.client_id() -> int`
- `Client.next_correlation_id() -> int`
- `Client.add_publication(channel, stream_id, ...) -> Publication`
- `Client.add_exclusive_publication(channel, stream_id, ...) -> ExclusivePublication`
- `Client.add_subscription(channel, stream_id, ...) -> Subscription`
- `Client.add_counter(type_id, label, key=b"", ...) -> Counter`
- `Client.counters_reader -> CountersReader`

## Publish APIs

### `Publication`
- `Publication.close() -> None`
- `Publication.is_open -> bool`
- `Publication.is_connected -> bool`
- `Publication.offer(data) -> int`
- `Publication.offer_with_retry(data, timeout=..., poll_interval=...) -> int`
- `Publication.try_claim(length) -> BufferClaim`
- `Publication.add_destination(uri, timeout=..., poll_interval=...) -> None`
- `Publication.remove_destination(uri, timeout=..., poll_interval=...) -> None`

### `ExclusivePublication`
- `ExclusivePublication.close() -> None`
- `ExclusivePublication.is_open -> bool`
- `ExclusivePublication.is_connected -> bool`
- `ExclusivePublication.offer(data) -> int`
- `ExclusivePublication.offer_with_retry(data, timeout=..., poll_interval=...) -> int`
- `ExclusivePublication.try_claim(length) -> BufferClaim`
- `ExclusivePublication.add_destination(uri, timeout=..., poll_interval=...) -> None`
- `ExclusivePublication.remove_destination(uri, timeout=..., poll_interval=...) -> None`

### `BufferClaim`
- `BufferClaim.length -> int`
- `BufferClaim.data -> memoryview`
- `BufferClaim.position -> int`
- `BufferClaim.write(payload, offset=0) -> None`
- `BufferClaim.commit() -> None`
- `BufferClaim.abort() -> None`

## Subscribe APIs

### `Subscription`
- `Subscription.close() -> None`
- `Subscription.is_open -> bool`
- `Subscription.is_connected -> bool`
- `Subscription.poll(handler, fragment_limit=10) -> int`
- `Subscription.poll_until(handler, min_fragments=1, timeout=..., ...) -> int`
- `Subscription.image_count -> int`
- `Subscription.image_by_session_id(session_id) -> Image | None`
- `Subscription.add_destination(uri, timeout=..., poll_interval=...) -> None`
- `Subscription.remove_destination(uri, timeout=..., poll_interval=...) -> None`

### Fragment handler utilities
- `FragmentCallbackAdapter`
- `copy_fragment(fragment: memoryview) -> bytes`
- `Header` dataclass

## Counter APIs

### `Counter`
- `Counter.close() -> None`
- `Counter.is_open -> bool`
- `Counter.constants -> CounterConstants`
- `Counter.counter_id -> int`
- `Counter.value -> int` (read/write)

### `CountersReader`
- `CountersReader.max_counter_id -> int`
- `CountersReader.value(counter_id: int) -> int`

## Image APIs

### `Image`
- `Image.release() -> None`
- `Image.is_open -> bool`
- `Image.position -> int`
- `Image.constants -> ImageConstants`

## CnC APIs

### `CnC`
- `CnC(aeron_dir: str, timeout_ms=5000)`
- `CnC.close() -> None`
- `CnC.filename -> str | None`
- `CnC.constants -> CncConstants`
- `CnC.to_driver_heartbeat_ms -> int`
- `CnC.read_error_log(since_timestamp=0) -> list[ErrorLogObservation]`
- `CnC.counters_reader -> CountersReader`

## Errors

Base type:
- `AeronError`

Common typed errors:
- `LibraryLoadError`
- `UnsupportedAeronVersionError`
- `AeronStateError`
- `ResourceClosedError`
- `TimedOutError`
- `NotConnectedError`
- `BackPressuredError`
- `AdminActionError`
- `PublicationClosedError`
- `MaxPositionExceededError`

Helpers:
- `check_rc(...)`
- `check_position(...)`
- `last_error_message(...)`
