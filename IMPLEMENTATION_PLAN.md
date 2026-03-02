# pyaeron Implementation Plan

Last updated: 2026-03-02
Status: Phase 8 complete

## Purpose
Create an idiomatic Python wrapper for the Aeron C client (`libaeron`) with a stable, Python-first API, strong lifecycle management, robust error handling, and production-ready tests.

## Goals
- Provide a high-level Python API that feels natural to Python users.
- Keep low-level C details private behind a minimal FFI layer.
- Support reliable publication/subscription workflows first.
- Build confidence through integration tests against a real media driver.
- Ship incrementally in phases with clear completion criteria.

## Non-Goals (Initial Scope)
- Full parity with every Aeron C API function in v1.
- Archive and cluster wrappers in initial delivery.
- Maximum throughput micro-optimizations before API correctness and usability.

## Guiding Principles
- Idiomatic Python over direct C mirroring.
- Explicit ownership and deterministic cleanup (`close()` + context managers).
- Typed exceptions rather than exposing raw error codes in normal usage.
- Narrow public API surface; expand only with tests and docs.
- Backwards-compatible evolution after first public release.

## Proposed Package Layout
- `pyaeron/__init__.py`
- `pyaeron/_capi.py` (private FFI + symbol loading + C structs/signatures)
- `pyaeron/errors.py`
- `pyaeron/context.py`
- `pyaeron/client.py`
- `pyaeron/publication.py`
- `pyaeron/subscription.py`
- `pyaeron/handlers.py`
- `pyaeron/types.py` (header/dataclass/value objects)
- `pyaeron/util.py`
- `tests/`
- `examples/`
- `docs/`
- `scripts/build_aeron.sh`

## Tooling Decisions
- FFI: `cffi` (preferred for callback safety and clear type declarations).
- Tests: `pytest`.
- Build metadata: `pyproject.toml` with setuptools/hatchling (to decide in Phase 1).
- Quality gates: `ruff`, `mypy` (strict mode staged), optional `pytest-xdist`.

## Phase Tracker
| Phase | Name | Status | Exit Criteria |
| --- | --- | --- | --- |
| 0 | Discovery + API Contract | Completed | Public API contract document accepted |
| 1 | Project Bootstrap | Completed | Package skeleton + CI + lint/test commands working |
| 2 | FFI Foundation | Completed | `libaeron` load + core symbols callable |
| 3 | Error Model | Completed | Negative returns map to typed exceptions |
| 4 | Core Lifecycle API | Completed | `Context` + `Client` lifecycle stable |
| 5 | Pub/Sub API MVP | Completed | Publish and receive one message in tests |
| 6 | Callback and Polling Ergonomics | Completed | Python handlers stable and documented |
| 7 | Integration Matrix + Reliability | Completed | Deterministic integration suite in CI |
| 8 | Advanced Features | Completed | Exclusive pub/counters/image extras shipped |
| 9 | Docs + Release | Not Started | Versioned release with examples and migration notes |

## Phase 0: Discovery + API Contract
Objective: Define what "idiomatic Python" means for this wrapper and lock the initial API contract.

Tasks:
- [x] Write `docs/api-contract.md` covering:
- [x] Naming, method signatures, return types, and context-manager semantics.
- [x] Exception classes and when they are raised.
- [x] Buffer input policy (`bytes`, `bytearray`, `memoryview`).
- [x] Callback signatures for subscription polling.
- [x] Document lifecycle invariants and idempotent close behavior.
- [x] Confirm first supported Python versions and OS targets.
- [x] Confirm Aeron version target and library discovery strategy.

Exit criteria:
- [x] API contract approved.
- [x] Open design questions resolved or explicitly deferred.

## Phase 1: Project Bootstrap
Objective: Establish repository structure, local dev workflow, and quality gates.

Tasks:
- [x] Add `pyproject.toml`.
- [x] Create package skeleton under `pyaeron/`.
- [x] Create `tests/`, `docs/`, `examples/`, `scripts/`.
- [x] Add lint/type/test tooling configuration.
- [x] Add `Makefile` or `justfile` for common commands.
- [x] Add CI workflow (lint + unit tests + selected integration test).
- [x] Add top-level `README.md` with quick-start placeholder.

Exit criteria:
- [x] `pytest`, lint, and type checks run locally.
- [x] CI passes on a no-op baseline.

## Phase 2: FFI Foundation
Objective: Implement private C FFI layer and dynamic library loading.

Tasks:
- [x] Implement `_capi.py` with:
- [x] Library discovery (`AERON_LIBRARY_PATH`, standard names, helpful error text).
- [x] Core type aliases and function signatures for MVP.
- [x] Constants for publication return codes and key enums.
- [x] Safe string conversion helpers for C strings.
- [x] Add smoke tests validating symbol availability.
- [x] Add `scripts/build_aeron.sh` for local build from `../aeron`.

