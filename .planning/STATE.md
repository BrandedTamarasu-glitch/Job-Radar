# Project State: Job Radar

**Last Updated:** 2026-02-13T20:00:09Z

## Project Reference

**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters. Every listing must be ranked reliably so the user can trust the report and focus their time on the best matches.

**Current Milestone:** v2.1.0 Source Expansion & Polish

**Milestone Goal:** Expand automated job source coverage, give users control over staffing firm scoring, and provide clean uninstall experiences across platforms

## Current Position

**Phase:** 32 - Job Aggregator APIs
**Current Plan:** 2/4
**Status:** In Progress

**Progress:** [██████████] 97%

**Next Action:** Execute Phase 32 Plan 02 (API Setup Wizard Extension)

## Performance Metrics

### Velocity (Recent Milestones)

| Milestone | Phases | Plans | Days | Plans/Day |
|-----------|--------|-------|------|-----------|
| v2.0.0 Desktop GUI | 3 | 8 | 2 | 4.0 |
| v1.5.0 Profile Mgmt | 4 | 7 | 7 | 1.0 |
| v1.4.0 Visual Design | 5 | 9 | 1 | 9.0 |
| v1.3.0 Accessibility | 3 | 7 | 1 | 7.0 |

**Average velocity:** ~5 plans/day (varies by complexity)
| Phase 31 P02 | 213 | 1 tasks | 5 files |
| Phase 32 P02 | 158 | 2 tasks | 2 files |
| Phase 32 P01 | 164 | 2 tasks | 2 files |

### Recent Plan Executions

| Plan | Duration (sec) | Tasks | Files | Date |
|------|---------------|-------|-------|------|
| 31-02 | 213 | 1 | 5 | 2026-02-13 |
| 31-01 | 224 | 2 | 2 | 2026-02-13 |

### Quality Indicators

**Test Coverage:**
- 460 tests across 17 test files
- All passing (v2.1.0 in progress)
- Coverage areas: scoring, config, tracker, wizard, report, UX, API, PDF, dedup, accessibility, profile management, GUI, rate limiting

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

Completed Phase 32 Plan 01: JSearch and USAJobs API Integration

**Executed:** JSearch aggregator (LinkedIn/Indeed/Glassdoor) and USAJobs federal API with source attribution and shared rate limiting

**Key accomplishments:**
- Task 1: Implemented fetch_jsearch, map_jsearch_to_job_result, fetch_usajobs, map_usajobs_to_job_result functions
- JSearch uses job_publisher field for source attribution (linkedin, indeed, glassdoor, jsearch_other)
- USAJobs handles nested MatchedObjectDescriptor response structure
- Task 2: Configured BACKEND_API_MAP and RATE_LIMITS for shared rate limiting across JSearch sources
- All 460 tests passing (no regressions)

**Commits:**
- 18b0cef - feat(32-job-aggregator-apis): add JSearch and USAJobs fetch functions
- ba1c9be - feat(32-job-aggregator-apis): configure rate limiters for JSearch and USAJobs

**Duration:** 164 seconds (2.7 minutes)

### What's Next

Execute Phase 32 Plan 02: API Setup Wizard Extension (add JSearch and USAJobs to --setup-apis)

### Files Changed This Session

- `/home/corye/Claude/Job-Radar/job_radar/sources.py` - Added JSearch/USAJobs fetch functions and mappers
- `/home/corye/Claude/Job-Radar/job_radar/rate_limits.py` - Configured backend API mapping and rate limits
- `/home/corye/Claude/Job-Radar/.planning/phases/32-job-aggregator-apis/32-01-SUMMARY.md` - Created
- `/home/corye/Claude/Job-Radar/.planning/STATE.md` - Updated position, decisions, metrics

### Context for Next Session

**If continuing:** Proceed to Phase 32 Plan 02. JSearch and USAJobs fetch functions implemented and tested. Rate limiters configured with conservative defaults. Ready to extend --setup-apis wizard with new sources.

**If resuming later:** Read STATE.md for current position, check .planning/phases/32-job-aggregator-apis/32-01-SUMMARY.md for implementation details.

---
*State initialized: 2026-02-13*
*Ready for Phase 31 planning*
