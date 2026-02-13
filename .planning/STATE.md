# Project State: Job Radar

**Last Updated:** 2026-02-13T20:18:14Z

## Project Reference

**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters. Every listing must be ranked reliably so the user can trust the report and focus their time on the best matches.

**Current Milestone:** v2.1.0 Source Expansion & Polish

**Milestone Goal:** Expand automated job source coverage, give users control over staffing firm scoring, and provide clean uninstall experiences across platforms

## Current Position

**Phase:** 32 - Job Aggregator APIs
**Current Plan:** 4/4
**Status:** Complete

**Progress:** [██████████] 100%

**Next Action:** Plan Phase 33 (Scoring Configuration Backend)

## Performance Metrics

### Velocity (Recent Milestones)

| Milestone | Phases | Plans | Days | Plans/Day |
|-----------|--------|-------|------|-----------|
| v2.0.0 Desktop GUI | 3 | 8 | 2 | 4.0 |
| v1.5.0 Profile Mgmt | 4 | 7 | 7 | 1.0 |
| v1.4.0 Visual Design | 5 | 9 | 1 | 9.0 |
| v1.3.0 Accessibility | 3 | 7 | 1 | 7.0 |

**Average velocity:** ~5 plans/day (varies by complexity)
| Phase 32 P04 | 426 | 2 tasks | 3 files |
| Phase 32 P03 | 330 | 2 tasks | 6 files |
| Phase 31 P02 | 213 | 1 tasks | 5 files |
| Phase 32 P02 | 158 | 2 tasks | 2 files |

### Recent Plan Executions

| Plan | Duration (sec) | Tasks | Files | Date |
|------|---------------|-------|-------|------|
| 32-04 | 426 | 2 | 3 | 2026-02-13 |
| 32-03 | 330 | 2 | 6 | 2026-02-13 |
| 32-02 | 158 | 2 | 2 | 2026-02-13 |
| 32-01 | 164 | 2 | 2 | 2026-02-13 |

### Quality Indicators

**Test Coverage:**
- 482 tests across 17 test files
- All passing (v2.1.0 in progress)
- Coverage areas: scoring, config, tracker, wizard, report, UX, API, PDF, dedup, accessibility, profile management, GUI, rate limiting, JSearch, USAJobs

**Code Stats (v2.0.0):**
- ~19,000 LOC Python (source + tests + GUI)
- 7 GUI modules (2,665 LOC)
- Zero regressions across milestone transitions

**CI/CD:**
- Automated multi-platform builds (Windows, macOS, Linux)
- Accessibility CI (Lighthouse >=95%, axe-core WCAG validation)
- Smoke tests on all platforms

## Accumulated Context

### Key Decisions This Milestone

| Decision | Rationale | Date |
|----------|-----------|------|
| Start phase numbering at 31 | Continue from v2.0.0 (ended at Phase 30) | 2026-02-13 |
| Infrastructure-first ordering | Fix rate limiter before adding APIs prevents technical debt | 2026-02-13 |
| Schema migration as separate phase | Isolate risk, validate backend before GUI | 2026-02-13 |
| Defer Linux DEB/RPM packaging | .tar.gz acceptable for Linux users, focus macOS/Windows | 2026-02-13 |
| Clear limiters before closing connections | pyrate-limiter background threads cause segfaults if connections closed while active | 2026-02-13 |
| BACKEND_API_MAP fallback to source name | Backward compatibility - unmapped sources continue to work | 2026-02-13 |
| Merge config overrides with defaults | Partial rate limit overrides for better UX - users only customize specific APIs | 2026-02-13 |
| Validate and warn on invalid configs | Invalid rate limit configs show warnings and use defaults - graceful degradation | 2026-02-13 |
| JSearch source attribution from job_publisher | Show original board name (LinkedIn/Indeed/Glassdoor) not "JSearch" for accurate attribution | 2026-02-13 |
| All JSearch sources share rate limiter | linkedin/indeed/glassdoor/jsearch_other use single "jsearch" backend to prevent API violations | 2026-02-13 |
| Validate API keys during setup with inline test requests | Immediate feedback to users prevents configuration errors | 2026-02-13 |
| Store keys even on validation failure | Network issues should not block setup - graceful degradation | 2026-02-13 |
| Profile schema forward-compatible design | New optional fields accepted without code changes - extensibility | 2026-02-13 |
| Three-phase source ordering (scrapers -> APIs -> aggregators) | Ensures native sources win in dedup over aggregated duplicates | 2026-02-13 |
| JSearch display source splitting for progress tracking | Shows individual source progress (LinkedIn: 5, Indeed: 7) not "JSearch: 12" | 2026-02-13 |
| Deduplication returns dict with stats and multi-source map | Enables transparency and future multi-source badge feature | 2026-02-13 |
| GUI Settings tab for API key configuration | Non-technical users can configure API keys without terminal | 2026-02-13 |
| Inline API validation with test buttons | Immediate feedback prevents configuration errors | 2026-02-13 |
| Atomic .env writes using tempfile + replace | Prevents corruption on crashes or interrupts | 2026-02-13 |

