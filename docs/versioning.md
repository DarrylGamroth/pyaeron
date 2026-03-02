# Versioning and Release Policy

## Versioning Scheme
`pyaeron` uses Semantic Versioning (`MAJOR.MINOR.PATCH`).

Examples:
- `0.1.0`: first stable feature baseline for core client flows
- `0.1.1`: backwards-compatible bug fix
- `0.2.0`: feature release that may include API adjustments while still pre-1.0

## Pre-1.0 Compatibility
While major version is `0`, minor releases (`0.x.0`) may contain breaking API changes.
Breaking changes are documented in:
- `CHANGELOG.md`
- release notes section in tagged releases

## Post-1.0 Compatibility Target
When `1.0.0` is released:
- breaking changes only in major releases
- backwards-compatible features in minor releases
- bug fixes in patch releases

## Deprecation Policy
- Deprecations are announced in one release before removal when practical.
- Deprecated APIs include migration guidance in docs and changelog entries.

## Release Process
1. Ensure `ruff`, `mypy`, unit tests, and integration tests pass.
2. Update `CHANGELOG.md`.
3. Bump versions in:
- `pyproject.toml`
- `pyaeron/_version.py`
4. Build artifacts (`sdist` and wheel).
5. Tag release (`vX.Y.Z`).
6. Publish artifacts.
7. Attach release notes.