MVP symbols:
- [x] Context: init/close + core setters/getters.
- [x] Client: init/start/close/is_closed/main_do_work.
- [x] Async add: publication/subscription + poll.
- [x] Data path: publication_offer + subscription_poll.
- [x] Error path: aeron_errcode/aeron_errmsg.

Exit criteria:
- [x] Core symbols callable from Python.
- [x] Library load failures are actionable.

## Phase 3: Error Model
Objective: Build a Python-native exception hierarchy and centralized result checking.

Tasks:
- [x] Implement `errors.py`:
- [x] Base `AeronError`.
- [x] Typed subclasses (driver timeout, client timeout, conductor timeout, I/O, argument/state errors).
- [x] Map `aeron_errcode()` to exception classes.
- [x] Provide helpers:
- [x] `check_rc(int)` for C functions returning `0/-1`.
- [x] `check_position(int)` for offer/claim semantics.
- [x] `last_error_message()` utility.
- [x] Add tests for mapping behavior.

Exit criteria:
- [x] No high-level module checks raw error codes directly.
- [x] Tests assert correct exception types/messages.

## Phase 4: Core Lifecycle API
Objective: Deliver `Context` and `Client` with deterministic lifecycle behavior.

Tasks:
- [x] Implement `Context` class:
- [x] Constructor allocates C context.
- [x] Configuration methods (`set_dir`, timeouts, invoker mode).
- [x] `close()`, `closed` property, idempotent semantics.
- [x] `__enter__/__exit__`.
- [x] Implement `Client` class:
- [x] Constructor with started client.
- [x] `do_work()` and optional idle helper.
- [x] `close()`, `is_open` semantics.
- [x] `client_id`, `next_correlation_id`.
- [x] Enforce ownership rules (context should not be reused incorrectly).
- [x] Add unit tests for lifecycle and close idempotency.

Exit criteria:
- [x] Context/client lifecycle tests pass.
- [x] No leaked resources in normal and error paths.

## Phase 5: Pub/Sub API MVP
Objective: Implement first end-to-end messaging flow with idiomatic wrappers.

Tasks:
- [x] Implement `Publication` wrapper and async-add publication polling flow.
- [x] Implement `Subscription` wrapper and async-add subscription polling flow.
- [x] Blocking helpers with timeout:
- [x] `Client.add_publication(...)`
- [x] `Client.add_subscription(...)`
- [x] `poll_until_ready(...)` internal helper.
- [x] `Publication.offer(data)` supporting buffer protocol.
- [x] `Publication.is_connected`.
- [x] `Subscription.poll(handler, fragment_limit=...)`.
- [x] `Subscription.is_connected`.
- [x] Add core constants/enums exposed in Pythonic form where needed.
- [x] Integration tests:
- [x] Add pub/sub.
- [x] Offer one message.
- [x] Poll one message.
- [x] Close resources in all paths.

Exit criteria:
- [x] End-to-end pub/sub works reliably over IPC.
- [x] Basic UDP path validated in at least one integration test.

## Phase 6: Callback and Polling Ergonomics
Objective: Ensure callback API is safe and intuitive for Python users.

Tasks:
- [x] Implement callback adapters in `handlers.py`.
- [x] Preserve callback references to avoid GC invalidation.
- [x] Convert fragment buffer to ergonomic Python type (default `memoryview`, with optional copy helper).
- [x] Header wrapper/value object for key fields.
- [x] Add timeout-aware poll loop helpers.
- [x] Add backpressure handling helper patterns.
- [x] Document callback lifetime guarantees and caveats.

Exit criteria:
- [x] Callback tests are stable across repeated runs.
- [x] No callback-related crashes under stress test loop.

## Phase 7: Integration Matrix + Reliability
Objective: Make integration tests deterministic and actionable.

Tasks:
- [x] Test harness for launching media driver process (or embedded strategy if available).
- [x] Deterministic setup/teardown and temp `aeron.dir` management.
- [x] Matrix:
- [x] IPC and UDP channel variants.
- [x] Invoker mode on/off.
- [x] Multi-message and backpressure scenarios.
- [x] Retry/wait helpers with clear timeout diagnostics.
- [x] CI gating strategy:
- [x] fast checks on PR
- [x] extended integration nightly/on-demand

Exit criteria:
- [x] Flaky test rate below agreed threshold.
- [x] CI failures provide actionable diagnostics.

## Phase 8: Advanced Features
Objective: Expand API after MVP is stable.

Candidate features:
- [x] Exclusive publications.
- [x] `try_claim` and buffer claim helpers.
- [x] Destination add/remove APIs.
- [x] Counters + counters reader.
- [x] Image APIs and selected metadata access.
- [x] Optional CnC monitoring helpers.

