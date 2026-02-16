# Project State: Job Radar

**Last Updated:** 2026-02-16T19:40:56Z

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-15)

**Core value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters.
**Current focus:** Phase 41 - Auto-Update Polish

## Current Position

**Milestone:** v2.2.0 Auto-Update & Source Expansion
**Phase:** 41 of 42 (Auto-Update Polish)
**Plan:** 1 of 2
**Status:** In Progress
**Last activity:** 2026-02-16 — Completed 41-01 Skip Version and Release Notes Backend

**Progress:** [█████████░] 50%

## Performance Metrics

### Velocity (Recent Milestones)

| Milestone | Phases | Plans | Days | Plans/Day |
|-----------|--------|-------|------|-----------|
| v2.1.0 Sources & Installers | 4 | 10 | 1 | 10.0 |
| v2.0.0 Desktop GUI | 3 | 8 | 2 | 4.0 |
| v1.5.0 Profile Mgmt | 4 | 7 | 7 | 1.0 |
| v1.4.0 Visual Design | 5 | 9 | 1 | 9.0 |

**Average velocity:** ~5 plans/day (varies by complexity)

### Recent Plan Executions

| Plan | Duration (sec) | Tasks | Files | Date |
|------|---------------|-------|-------|------|
| 41-01 | 174 | 1 | 2 | 2026-02-16 |
| 40-02 | 222 | 2 | 2 | 2026-02-16 |
| 40-01 | 221 | 2 | 3 | 2026-02-16 |
| 39-02 | ~600 | 3 | 3 | 2026-02-16 |
| 39-01 | 356 | 2 | 5 | 2026-02-16 |
| 38-02 | 1067 | 3 | 2 | 2026-02-16 |
| 38-01 | 187 | 1 | 2 | 2026-02-16 |
| 37-03 | 121 | 2 | 3 | 2026-02-14 |
| 37-02 | 176 | 2 | 7 | 2026-02-14 |

### Quality Indicators

**Test Coverage:**
- 566 tests across 19 test files
- All passing (v2.1.0 shipped)
- Coverage areas: scoring, config, tracker, wizard, report, UX, API, PDF, dedup, accessibility, profile management, GUI, rate limiting, JSearch, USAJobs, schema migration, scoring config widget, uninstaller

**Code Stats (v2.1.0 shipped):**
- ~26,000 LOC Python (source + tests + GUI)
- 9 GUI modules (3,899 LOC)
- Zero regressions across milestone transitions

## Accumulated Context

### Key Decisions (Recent)

Recent decisions affecting v2.2.0 work:

- v2.2.0 (41-01): None sentinel in suppressed_versions distinguishes permanent skip from time-based dismiss
- v2.2.0 (41-01): extract_summary() returns first 5 bullets or paragraph (not full body)
- v2.2.0 (40-02): Install callback passes dest_path to MainWindow instead of storing it internally
- v2.2.0 (40-02): Linux uses LinuxInstallInstructionsDialog directly, no confirmation dialog
- v2.2.0 (40-02): 1.5 second delay before app exit (allows user to see status message)
- v2.2.0 (40-02): Download Manually button opens release_url in browser (SHA256 mismatch alternative)
- v2.2.0 (40-01): Cleanup old installers on startup, not immediately after launch (avoid race condition)
- v2.2.0 (40-01): Use tkinter clipboard instead of pyperclip (no external dependency)
- v2.2.0 (40-01): macOS quarantine attribute left intact, trust notarization (per research)
- v2.2.0 (40-01): Windows uses DETACHED_PROCESS and CREATE_NEW_PROCESS_GROUP flags
- v2.2.0 (39-02): Banner transforms in-place between states (no separate widgets)
- v2.2.0 (39-02): Session-only dismiss on cancel (softer than 24h suppress)
- v2.2.0 (39-02): "Install Now" stub — Phase 40 implements installer launch
- v2.2.0 (39-01): SHA256 verification gracefully skips when digest is None (pre-June 2025 releases)
- v2.2.0 (39-01): Progress updates throttled to every ~100KB (balance responsiveness vs overhead)
- v2.2.0 (39-01): Cancellation deletes partial files immediately (avoid disk clutter)
- v2.2.0 (39-01): Asset selection uses regex pattern matching (handles naming variations)
- v2.2.0 (38-02): Blue/teal accent banner color matches VS Code update style
- v2.2.0 (38-02): Updates section placed before API Key Settings in Settings tab
- v2.2.0 (38-02): Manual check shows inline feedback instead of banner
- v2.2.0 (38-01): packaging.version.Version for semantic comparison (handles 1.10 > 1.9)
- v2.2.0 (38-01): Per-version suppress tracking (new version shows even if old dismissed)
- v2.2.0 (38-01): Queue-based async messaging for UpdateChecker (thread-safe GUI integration)
- v2.1.0: CI/CD automated installer builds on tagged releases (foundation for auto-update)
- v2.1.0: macOS DMG installer with custom background (notarization needed for auto-update)
- v2.0: CustomTkinter GUI with non-blocking threading (pattern for update download worker)
- v2.0: Queue-based messaging for thread-safe GUI updates (reuse for download progress)

Full decision log: PROJECT.md Key Decisions table (143 decisions)

### Active Constraints

- Python 3.10+ (EOL Oct 2026 - plan migration to 3.11+ by Q4)
- No API keys required for basic usage (tiered approach)
- Backward compatible profiles and CLI flags
- Single-file HTML reports (file:// portability)
- Cross-platform (macOS, Linux, Windows)

### Pending Todos

[From .planning/todos/pending/]

None yet for v2.2.0.

### Blockers/Concerns

- Phase 40 (Auto-Update Installation): macOS notarization requires Apple Developer account and CI/CD integration — research needed during phase planning
- Phase 42 (hiring.cafe Integration): Unofficial API endpoint discovery and field mapping required — execute /gsd:research-phase before planning

## Session Continuity

Last session: 2026-02-16
Stopped at: Completed 41-01-PLAN.md execution (Skip Version and Release Notes Backend)
Resume file: None

**Next step:** Continue to 41-02-PLAN.md (Update Banner "Skip This Version" and "What's New" UI)

---
*State initialized: 2026-02-13*
*Last activity: 2026-02-16 - Completed 41-01 Skip Version and Release Notes Backend (Phase 41: 1 of 2 plans)*
