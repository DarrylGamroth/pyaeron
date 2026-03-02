# pyaeron

`pyaeron` is an idiomatic Python wrapper around the Aeron C client (`libaeron`).

## Status
Phase 8 advanced wrapper APIs are complete:
- project packaging and tooling are configured
- package/module skeleton is in place
- `cffi`-based Aeron C API loader and symbol bindings are implemented
- typed Aeron error model (`check_rc`, `check_position`, code-to-exception mapping) is implemented
- `Context` and `Client` lifecycle APIs are stable
- pub/sub APIs are implemented for publication/subscription add, offer, and poll
- callback ergonomics are implemented (`FragmentCallbackAdapter`, `Subscription.poll_until`)
- integration harness is deterministic with per-test media-driver isolation
- advanced APIs are implemented: exclusive publication, buffer claim, destinations, counters, images, and CnC helpers

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
- Advanced feature guide: `docs/advanced.md`
