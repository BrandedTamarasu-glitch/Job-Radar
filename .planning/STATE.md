# Project State: Job Radar

**Last Updated:** 2026-05-15T00:00:00-07:00

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-16)

**Core value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters.
**Current focus:** Product Iteration U-Y, Sprint U adaptive command center

## Current Position

**Milestone:** Product Iteration U-Y — IN PROGRESS
**Status:** Sprint U in progress; Sprints V-Y planned
**Last activity:** 2026-05-15 — completed Product Iteration P-T and started Product Iteration U-Y by documenting Sprints U-Y and surfacing local maintenance suggestions in Profile dashboard recommendations.

**Next step:** continue Sprint U by adding source-quality dashboard signals and validating command-center prioritization.

## Performance Metrics

### Velocity (Recent Milestones)

| Milestone | Phases | Plans | Days | Plans/Day |
|-----------|--------|-------|------|-----------|
| v2.1.0 Sources & Installers | 4 | 10 | 1 | 10.0 |
| v2.0.0 Desktop GUI | 3 | 8 | 2 | 4.0 |
| v1.5.0 Profile Mgmt | 4 | 7 | 7 | 1.0 |
| v1.4.0 Visual Design | 5 | 9 | 1 | 9.0 |

**Average velocity:** ~5 plans/day (varies by complexity)
| Phase 42 P02 | 348 | 2 tasks | 5 files |

### Recent Plan Executions

| Plan | Duration (sec) | Tasks | Files | Date |
|------|---------------|-------|-------|------|
| 42-02 | 348 | 2 | 5 | 2026-02-16 |
| 42-01 | 220 | 1 | 2 | 2026-02-16 |
| 41-02 | 273 | 2 | 3 | 2026-02-16 |
| 41-01 | 174 | 1 | 2 | 2026-02-16 |
| 40-02 | 222 | 2 | 2 | 2026-02-16 |
| 40-01 | 221 | 2 | 3 | 2026-02-16 |
| 39-02 | ~600 | 3 | 3 | 2026-02-16 |
| 39-01 | 356 | 2 | 5 | 2026-02-16 |
| 38-02 | 1067 | 3 | 2 | 2026-02-16 |

### Quality Indicators

**Test Coverage:**
- 593 tests across 19 test files (added 15 for hiring.cafe mapper + 7 pipeline + 5 dedup in 42-02)
- 672 passing, 4 pre-existing platform-specific failures (config, installer_launch)
- Coverage areas: scoring, config, tracker, wizard, report, UX, API, PDF, dedup, accessibility, profile management, GUI, rate limiting, JSearch, USAJobs, hiring.cafe, schema migration, scoring config widget, uninstaller

**Code Stats (v2.1.0 shipped):**
- ~26,000 LOC Python (source + tests + GUI)
- 9 GUI modules (3,899 LOC)
- Zero regressions across milestone transitions

## Accumulated Context

### Key Decisions (Recent)

Recent decisions affecting v2.2.0 work:

- v2.2.0 (42-02): hiring.cafe per-query limit is 50 results (not 1000 from phase goal)
- v2.2.0 (42-02): hiring.cafe rate limit at 60 req/hour with SQLite persistence
- v2.2.0 (42-02): hiring.cafe no retry (retries=1) - fail fast on API errors
- v2.2.0 (42-02): hiring.cafe silent skip on failure (empty list, debug log only)
- v2.2.0 (42-02): hiring.cafe runs in API phase (Phase 2) so native sources win in dedup
- v2.2.0 (42-02): Dedup enhancement keeps listing with more data when duplicates found
- v2.2.0 (42-02): Richness scoring: salary +3, description +2, structured salary +1, employment_type +1, apply_info +1, date_posted +1
- v2.2.0 (42-02): Remote jobs always included regardless of location preference (hiring.cafe)
- v2.2.0 (42-01): Salary format $120K - $160K (K-format, not comma-format) for hiring.cafe
- v2.2.0 (42-01): Missing salary displays "Not listed" (hiring.cafe convention)
- v2.2.0 (42-01): Hourly conversion uses 2080 hours/year (40hrs/week x 52 weeks)
- v2.2.0 (42-01): Salary period fallback heuristics: <500 = hourly, <20000 = monthly, else yearly
- v2.2.0 (41-02): Use tkinter.Menu for dropdown instead of CTkOptionMenu (popup behavior)
- v2.2.0 (41-02): Clickable version uses CTkButton with underline and transparent fg_color
- v2.2.0 (41-02): Conditional packing for Settings widgets based on state
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

### Active Sprint Plan

See `.planning/PRODUCT_ITERATION_SPRINTS_U_Y.md`.

- Sprint U: Adaptive Command Center — in progress
- Sprint V: Workflow Shortcuts & Bulk Actions — planned
- Sprint W: Source Strategy & Preset Intelligence — planned
- Sprint X: Release Readiness & Regression Sweep — planned
- Sprint Y: Post-Release Feedback Loop — planned

### Blockers/Concerns

None. Sprint U is active.

## Session Continuity

Last session: 2026-05-15
Stopped at: Sprint U dashboard maintenance-suggestion foundation in progress
Resume file: None

**Next step:** Continue Sprint U source-quality dashboard signals and validation.

---
*State initialized: 2026-02-13*
*Last activity: 2026-02-16 - Completed 42-01 hiring.cafe Mapper & Salary Normalization*
