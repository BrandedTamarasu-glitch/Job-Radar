---
phase: 32-job-aggregator-apis
plan: 01
subsystem: api
tags: [jsearch, usajobs, rapidapi, rate-limiting, job-aggregation]

# Dependency graph
requires:
  - phase: 31-rate-limiter-infrastructure
    provides: Rate limiter with SQLite backend, BACKEND_API_MAP for shared limiters, config-driven rate limits
provides:
  - JSearch API integration (LinkedIn, Indeed, Glassdoor aggregator)
  - USAJobs API integration (federal job listings)
  - Source attribution from job_publisher field
  - Shared rate limiter across JSearch display sources
affects: [33-gui-api-settings, 34-source-integration-testing, api-setup-wizard]

# Tech tracking
tech-stack:
  added: []
  patterns: [RapidAPI header format, USAJobs government API headers, source attribution from aggregator responses]

key-files:
  created: []
  modified: [job_radar/sources.py, job_radar/rate_limits.py]

key-decisions:
  - "JSearch results use job_publisher for source attribution (linkedin/indeed/glassdoor), not 'JSearch'"
  - "Unknown JSearch publishers map to 'jsearch_other' to handle dynamic source additions"
  - "USAJobs requires both API key and email in User-Agent header per government API spec"
  - "All JSearch display sources share single rate limiter backend to prevent API violations"

patterns-established:
  - "RapidAPI integration: X-RapidAPI-Key and X-RapidAPI-Host headers (exact case required)"
  - "Government API pattern: custom headers (Host, User-Agent with email, Authorization-Key)"
  - "Source aggregator mapping: use original publisher field, whitelist known sources, log unknowns"
  - "Shared backend rate limiters via BACKEND_API_MAP for multiple display sources"

# Metrics
duration: 164s
completed: 2026-02-13
---

# Phase 32 Plan 01: JSearch and USAJobs API Integration Summary

**JSearch aggregator (LinkedIn/Indeed/Glassdoor) and USAJobs federal API with source attribution and shared rate limiting**

## Performance

- **Duration:** 2 min 44 sec
- **Started:** 2026-02-13T19:55:11Z
- **Completed:** 2026-02-13T19:57:55Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- JSearch API integration aggregates LinkedIn, Indeed, Glassdoor with source attribution from job_publisher field
- USAJobs federal API integration with nested response structure handling and optional federal filters
- Rate limiter configuration shares backend across JSearch display sources to prevent API violations
- All 460 tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement JSearch and USAJobs fetch functions with response mapping** - `18b0cef` (feat)
2. **Task 2: Update rate limiter configuration for JSearch and USAJobs backends** - `ba1c9be` (feat)

## Files Created/Modified
- `job_radar/sources.py` - Added fetch_jsearch, map_jsearch_to_job_result, fetch_usajobs, map_usajobs_to_job_result functions, JSEARCH_KNOWN_SOURCES whitelist, updated _SOURCE_DISPLAY_NAMES
- `job_radar/rate_limits.py` - Added BACKEND_API_MAP entries for linkedin/indeed/glassdoor/jsearch_other->jsearch and usajobs->usajobs, added RATE_LIMITS defaults for jsearch (100/min) and usajobs (60/min)

## Decisions Made

**JSearch Source Attribution:**
- Use job_publisher field for source name (e.g., "LinkedIn", "Indeed", "Glassdoor")
- Whitelist known sources: LinkedIn, Indeed, Glassdoor
- Unknown publishers map to "jsearch_other" for graceful handling
- Log unknown publishers at debug level for future expansion
- This provides accurate source attribution while handling dynamic publisher additions

**Rate Limiter Sharing:**
- All JSearch display sources (linkedin, indeed, glassdoor, jsearch_other) share single "jsearch" backend rate limiter
- Prevents hitting JSearch API limits faster when multiple display sources are used
- USAJobs gets its own rate limiter
- Conservative defaults: JSearch 100/min, USAJobs 60/min

**USAJobs Header Format:**
- Requires three custom headers per government API spec:
  - Host: data.usajobs.gov
  - User-Agent: {email} (must contain email from API registration)
  - Authorization-Key: {api_key}
- Both USAJOBS_API_KEY and USAJOBS_EMAIL required in .env

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation followed established Adzuna pattern from Phase 30-31.

## User Setup Required

None - no external service configuration required. API credentials will be configured via --setup-apis wizard (Phase 32 Plan 02).

## Next Phase Readiness

Ready for Phase 32 Plan 02 (API Setup Wizard Extension):
- JSearch and USAJobs fetch functions implemented and tested
- Rate limiters configured with conservative defaults
- All new functions follow established patterns (credential check, rate limit check, fetch, map)
- Display names configured for progress callbacks
- No blockers or concerns

## Self-Check: PASSED

**Files exist:**
- FOUND: job_radar/sources.py (modified with new functions)
- FOUND: job_radar/rate_limits.py (modified with new mappings)

**Commits exist:**
- FOUND: 18b0cef (Task 1: JSearch and USAJobs fetch functions)
- FOUND: ba1c9be (Task 2: Rate limiter configuration)

**Verification:**
- All imports successful: fetch_jsearch, fetch_usajobs, map_jsearch_to_job_result, map_usajobs_to_job_result
- _SOURCE_DISPLAY_NAMES includes: linkedin, indeed, glassdoor, jsearch_other, usajobs
- BACKEND_API_MAP correctly maps display sources to backends
- RATE_LIMITS includes jsearch and usajobs with conservative defaults
- All 460 tests pass with zero regressions

---
*Phase: 32-job-aggregator-apis*
*Completed: 2026-02-13*
