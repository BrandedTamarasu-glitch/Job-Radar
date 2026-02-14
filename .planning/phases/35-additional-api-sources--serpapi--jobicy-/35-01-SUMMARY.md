---
phase: 35-additional-api-sources--serpapi--jobicy-
plan: 01
subsystem: api
tags: [serpapi, jobicy, rate-limiting, job-aggregation, remote-jobs, google-jobs]

# Dependency graph
requires:
  - phase: 32-rate-limiter-infrastructure
    provides: pyrate-limiter SQLite backend with RATE_LIMITS config and BACKEND_API_MAP
  - phase: 32-jsearch-usajobs-api-integration
    provides: fetch pattern, mapper pattern, query generation, three-phase source ordering
provides:
  - SerpAPI Google Jobs fetch function with rate limiting (50/min conservative)
  - Jobicy remote jobs fetch function (public API, 1/hour rate limit)
  - Response mappers with HTML cleaning and field validation
  - get_quota_usage() utility for SQLite bucket query
  - Search pipeline integration in aggregator and API phases
affects: [35-02-gui-quota-tracking, v2.1.0-milestone]

# Tech tracking
tech-stack:
  added: []
  patterns: [quota-tracking-via-sqlite-query, public-api-no-key-pattern]

key-files:
  created: []
  modified: [job_radar/rate_limits.py, job_radar/sources.py]

key-decisions:
  - "SerpAPI conservative 50/min rate limit for 100 searches/month free tier"
  - "Jobicy 1/hour rate limit per API documentation"
  - "SerpAPI in aggregator phase (Google Jobs aggregator), Jobicy in API phase (native remote source)"
  - "get_quota_usage() queries SQLite bucket directly for (used, limit, period) tuples"
  - "Jobicy requires non-empty description after HTML cleaning for scoring"

patterns-established:
  - "Pattern: get_quota_usage() uses read-only SQLite SELECT on rate_limits table"
  - "Pattern: Public API sources skip API key check but still rate limit"

# Metrics
duration: 230s (3.8 min)
completed: 2026-02-14
---

# Phase 35 Plan 01: Additional API Sources (SerpAPI, Jobicy) Summary

**SerpAPI Google Jobs and Jobicy remote jobs backend integration with rate limiters, response mappers, quota tracking utility, and three-phase search pipeline integration**

## Performance

- **Duration:** 3.8 min (230 seconds)
- **Started:** 2026-02-14T03:27:19Z
- **Completed:** 2026-02-14T03:31:09Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added SerpAPI fetch function using Google Jobs API with conservative 50/min rate limiting
- Added Jobicy fetch function for remote-focused job listings (public API, 1/hour limit)
- Implemented get_quota_usage() for real-time quota tracking via SQLite bucket queries
- Integrated both sources into search pipeline with correct phase ordering (SerpAPI→aggregator, Jobicy→API)
- HTML cleaning and field validation in both response mappers

## Task Commits

Each task was committed atomically:

1. **Task 1: Add SerpAPI and Jobicy rate limiter config and quota tracking utility** - `1d7aeb9` (feat)
2. **Task 2: Implement SerpAPI and Jobicy fetch functions with response mappers** - `0f4f291` (feat)

## Files Created/Modified
- `job_radar/rate_limits.py` - Added serpapi/jobicy rate configs, BACKEND_API_MAP entries, get_quota_usage() function
- `job_radar/sources.py` - Added fetch_serpapi(), fetch_jobicy(), map_serpapi_to_job_result(), map_jobicy_to_job_result(), updated build_search_queries() and fetch_all()

## Decisions Made

**Rate limit configuration:**
- SerpAPI: 50/min conservative default for 100 searches/month free tier cap
- Jobicy: 1/hour per API documentation ("once per hour")

**Source phase ordering:**
- SerpAPI added to AGGREGATOR_SOURCES (Google Jobs aggregator, runs last)
- Jobicy added to API_SOURCES (native remote source, runs in middle phase)

**Quota tracking implementation:**
- get_quota_usage() queries pyrate-limiter SQLite bucket table directly
- Returns (used, limit, period) tuple or None if not available
- Uses shortest rate window for display (most relevant for quota warnings)

**Jobicy data quality:**
- Skip jobs with empty description after HTML cleaning (required for scoring)
- All Jobicy jobs are remote by definition (arrangement="remote")

**SerpAPI response handling:**
- Prefer apply_options[0].link, fall back to share_link for job URL
- Use detected_extensions.work_from_home for remote detection
- Use detected_extensions.schedule_type for employment type

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation followed existing fetch_jsearch() and fetch_usajobs() patterns cleanly.

## User Setup Required

None - API keys configured via existing `job-radar --setup-apis` workflow. Both sources optional (graceful degradation on missing credentials).

## Next Phase Readiness

Backend integration complete. Ready for:
- GUI quota tracking display (Plan 35-02)
- API key test buttons in Settings tab
- Source enable/disable checkboxes
- Quota exhaustion warnings during search

Both sources now available in automated search pipeline. SerpAPI provides alternative to JSearch for Google Jobs aggregation. Jobicy adds remote-focused job listings complementing existing sources.

---
*Phase: 35-additional-api-sources--serpapi--jobicy-*
*Plan: 01*
*Completed: 2026-02-14*
