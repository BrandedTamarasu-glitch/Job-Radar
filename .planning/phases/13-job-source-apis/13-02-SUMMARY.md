---
phase: 13-job-source-apis
plan: 02
subsystem: api
tags: [adzuna, authentic-jobs, api-integration, deduplication, sequential-fetch, error-handling]

# Dependency graph
requires:
  - phase: 13-01
    provides: Extended JobResult with salary fields, text cleaning utilities, location parsing, fuzzy deduplication module
  - phase: 12-02
    provides: API credential management (get_api_key) and rate limiting (check_rate_limit)
provides:
  - Adzuna API integration with salary data extraction and location normalization
  - Authentic Jobs API integration with design/creative roles
  - Sequential scraper-then-API fetch pipeline with cross-source deduplication
  - Per-source mapper functions with strict validation and HTML cleaning
  - Graceful error handling for network failures, rate limits, and missing credentials
affects: [14-wellfound-integration, 15-pdf-parsing]

# Tech tracking
tech-stack:
  added: []
  patterns: [sequential-fetch-pipeline, per-source-mappers, strict-validation]

key-files:
  created: []
  modified: [job_radar/sources.py]

key-decisions:
  - "Sequential scraper-then-API flow (scrapers first, APIs supplement)"
  - "Strict validation in mappers - skip jobs missing title/company/url"
  - "Silent skip for network/500 errors (debug log only)"
  - "401/403 show error message suggesting --setup-apis"
  - "Per-source mapper functions for clear separation of concerns"

patterns-established:
  - "Pattern 1: API fetchers check credentials first, then rate limit, then fetch"
  - "Pattern 2: Mapper functions validate required fields strictly, return None for invalid"
  - "Pattern 3: Sequential fetch with _run_queries_parallel() helper to avoid duplication"
  - "Pattern 4: Cross-source deduplication runs after all sources complete"

# Metrics
duration: 3.4min
completed: 2026-02-10
---

# Phase 13 Plan 02: Adzuna and Authentic Jobs Integration Summary

**Adzuna and Authentic Jobs API fetchers integrated with sequential scraper-then-API pipeline and cross-source fuzzy deduplication**

## Performance

- **Duration:** 3.4 min
- **Started:** 2026-02-10T16:30:32Z
- **Completed:** 2026-02-10T16:33:51Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Adzuna API fetcher with salary data extraction (salary_min, salary_max, salary_currency)
- Authentic Jobs API fetcher with defensive nested access for unclear API structure
- Both fetchers validate credentials and rate limits before making requests
- Per-source mapper functions with strict validation - skip jobs missing required fields
- Sequential fetch pipeline runs scrapers first, then APIs supplement results
- Cross-source deduplication runs after all sources complete using fuzzy matching
- All 174 existing tests pass without modification

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement Adzuna and Authentic Jobs API fetchers with mappers** - `e47f52b` (feat)
2. **Task 2: Integrate API sources with sequential scraper-then-API flow and deduplication** - `2d4decf` (feat)

## Files Created/Modified
- `job_radar/sources.py` - Added fetch_adzuna() and fetch_authenticjobs() with per-source mappers, updated build_search_queries() to include API sources, refactored fetch_all() to sequential scraper-then-API flow with cross-source deduplication

## Decisions Made

**Sequential Fetch Order:**
- Scrapers run first (Dice, HN Hiring, RemoteOK, WWR), then APIs (Adzuna, Authentic Jobs)
- Provides users with initial scraper results faster while APIs supplement
- Single progress bar tracks across both phases continuously

**Error Handling Strategy:**
- 401/403 authentication errors: log.error with --setup-apis suggestion (actionable)
- Network/500 errors: log.debug silent skip (transient, not actionable)
- Rate limit hits: log.warning with retry time (handled by check_rate_limit)
- Missing credentials: return [] silently (get_api_key logs warning)

**Mapper Validation:**
- Strict validation: jobs missing title/company/url are skipped and logged at debug level
- HTML stripped from descriptions with strip_html_and_normalize()
- Locations normalized with parse_location_to_city_state()
- Adzuna salary fields populate salary_min/max/currency (backward compatible)

**Code Structure:**
- Created _run_queries_parallel() helper function to avoid duplicating ThreadPoolExecutor logic
- Per-source mapper functions (map_adzuna_to_job_result, map_authenticjobs_to_job_result)
- Authentic Jobs mapper uses defensive nested access due to unclear API docs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - straightforward implementation following established patterns from Phase 13-01.

## User Setup Required

None - API credentials are optional. Sources are skipped gracefully when credentials missing. Users can run `job-radar --setup-apis` to configure.

## Next Phase Readiness

**Ready for additional API sources:**
- Pattern established for API fetchers (credential check → rate limit → fetch → map)
- Sequential pipeline supports mixing scrapers and APIs
- Cross-source deduplication prevents duplicates across all sources
- All existing tests pass

**Foundation complete for:**
- 14-wellfound-integration: Can follow same pattern (fetcher + mapper + add to queries)
- Additional job sources: Pattern generalizes to any API or scraper

**No blockers or concerns.**

---
*Phase: 13-job-source-apis*
*Completed: 2026-02-10*