### Active Constraints

- Python 3.10+ (EOL Oct 2026 - plan migration to 3.11+ by Q4)
- No API keys required for basic usage (tiered approach)
- Backward compatible profiles and CLI flags
- Single-file HTML reports (file:// portability)
- Cross-platform (macOS, Linux, Windows)

### Known Issues

None currently. v2.0.0 shipped clean.

### Todos (Cross-Phase)

- [ ] Research JSearch free tier rate limits (sparse documentation)
- [ ] Test macOS notarization timing (Apple server variability)
- [ ] Document Windows SmartScreen bypass for unsigned installer
- [ ] Validate schema migration with 100+ skill profiles (property-based testing)

### Blockers

None.

## Session Continuity

### What Just Happened

Completed Phase 32 Plan 04: GUI API Settings and Comprehensive Tests (PLAN 4 OF 4 - PHASE COMPLETE)

**Executed:** Added GUI API Settings tab and comprehensive test coverage for all Phase 32 functionality

**Key accomplishments:**
- Task 1: Added Settings tab to GUI with API key configuration for all sources
- JSearch section: API key field with test button and status indicator
- USAJobs section: email and API key fields with dual-credential validation
- Adzuna section: App ID and App Key fields
- Authentic Jobs section: API key field
- Keys masked by default with Show/Hide toggle for security
- Test buttons validate credentials via inline API requests with status feedback
- Save button writes atomically to .env using tempfile + replace pattern
- Tip displayed when JSearch not configured to drive adoption
- Task 2: Added comprehensive test suite for JSearch, USAJobs, and deduplication stats
- 18+ new tests covering JSearch source attribution, USAJobs nested structure, federal filters, dedup stats
- Updated all 22 existing dedup tests to handle new dict return type
- All 482 tests passing (up from 460 baseline)

**Commits:**
- f96f645 - feat(32-04): add API key configuration to GUI Settings tab
- aa4bced - test(32-04): add comprehensive tests for JSearch, USAJobs, dedup stats

**Duration:** 426 seconds (7.1 minutes)

### What's Next

Phase 32 complete - all 4 plans executed successfully. Ready for next phase or milestone completion.

### Files Changed This Session

- `/home/corye/Claude/Job-Radar/job_radar/gui/main_window.py` - Added Settings tab with API configuration UI (+482 lines)
- `/home/corye/Claude/Job-Radar/tests/test_sources_api.py` - Added JSearch, USAJobs, query builder tests (+224 lines)
- `/home/corye/Claude/Job-Radar/tests/test_deduplication.py` - Updated for dict return type, added stats tests (+155/-41 lines)
- `/home/corye/Claude/Job-Radar/.planning/phases/32-job-aggregator-apis/32-04-SUMMARY.md` - Created
- `/home/corye/Claude/Job-Radar/.planning/STATE.md` - Updated position, decisions, metrics

### Context for Next Session

**If continuing:** Phase 32 complete - all 4 plans executed. JSearch and USAJobs fully integrated with GUI API settings and comprehensive test coverage. Ready for next phase.

**If resuming later:** Read STATE.md for current position, check .planning/phases/32-job-aggregator-apis/32-04-SUMMARY.md for GUI settings and test details.

---
*State initialized: 2026-02-13*
*Phase 32 complete, ready for Phase 33 planning*
