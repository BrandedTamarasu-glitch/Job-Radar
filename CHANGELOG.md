# Changelog

## v2.1.7 — 2026-02-14

### Critical Bug Fix
- **Tab buttons now work reliably** - Fixed invisible welcome screen frame blocking tab button clicks
- **Root cause** - `grid_slaves()` didn't clear `place()`-managed widgets, leaving invisible overlay
- **Impact** - Eliminated random tab switching delays and click blocking

## v2.1.6 — 2026-02-14