Exit criteria:
- [x] Each feature ships with tests + docs.
- [x] Public API additions are versioned and changelogged.

## Phase 9: Documentation + Release
Objective: Prepare first public release with clear operational guidance.

Tasks:
- [ ] Complete `README.md` quick start and installation docs.
- [ ] Add examples:
- [ ] basic publisher
- [ ] basic subscriber
- [ ] invoker mode sample
- [ ] Add API reference docs from docstrings.
- [ ] Add troubleshooting guide (`libaeron` load errors, driver connectivity, timeouts).
- [ ] Create changelog and semantic version policy.
- [ ] Publish initial package release.

Exit criteria:
- [ ] Docs and examples validated by clean-environment run.
- [ ] Release tag and package artifact published.

## Cross-Cutting Work Items
- [ ] Thread-safety audit for shared wrapper objects.
- [ ] Resource leak checks under repeated open/close loops.
- [ ] Structured logging hooks for diagnostics.
- [ ] Performance baseline measurements (latency/throughput smoke benchmark).
- [ ] API stability policy for pre-1.0 iterations.

## Risk Register
| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| Callback lifetime/GC issues | High | Medium | Strong reference retention tests and design review |
| Integration test flakiness | High | High | Deterministic harness + explicit waits/timeouts |
| `libaeron` discovery differences by OS | Medium | Medium | Layered load strategy + env override + docs |
| Overexposed C-style API | Medium | Medium | Enforce public API review against contract |
| Premature optimization complexity | Medium | Medium | MVP-first scope and staged enhancements |

## Definition of Done (Per Phase)
- [ ] Code implemented.
- [ ] Tests added and passing.
- [ ] Docs updated.
- [ ] Changelog entry added (if public behavior changed).
- [ ] Review notes captured in this file or linked docs.

## Progress Log
Use this section for implementation updates.

- 2026-03-01: Initial phased plan created.
- 2026-03-01: Completed Phase 0. Added `docs/api-contract.md` with accepted v0.1 API contract and explicit deferred decisions.
- 2026-03-01: Completed Phase 1 bootstrap. Added packaging, tooling, package skeleton, CI workflow, and smoke tests.
- 2026-03-01: Verified locally in `.venv` with `make check` (ruff + mypy + unit tests + integration-smoke tests).
- 2026-03-01: Completed Phase 2 FFI foundation. Replaced placeholder loader with `cffi` MVP bindings in `_capi.py`.
- 2026-03-01: Added Phase 2 smoke tests (`tests/unit/test_capi.py`, `tests/integration/test_capi_symbol_smoke.py`).
- 2026-03-01: Verified locally in `.venv` with `make check`; integration symbol smoke skipped when `libaeron` is unavailable.
- 2026-03-01: Completed Phase 3 error model with typed exception hierarchy and helpers (`check_rc`, `check_position`, `last_error_message`).
- 2026-03-01: Added error mapping tests in `tests/unit/test_errors.py`.
- 2026-03-01: Verified locally in `.venv` with `make check`; integration tests passed with `libaeron` available.
- 2026-03-01: Completed Phase 4 core lifecycle API with C-backed `Context` and `Client`.
- 2026-03-01: Added integration lifecycle coverage in `tests/integration/test_client_lifecycle.py`.
- 2026-03-01: Verified locally in `.venv` with `make check` (unit + integration).
- 2026-03-01: Completed Phase 5 pub/sub MVP with real `Publication.offer` and `Subscription.poll`.
- 2026-03-01: Added integration coverage for IPC and UDP in `tests/integration/test_pubsub_mvp.py`.
- 2026-03-01: Verified locally in `.venv` with `make check` (all tests passing).
- 2026-03-01: Completed Phase 6 callback ergonomics with adapters/copy helpers and timeout-aware polling helpers.
- 2026-03-01: Added `docs/callbacks.md` and unit coverage in `tests/unit/test_handlers.py`.
- 2026-03-01: Verified locally in `.venv` with `make check` (unit + integration).
- 2026-03-01: Completed Phase 7 deterministic integration harness in `tests/integration/conftest.py` and `tests/integration/support.py`.
- 2026-03-01: Added integration matrix coverage (`ipc`/`udp`, invoker on/off, multi-message, retry behavior) in `tests/integration/test_pubsub_matrix.py`.
- 2026-03-01: Added CI lanes for fast PR integration and extended scheduled/on-demand integration in `.github/workflows/ci.yml`.
- 2026-03-01: Verified locally in `.venv` with `make check` (all tests passing).

## Immediate Next Steps
- [x] Execute Phase 0 and produce `docs/api-contract.md`.
- [x] Finalize tooling stack in Phase 1.
- [x] Start Phase 2 FFI skeleton with a minimal callable symbol set.
