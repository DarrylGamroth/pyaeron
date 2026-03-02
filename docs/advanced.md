# Advanced Features

`pyaeron` includes wrappers for advanced Aeron APIs beyond basic pub/sub.

## Exclusive Publications
- `Client.add_exclusive_publication(channel, stream_id, ...) -> ExclusivePublication`
- `ExclusivePublication.offer(...)`
- `ExclusivePublication.offer_with_retry(...)`
- `ExclusivePublication.try_claim(length) -> BufferClaim`
- `ExclusivePublication.add_destination(uri)` / `remove_destination(uri)`

## Buffer Claim
- `Publication.try_claim(length) -> BufferClaim`
- `BufferClaim.write(payload, offset=0)`
- `BufferClaim.commit()` and `BufferClaim.abort()`
- Context-manager semantics: commit on success, abort on exception.

## Destination Management
Available on:
- `Publication`
- `ExclusivePublication`
- `Subscription`

All expose:
- `add_destination(uri, timeout=..., poll_interval=...)`
- `remove_destination(uri, timeout=..., poll_interval=...)`

## Counters
- `Client.add_counter(type_id=..., label=..., key=...) -> Counter`
- `Counter.constants` / `Counter.counter_id`
- `Counter.value` read/write
- `Client.counters_reader -> CountersReader`
- `CountersReader.max_counter_id`
- `CountersReader.value(counter_id)`

## Images
- `Subscription.image_count`
- `Subscription.image_by_session_id(session_id) -> Image | None`
- `Image.constants`
- `Image.position`
- `Image.release()`

## CnC Monitoring
- `CnC(aeron_dir, timeout_ms=...)`
- `CnC.constants`
- `CnC.filename`
- `CnC.to_driver_heartbeat_ms`
- `CnC.read_error_log(since_timestamp=0)`
- `CnC.counters_reader`
