# pyaeron

`pyaeron` is an idiomatic Python wrapper around the Aeron C client (`libaeron`).

## Status
Phase 7 foundation is complete:
- project packaging and tooling are configured
- package/module skeleton is in place
- `cffi`-based Aeron C API loader and MVP symbol bindings are implemented
- typed Aeron error model (`check_rc`, `check_position`, code-to-exception mapping) is implemented
- `Context` and `Client` now use real Aeron C lifecycle calls
- pub/sub MVP is live: `Client.add_publication`, `Client.add_subscription`, `Publication.offer`, `Subscription.poll`
- callback ergonomics helpers are live: `copy_fragment`, `FragmentCallbackAdapter`, `Subscription.poll_until`, `Publication.offer_with_retry`
- deterministic integration harness is live: per-test media driver process, isolated `AERON_DIR`, and matrix coverage
- lint, type checking, unit tests, and integration-smoke CI are wired

Core Aeron functionality is implemented in later phases.

## Quick Start (Development)
```bash
python -m pip install -U pip
python -m pip install -e ".[dev]"
make check
```

## Repository Layout
- `pyaeron/`: package source
- `tests/`: unit and integration-smoke tests
- `docs/`: design and implementation documents
- `scripts/`: helper scripts

## Planning Docs
- Implementation tracker: `IMPLEMENTATION_PLAN.md`
- API contract: `docs/api-contract.md`
- Callback/lifetime semantics: `docs/callbacks.md`
- Integration strategy: `docs/integration.md`
