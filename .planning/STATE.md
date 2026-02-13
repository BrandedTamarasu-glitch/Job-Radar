# Project State: Job Radar

**Last Updated:** 2026-02-13T18:24:16Z

## Project Reference

**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters. Every listing must be ranked reliably so the user can trust the report and focus their time on the best matches.

**Current Milestone:** v2.1.0 Source Expansion & Polish

**Milestone Goal:** Expand automated job source coverage, give users control over staffing firm scoring, and provide clean uninstall experiences across platforms

## Current Position

**Phase:** 31 - Rate Limiter Infrastructure
**Current Plan:** 2/2
**Status:** In progress

**Progress:** [██████████] 98%

**Next Action:** Continue Phase 31 - Plan 31-02 (configuration-driven rate limits)

## Performance Metrics

### Velocity (Recent Milestones)

| Milestone | Phases | Plans | Days | Plans/Day |
|-----------|--------|-------|------|-----------|
| v2.0.0 Desktop GUI | 3 | 8 | 2 | 4.0 |
| v1.5.0 Profile Mgmt | 4 | 7 | 7 | 1.0 |
| v1.4.0 Visual Design | 5 | 9 | 1 | 9.0 |
| v1.3.0 Accessibility | 3 | 7 | 1 | 7.0 |

**Average velocity:** ~5 plans/day (varies by complexity)

### Recent Plan Executions

| Plan | Duration (sec) | Tasks | Files | Date |
|------|---------------|-------|-------|------|
| 31-01 | 224 | 2 | 2 | 2026-02-13 |

### Quality Indicators

**Test Coverage:**
- 455 tests across 17 test files
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

Completed Phase 31 Plan 01: Rate Limiter Infrastructure

**Executed:** Fixed SQLite connection leaks via atexit cleanup and established shared rate limiter architecture

**Key accomplishments:**
- Task 1: Added atexit cleanup handler that clears limiters before closing connections (prevents segfaults)
- Task 2: Implemented BACKEND_API_MAP for shared rate limiters across sources using same backend API
- Added 3 new tests: cleanup, shared backend, fallback behavior
- All 455 tests passing (no regressions)

**Commits:**
- 487a7b2 - feat(31-rate-limiter-infrastructure): add atexit cleanup handler for SQLite connections
- 98cbee3 - feat(31-rate-limiter-infrastructure): implement shared rate limiters for backend APIs

**Duration:** 224 seconds (3.7 minutes)

### What's Next

Execute Phase 31 Plan 02: Configuration-driven rate limits

### Files Changed This Session

- `/home/corye/Claude/Job-Radar/job_radar/rate_limits.py` - Added atexit cleanup, BACKEND_API_MAP, shared limiter logic
- `/home/corye/Claude/Job-Radar/tests/test_rate_limits.py` - Added 3 new tests
- `/home/corye/Claude/Job-Radar/.planning/phases/31-rate-limiter-infrastructure/31-01-SUMMARY.md` - Created
- `/home/corye/Claude/Job-Radar/.planning/STATE.md` - Updated position and decisions

### Context for Next Session

**If continuing:** Proceed to Phase 31 planning. Research suggests this is foundation work (atexit handlers, shared rate limiters, config-driven limits) with standard Python patterns.

**If resuming later:** Read STATE.md for current position, check ROADMAP.md Phase 31 success criteria, review research/SUMMARY.md Phase 1 implications.

---
*State initialized: 2026-02-13*
*Ready for Phase 31 planning*
