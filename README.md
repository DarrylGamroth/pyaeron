# pyaeron

`pyaeron` is an idiomatic Python wrapper around the Aeron C client (`libaeron`).

## Status
Phase 2 foundation is complete:
- project packaging and tooling are configured
- package/module skeleton is in place
- `cffi`-based Aeron C API loader and MVP symbol bindings are implemented
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
