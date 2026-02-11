---
phase: 14-wellfound-urls
plan: 01
subsystem: job-sources
tags: [wellfound, angellist, manual-urls, startup-jobs]

# Dependency graph
requires:
  - phase: 13-job-source-apis
    provides: API integration infrastructure and generate_manual_urls() pattern
provides:
  - Wellfound manual URL generation with /role/r/ (remote) and /role/l/ (location) patterns
  - Slug generation helper for converting titles/locations to URL-safe format
  - Wellfound integrated as first manual source in search reports
affects: [15-pdf-resume-parsing, future-manual-source-additions]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Slugification pattern for URL path generation (hyphens, lowercase, alphanumeric)"]

key-files:
  created: []
  modified: [job_radar/sources.py, tests/test_sources_api.py]

key-decisions:
  - "Wellfound appears first in manual URL list (top priority for startup jobs)"
  - "No urllib.parse.quote() for Wellfound slugs - uses raw hyphenated path segments"
  - "Remote detection is case-insensitive for flexibility"
  - "No HEAD request validation - Wellfound blocks automated requests (403)"

patterns-established:
  - "Pattern 1: _slugify_for_wellfound() helper for consistent URL slug generation"
  - "Pattern 2: Remote detection via 'remote' substring in location (case-insensitive)"

# Metrics
duration: 2.6min
completed: 2026-02-10
---

# Phase 14 Plan 01: Wellfound URLs Summary

**Wellfound startup job search URLs with /role/r/ remote and /role/l/ location patterns, integrated as first manual source**

## Performance

- **Duration:** 2.6 min
- **Started:** 2026-02-10T17:08:35Z
- **Completed:** 2026-02-10T17:11:09Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Generated Wellfound URLs with role-based search patterns (remote and location variants)
- Integrated Wellfound as top priority manual source (appears first in reports)
- Added comprehensive test coverage with 13 tests (location, remote, slugification edge cases)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement Wellfound URL generator and integrate into manual URLs** - `184fc4e` (feat)
2. **Task 2: Add test coverage for Wellfound URL generation** - `72b34ea` (test)

## Files Created/Modified
- `job_radar/sources.py` - Added _slugify_for_wellfound() helper and generate_wellfound_url() function, integrated Wellfound as first manual source
- `tests/test_sources_api.py` - Added 13 Wellfound tests covering URL generation, slugification, and integration

## Decisions Made

**1. No URL encoding for Wellfound slugs**
- Wellfound expects raw hyphenated path segments (e.g., `/software-engineer`), not percent-encoded values
- Used simple slugification (lowercase, hyphen replacement, alphanumeric filter) instead of urllib.parse.quote()

**2. Wellfound as first manual source**
- Placed Wellfound before Indeed/LinkedIn/Glassdoor in generators list
- Rationale: Startup-focused platform provides unique value, merits top positioning

**3. Case-insensitive remote detection**
- Detects "remote", "Remote", "REMOTE", or "remote - US" in location string
- Uses /role/r/ pattern for remote-only searches

**4. No HEAD request validation**
- Skipped URL validation checks that work for other sources
- Wellfound uses bot protection (returns 403 for automated requests)
- URLs still work for manual user browsing

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation followed research patterns directly. All tests passed on first run.

## User Setup Required

None - no external service configuration required. Wellfound URLs work without API keys or authentication.

## Next Phase Readiness

Wellfound manual URLs are fully integrated into existing report generation infrastructure. No changes needed to report.py or search.py - existing data flow handles Wellfound automatically through generate_manual_urls() return structure.

Ready for Phase 15 (PDF Resume Parsing) - job source infrastructure complete.

---
*Phase: 14-wellfound-urls*
*Completed: 2026-02-10*
