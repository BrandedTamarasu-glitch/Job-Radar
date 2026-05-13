# Changelog

## v2.4.0 — 2026-05-13

### New Features
- **GUI search controls** — Added GUI presets, automated/manual source toggles, company include/exclude filters, must-have and nice-to-have skill controls, location strictness, and freshness presets.
- **Application pipeline foundation** — Added tracker persistence for notes, next actions, and next-action dates; added an Applications view-model; added application pipeline CSV export helpers.

### Fixes
- **Release test compatibility** — Metadata tests now support Python 3.10 via `tomli` fallback, fixing the failed release workflow collection error on macOS.

### Validation
- 754 automated tests collected: 746 passed, 8 skipped.

## v2.3.0 — 2026-05-13

### New Features
- **GUI search outcome clarity** — Completion screens now show source warnings, per-source job counts, zero-result next actions, and clearer cancelled/error states.
- **Runtime stability controls** — Added documented controls for fetch parallelism, request timeout, and slow-source warning thresholds.
- **Cache maintenance controls** — Added stale cache pruning plus visible cache clearing in both CLI (`--clear-cache`) and GUI Settings.

### Improvements
- **Report responsiveness** — Removed unused report assets, added a payload-size guard, collapsed lower-score rows in large reports, and centralized external asset tags.
- **Long-running data maintenance** — Added conservative tracker pruning for old seen jobs while preserving application status and legacy records.
- **Storage consistency** — Tracker data now defaults to app data `results/tracker.json`, with legacy launch-directory tracker fallback.
- **Uninstall clarity** — Runtime data locations, cleanup behavior, and profile/config-only backup scope are documented consistently across README, workflow docs, and FAQ.

### Validation
- 727 automated tests collected: 719 passed, 8 skipped.

## v2.2.0 — 2026-02-16

### New Features
- **In-app auto-update** — Detect new releases, preview changelog, download with progress bar, SHA256 verification, launch installer, and skip-version support
- **hiring.cafe integration** — New free job source (tech job aggregator, rate limited: 60/hour, no API key required)
- **Cross-source dedup richness scoring** — When duplicate listings are found across sources, the richest version (most complete data) is kept instead of first-seen

### Improvements
- 9 Windows CI test fixes for cross-platform reliability
- 664 automated tests across 21 test files (was 566 across 19)

## v2.1.7 — 2026-02-14

### Critical Bug Fix
- **Tab buttons now work reliably** - Fixed invisible welcome screen frame blocking tab button clicks
- **Root cause** - `grid_slaves()` didn't clear `place()`-managed widgets, leaving invisible overlay
- **Impact** - Eliminated random tab switching delays and click blocking

## v2.1.6 — 2026-02-14
