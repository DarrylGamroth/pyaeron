# Release Notes: 0.1.0

Release date: 2026-03-02
Tag: `v0.1.0`

## Highlights
- Complete idiomatic Python lifecycle API around Aeron C client.
- Stable pub/sub wrappers with timeout and retry ergonomics.
- Advanced feature coverage including exclusive publications, buffer claims, counters, images, and CnC helpers.
- Deterministic integration test matrix for IPC/UDP and invoker/non-invoker modes.
- Header-driven cffi declaration generation from `aeronc.h`.

## Packaging
Release artifacts are built as:
- source distribution (`sdist`)
- wheel

## Compatibility
- Python `>=3.10`
- Requires compatible `libaeron` installed on host system.
