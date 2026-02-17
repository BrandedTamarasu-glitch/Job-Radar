# Changelog

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
