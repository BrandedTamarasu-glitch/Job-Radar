# Project State: Job Radar

**Last Updated:** 2026-02-13T20:07:37Z

## Project Reference

**Core Value:** Accurate job-candidate scoring — if the scoring is wrong, nothing else matters. Every listing must be ranked reliably so the user can trust the report and focus their time on the best matches.

**Current Milestone:** v2.1.0 Source Expansion & Polish

**Milestone Goal:** Expand automated job source coverage, give users control over staffing firm scoring, and provide clean uninstall experiences across platforms

## Current Position

**Phase:** 32 - Job Aggregator APIs
**Current Plan:** 3/4
**Status:** In Progress

**Progress:** [██████████] 98%

**Next Action:** Execute Phase 32 Plan 04 (if exists) or complete phase

## Performance Metrics

### Velocity (Recent Milestones)

| Milestone | Phases | Plans | Days | Plans/Day |
|-----------|--------|-------|------|-----------|
| v2.0.0 Desktop GUI | 3 | 8 | 2 | 4.0 |
| v1.5.0 Profile Mgmt | 4 | 7 | 7 | 1.0 |
| v1.4.0 Visual Design | 5 | 9 | 1 | 9.0 |
| v1.3.0 Accessibility | 3 | 7 | 1 | 7.0 |

**Average velocity:** ~5 plans/day (varies by complexity)
| Phase 32 P03 | 330 | 2 tasks | 6 files |
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
| Validate API keys during setup with inline test requests | Immediate feedback to users prevents configuration errors | 2026-02-13 |
| Store keys even on validation failure | Network issues should not block setup - graceful degradation | 2026-02-13 |
| Profile schema forward-compatible design | New optional fields accepted without code changes - extensibility | 2026-02-13 |
| Three-phase source ordering (scrapers -> APIs -> aggregators) | Ensures native sources win in dedup over aggregated duplicates | 2026-02-13 |
| JSearch display source splitting for progress tracking | Shows individual source progress (LinkedIn: 5, Indeed: 7) not "JSearch: 12" | 2026-02-13 |
| Deduplication returns dict with stats and multi-source map | Enables transparency and future multi-source badge feature | 2026-02-13 |

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

Completed Phase 32 Plan 03: JSearch and USAJobs Integration into Search Pipeline (PLAN 3 OF 4)

**Executed:** Integrated JSearch and USAJobs into main search workflow with three-phase source ordering and enhanced deduplication

**Key accomplishments:**
- Task 1: Integrated JSearch and USAJobs into query builder and fetch_all orchestrator
- Query generation creates jsearch and usajobs queries from profile titles with location mapping
- Three-phase source ordering ensures native sources win in dedup (scrapers -> APIs -> aggregators)
- USAJobs added to API_SOURCES (native federal source runs before JSearch)
- JSearch results split by actual source (linkedin/indeed/glassdoor) for accurate progress display
- Task 2: Enhanced deduplication with multi-source tracking and statistics reporting
- Deduplication now returns dict with results, stats, and multi_source map
- Stats track original_count, deduped_count, duplicates_removed, sources_involved
- CLI displays dedup stats when duplicates found: "N duplicates removed across M sources"
- Updated sources_searched to include LinkedIn, Indeed, Glassdoor, USAJobs (Federal)
- All 460 tests passing (no regressions)

**Commits:**
- f67d896 - feat(32-job-aggregator-apis): integrate JSearch and USAJobs into search pipeline
- 8b80a14 - feat(32-job-aggregator-apis): enhance deduplication with multi-source tracking and stats

**Duration:** 330 seconds (5.5 minutes)

### What's Next

Check if Phase 32 Plan 04 exists, otherwise phase is complete. Ready for GUI API settings or source integration testing.

### Files Changed This Session

- `/home/corye/Claude/Job-Radar/job_radar/sources.py` - Integrated JSearch/USAJobs queries, three-phase fetch_all, enhanced tracking (+56/-7 lines)
- `/home/corye/Claude/Job-Radar/job_radar/deduplication.py` - Enhanced with stats and multi-source tracking (+73/-9 lines)
- `/home/corye/Claude/Job-Radar/job_radar/search.py` - Updated to handle dedup stats and new sources (+8/-1 lines)
- `/home/corye/Claude/Job-Radar/job_radar/gui/worker_thread.py` - Updated for new fetch_all return type (+4/-1 lines)
- `/home/corye/Claude/Job-Radar/tests/test_deduplication.py` - Updated for new return type (+31/-31 lines)
- `/home/corye/Claude/Job-Radar/tests/test_ux.py` - Updated mock to return tuple (+1/-1 lines)
- `/home/corye/Claude/Job-Radar/.planning/phases/32-job-aggregator-apis/32-03-SUMMARY.md` - Created
- `/home/corye/Claude/Job-Radar/.planning/STATE.md` - Updated position, decisions, metrics

### Context for Next Session

**If continuing:** Check for Phase 32 Plan 04. If none exists, phase is complete. JSearch and USAJobs now fully integrated into search pipeline with three-phase source ordering and enhanced dedup stats.

**If resuming later:** Read STATE.md for current position, check .planning/phases/32-job-aggregator-apis/32-03-SUMMARY.md for integration details.

---
*State initialized: 2026-02-13*
*Ready for Phase 31 planning*
