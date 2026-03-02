# Changelog

## Unreleased
- Added embedded media driver support via `MediaDriverContext` and `MediaDriver`.
- Added `libaeron_driver` loader and symbol validation.
- Added integration coverage for embedded driver pub/sub roundtrip.

## 0.1.0 - 2026-03-02
- Added idiomatic lifecycle wrappers for `Context` and `Client`.
- Added publication/subscription APIs with callback adapters and polling helpers.
- Added advanced feature wrappers: `ExclusivePublication`, `BufferClaim`, destinations, counters, images, and `CnC`.
- Added deterministic integration matrix tests across IPC/UDP and invoker modes.
- Switched cffi declarations to generated output from Aeron `aeronc.h`.
- Added production-facing docs: API reference, troubleshooting guide, examples, and release/versioning policy.
