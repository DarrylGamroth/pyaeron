# Callback Semantics

This document defines the runtime behavior of fragment callbacks in `pyaeron`.

## Lifetime
- The `fragment: memoryview` passed to `Subscription.poll(...)` callbacks is callback-scoped.
- Do not store that view after callback return.
- To persist payload bytes, call `copy_fragment(fragment)` or pass `copy_payload=True` to `poll_until(...)`.

## Error Propagation
- Callback exceptions are captured during native poll execution.
- `Subscription.poll(...)` re-raises the callback exception in Python after control returns from Aeron.

## Callback Retention
- `pyaeron` retains the C callback reference for the duration of each native poll call to avoid GC invalidation.

## Helper APIs
- `Publication.offer_with_retry(...)` retries transient offer states:
  - not connected
  - back pressured
  - admin action
- `Subscription.poll_until(...)` repeatedly polls until enough fragments are consumed or timeout is reached.

