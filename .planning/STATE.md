# Project State: Job Radar

**Last Updated:** 2026-02-13T21:42:06Z

## Project Reference

**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters. Every listing must be ranked reliably so the user can trust the report and focus their time on the best matches.

**Current Milestone:** v2.1.0 Source Expansion & Polish

**Milestone Goal:** Expand automated job source coverage, give users control over staffing firm scoring, and provide clean uninstall experiences across platforms

## Current Position

**Phase:** 33 - Scoring Configuration Backend
**Current Plan:** 1/3
**Status:** In Progress

**Progress:** [███░░░░░░░] 33%

**Next Action:** Execute Phase 33 Plan 02 (Wizard Integration)

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
| 33-01 | 165 | 2 | 2 | 2026-02-13 |
| 32-04 | 426 | 2 | 3 | 2026-02-13 |
| 32-03 | 330 | 2 | 6 | 2026-02-13 |
| 32-02 | 158 | 2 | 2 | 2026-02-13 |

### Quality Indicators

**Test Coverage:**
- 494 tests across 17 test files
- All passing (v2.1.0 in progress)
- Coverage areas: scoring, config, tracker, wizard, report, UX, API, PDF, dedup, accessibility, profile management, GUI, rate limiting, JSearch, USAJobs, schema migration

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
| DEFAULT_SCORING_WEIGHTS matches hardcoded scoring.py | Preserve score stability for existing users during migration to v2 | 2026-02-13 |
| v0/v1 profiles migrate directly to v2 | Simplified migration using schema_version < 2 check, not incremental | 2026-02-13 |
| Default staffing_preference is 'neutral' | Clean slate for users to configure (differs from old +4.5 boost) | 2026-02-13 |
| Minimum 0.05 per scoring weight component | Prevents zeroing dimensions while allowing customization | 2026-02-13 |
| Graceful fallback for corrupted scoring_weights | Reset to defaults with warning instead of crashing (availability over strict validation) | 2026-02-13 |

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

Completed Phase 33 Plan 01: Profile Schema v2 Migration (PLAN 1 OF 3)

**Executed:** Added profile schema v2 with auto-migration, scoring_weights validation, and graceful fallback

**Key accomplishments:**
- Task 1 (RED): Added 12 failing tests for v2 schema migration and validation
- 5 migration tests (v0→v2, v1→v2, backup creation, data preservation, no-op for v2)
- 7 validation tests (scoring_weights components, sum-to-1.0, min 0.05, staffing_preference values, corrupted fallback)
- Task 2 (GREEN): Implemented v2 migration and validation in profile_manager.py
- Bumped CURRENT_SCHEMA_VERSION from 1 to 2
- Added DEFAULT_SCORING_WEIGHTS constant matching current hardcoded behavior
- Implemented v0→v2 and v1→v2 auto-migration with backup creation
- Extended validate_profile with scoring_weights and staffing_preference checks
- Added graceful fallback for corrupted scoring_weights with warning
- All 494 tests passing (12 new tests, zero regressions)

**Commits:**
- 6a943ad - test(33-01): add failing tests for v2 schema migration and validation
- 78ad414 - feat(33-01): implement v2 schema migration with scoring weights and staffing preference

**Duration:** 165 seconds (2min 45s)

### What's Next

Phase 33 in progress - 2 plans remaining (wizard integration, scoring engine integration)

### Files Changed This Session

- `/home/corye/Claude/Job-Radar/job_radar/profile_manager.py` - Added DEFAULT_SCORING_WEIGHTS, v2 migration logic, extended validation (+80 lines)
- `/home/corye/Claude/Job-Radar/tests/test_profile_manager.py` - Added 12 new tests for migration and validation (+195 lines)
- `/home/corye/Claude/Job-Radar/.planning/phases/33-scoring-configuration-backend/33-01-SUMMARY.md` - Created
- `/home/corye/Claude/Job-Radar/.planning/STATE.md` - Updated position, decisions, metrics

### Context for Next Session

**If continuing:** Phase 33 Plan 01 complete - profile schema v2 with auto-migration ready. Next: Plan 02 (wizard integration for scoring_weights configuration) or Plan 03 (scoring engine integration).

**If resuming later:** Read STATE.md for current position, check .planning/phases/33-scoring-configuration-backend/33-01-SUMMARY.md for migration details and DEFAULT_SCORING_WEIGHTS values.

---
*State initialized: 2026-02-13*
*Phase 33 Plan 01 complete - schema v2 migration ready, 2 plans remaining*
