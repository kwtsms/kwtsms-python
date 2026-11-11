# Changelog

All notable changes to the kwtSMS Python client are documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

### Fixed
- Bug fixes.

---

## [0.8.0] - 2026-11-06

### Added
- Client identifies itself with its name and version; optional `app_name` argument.

### Changed
- `send_with_retry()` no longer retries by default; `wait_seconds` parameter added.

---

## [0.7.35] - 2026-03-14

### Added
- README badges.

---

## [0.7.34] - 2026-03-14

### Added
- Country-specific phone validation (80+ countries).
- Trunk prefix handling.
- `find_country_code()` and `validate_phone_format()`.

---

## [0.7.33] - 2026-03-14

### Changed
- Maintenance.

---

## [0.7.32] - 2026-03-13

### Removed
- CLI module. Use the standalone [kwtsms-cli](https://github.com/boxlinknet/kwtsms-cli) instead.

---

## [0.7.31] - 2026-03-06

### Added
- README badges.

---

## [0.7.30] - 2026-03-06

### Changed
- Maintenance.

---

## [0.7.29] - 2026-03-06

### Fixed
- Bug fixes.

---

## [0.7.28] - 2026-03-06

### Fixed
- Bug fixes.

---

## [0.7.27] - 2026-03-06

### Changed
- Maintenance.

---

## [0.7.26] - 2026-03-06

### Changed
- Maintenance.

---

## [0.7.25] - 2026-03-05

### Added
- Security policy.

---

## [0.7.24] - 2026-03-05

### Added
- `send_with_retry()` method.

---

## [0.7.23] - 2026-03-05

### Added
- `AsyncKwtSMS` class (`pip install kwtsms[async]`).

---

## [0.7.22] - 2026-03-05

### Added
- `parse_webhook()` for delivery receipts.

---

## [0.7.21] - 2026-03-05

### Added
- `status()` method.

---

## [0.7.20] - 2026-03-05

### Added
- CI and automatic PyPI publishing.

---

## [0.7.19] - 2026-03-05

### Added
- README badges.

---

## [0.7.18] - 2026-03-05

### Changed
- Package metadata updated.

---

## [0.7.17] - 2026-03-05

### Fixed
- Bug fixes.

---

## [0.7.16] - 2026-03-05

### Added
- Ten runnable examples with guides.
- Contribution guidelines.

---

## [0.7.15] - 2026-03-04

### Added
- `KwtSMS.purchased` property.

### Fixed
- Bug fixes.

---

## [0.7.14] - 2026-03-04

### Added
- Wider emoji cleaning.
- Messages with no usable text are caught before any API call.

### Fixed
- Bug fixes.

---

## [0.7.13] - 2026-03-01

### Added
- Developer-friendly action messages on API errors.
- Test suites.

### Fixed
- Bug fixes.

---

## [0.7.10] - 2026-02-15

### Added
- `senderids()` and `coverage()` methods.

---

## [0.7.6] - 2026-02-01

### Changed
- Repository restructured.

---

## [0.7.0] - 2026-01-15

### Added
- Initial release.
- `KwtSMS` class with verify, balance, send and validate.
- Phone and message cleaning utilities.
- `.env` support and JSONL logging.
- Bulk send with auto-batching and retry.
- Zero external dependencies, Python 3.8+.

---
