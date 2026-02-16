---
phase: 42-hiring-cafe-integration
plan: 01
subsystem: api
tags: [hiring.cafe, mapper, salary-normalization, tdd, job-sources]

# Dependency graph
requires:
  - phase: 30-jsearch-usajobs
    provides: Source mapper pattern and text utilities (strip_html_and_normalize, parse_location_to_city_state)
provides:
  - map_hiringcafe_to_job_result() mapper function
  - _normalize_salary_to_annual() helper for salary period conversion
  - _format_hiringcafe_salary() helper for standardized salary display
affects: [42-02-hiringcafe-fetcher, job-sources, salary-display]

# Tech tracking
tech-stack:
  added: []
  patterns: [TDD mapper pattern, salary normalization with period conversion, $XXXK format]

key-files:
  created: []
  modified:
    - job_radar/sources.py
    - tests/test_sources_api.py

key-decisions:
  - "Salary format: $120K - $160K (not $120,000 - $160,000) per user decision"
  - "Missing salary displays 'Not listed' (not 'Not specified') for consistency with hiring.cafe UI"
  - "Hourly conversion: 2080 hours/year (40hrs/week x 52 weeks)"
  - "Monthly conversion: 12 months/year"
  - "Fallback heuristics: <500 = hourly, <20000 = monthly, else yearly"

patterns-established:
  - "Salary period normalization pattern for APIs that provide hourly/monthly/yearly salaries"
  - "K-format salary display pattern (short form) vs comma-format (long form)"
  - "Three-function mapper structure: normalize helper, format helper, main mapper"

# Metrics
duration: 220s
completed: 2026-02-16
---

# Phase 42 Plan 01: hiring.cafe Mapper Summary

**TDD mapper with salary normalization converting hourly/monthly/yearly to annual $XXXK format**

## Performance

- **Duration:** 3min 40s
- **Started:** 2026-02-16T12:36:34Z
- **Completed:** 2026-02-16T12:40:14Z
- **Tasks:** 1 (TDD with 3 commits: test, feat, refactor skipped)
- **Files modified:** 2

## Accomplishments
- map_hiringcafe_to_job_result() converts hiring.cafe API response items to JobResult objects with validated fields
- _normalize_salary_to_annual() handles hourly (x2080), monthly (x12), yearly (identity) conversions with fallback heuristics
- _format_hiringcafe_salary() produces standardized $120K - $160K format or "Not listed"
- Missing title/company/url returns None (defensive - skip bad entry without crashing)
- All 15 new tests pass, zero regressions across 106 test_sources_api.py tests

## Task Commits

Each task was committed atomically:

1. **Task 1: TDD hiring.cafe mapper and salary normalization**
   - RED: `ef93074` (test: add failing tests)
   - GREEN: `14d1e61` (feat: implement mapper and helpers)
   - REFACTOR: Skipped (no cleanup needed - implementation clean on first pass)

## Files Created/Modified
- `job_radar/sources.py` - Added map_hiringcafe_to_job_result(), _normalize_salary_to_annual(), _format_hiringcafe_salary() after Jobicy section
- `tests/test_sources_api.py` - Added 15 tests covering valid data, missing fields, salary edge cases, HTML cleaning, truncation

## Decisions Made

**1. Salary format: $120K - $160K (K-format, not comma-format)**
- Rationale: User decision - shorter, cleaner display in reports
- Contrast: Adzuna uses $120,000 - $160,000 (comma-format)

**2. Missing salary: "Not listed" (not "Not specified")**
- Rationale: Matches hiring.cafe UI convention, differentiates from other sources
- Contrast: Jobicy uses "Not specified", Adzuna uses "Not specified"

**3. Hourly conversion factor: 2080 hours/year**
- Rationale: Standard full-time calculation (40 hours/week x 52 weeks)
- Example: $75/hour → $156,000/year

**4. Fallback heuristics when period is ambiguous**
- If value < 500: assume hourly (e.g., 50 → 50 * 2080 = 104,000)
- If value < 20,000: assume monthly (e.g., 8,000 → 8,000 * 12 = 96,000)
- Else: assume yearly (e.g., 120,000 → 120,000)
- Rationale: Handles cases where API doesn't provide salary_period field

## Deviations from Plan

None - plan executed exactly as written. All 15 tests implemented and passed as specified.

## Issues Encountered

None - TDD cycle proceeded smoothly. Tests written first (RED), implementation made them pass (GREEN), no refactoring needed.

## User Setup Required

None - no external service configuration required. This is a pure mapper function (data transformation layer).

## Next Phase Readiness

**Ready for Phase 42 Plan 02 (hiring.cafe API fetcher):**
- Mapper function available: map_hiringcafe_to_job_result()
- Salary normalization tested and working
- HTML cleaning and truncation working via strip_html_and_normalize()
- Location normalization working via parse_location_to_city_state()
- Arrangement detection working via _parse_arrangement()

**Blocker:** hiring.cafe API endpoint discovery still needed (research phase prerequisite)

## Self-Check: PASSED

All claims verified:
- FOUND: job_radar/sources.py (modified file exists)
- FOUND: tests/test_sources_api.py (test file exists)
- FOUND: ef93074 (RED phase commit)
- FOUND: 14d1e61 (GREEN phase commit)
- FOUND: map_hiringcafe_to_job_result function
- FOUND: _normalize_salary_to_annual function
- FOUND: _format_hiringcafe_salary function

---
*Phase: 42-hiring-cafe-integration*
*Completed: 2026-02-16*
