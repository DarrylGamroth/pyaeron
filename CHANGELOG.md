# Changelog

## 0.1.0a1 - 2026-03-02
- Added `ExclusivePublication` support including retry and buffer-claim flows.
- Added `BufferClaim` helper with context-manager commit/abort semantics.
- Added destination add/remove APIs on publication, exclusive publication, and subscription.
- Added counter registration APIs (`Client.add_counter`, `Counter`, `CountersReader`).
- Added retained image APIs (`Subscription.image_count`, `image_by_session_id`, `Image`).
- Added CnC monitoring wrapper (`CnC`) with constants, heartbeat, error log, and counters reader access.
- Added unit and integration coverage for Phase 8 advanced features.
