---
phase: 13-job-source-apis
plan: 01
subsystem: api
tags: [rapidfuzz, beautifulsoup4, fuzzy-matching, deduplication, text-cleaning, location-parsing]

# Dependency graph
requires:
  - phase: 12-api-foundation
    provides: API credential management (python-dotenv, api_config.py) and rate limiting (pyrate-limiter, rate_limits.py)
provides:
  - Extended JobResult with optional salary_min, salary_max, salary_currency fields
  - strip_html_and_normalize() for HTML tag removal and whitespace normalization
  - parse_location_to_city_state() for location standardization
  - deduplicate_cross_source() for fuzzy deduplication using rapidfuzz
  - Foundation for API fetcher integration
affects: [13-02-adzuna-integration, 13-03-authentic-jobs-integration, 13-04-api-pipeline-integration]

# Tech tracking
tech-stack:
  added: [rapidfuzz]
  patterns: [fuzzy-deduplication, bucketing-optimization, token-sort-ratio-matching]

key-files:
  created: [job_radar/deduplication.py]
  modified: [job_radar/sources.py, pyproject.toml]

key-decisions:
  - "Use rapidfuzz token_sort_ratio for title/company matching (word-order independent)"
  - "Use rapidfuzz ratio for location matching (exact location matters more)"
  - "Bucketing by company first word reduces O(N²) to O(N*B) comparisons"
  - "Keep first occurrence in deduplication (preserves source priority)"
  - "All 50 US states in _STATE_ABBREV map for comprehensive location parsing"

patterns-established:
  - "Pattern 1: Optional dataclass fields with None defaults for backward compatibility"
  - "Pattern 2: HTML cleaning with html.unescape() then BeautifulSoup get_text() then regex whitespace normalization"
  - "Pattern 3: Location parsing with regex patterns and state abbreviation map, graceful fallback to raw string"
  - "Pattern 4: Fuzzy deduplication with exact duplicate fast path, then fuzzy matching within buckets"

# Metrics
duration: 2.7min
completed: 2026-02-10
---

# Phase 13 Plan 01: API Foundation Summary

**Extended JobResult with optional salary fields, created cross-source fuzzy deduplication with rapidfuzz token_sort_ratio, and added HTML stripping and location parsing utilities**

## Performance

- **Duration:** 2.7 min
- **Started:** 2026-02-10T16:25:30Z
- **Completed:** 2026-02-10T16:28:11Z
- **Tasks:** 2
- **Files modified:** 3 (created 1)

## Accomplishments
- JobResult dataclass extended with 3 optional salary fields (salary_min, salary_max, salary_currency)
- Text cleaning utilities: strip_html_and_normalize() removes HTML tags, decodes entities, normalizes whitespace
- Location parsing: parse_location_to_city_state() standardizes to "City, State" format with all 50 US states
- Cross-source fuzzy deduplication module using rapidfuzz with bucketing optimization
- Backward compatibility maintained: all 174 existing tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend JobResult and add text utility functions** - `574f72c` (feat)
2. **Task 2: Create deduplication module and add rapidfuzz dependency** - `aee28c2` (feat)

## Files Created/Modified
- `job_radar/sources.py` - Extended JobResult with salary_min/max/currency fields, added strip_html_and_normalize() and parse_location_to_city_state() functions, added adzuna and authentic_jobs to _SOURCE_DISPLAY_NAMES
- `job_radar/deduplication.py` - Created new module with deduplicate_cross_source() using rapidfuzz token_sort_ratio for fuzzy matching with bucketing optimization
- `pyproject.toml` - Added rapidfuzz to dependencies

## Decisions Made

**Text Cleaning Strategy:**
- Use html.unescape() first (decode entities), then BeautifulSoup get_text() (strip tags), then regex (normalize whitespace) for robust HTML cleaning

**Location Parsing Approach:**
- Three-pattern regex matching: exact "City, ST" format, "City, State Name" with abbreviation map, and "City, State, Country" extraction
- All 50 US states in _STATE_ABBREV map for comprehensive coverage
- Graceful fallback to raw string (better to show raw than guess wrong)

**Deduplication Algorithm:**
- token_sort_ratio for title/company (handles word order variations like "Senior Software Engineer" vs "Software Engineer, Senior")
- Standard ratio for location (exact location matching more important)
- Thresholds: 85 for title/company, 80 for location (high precision)
- Bucketing by company first word reduces comparisons from O(N²) to O(N*B)
- Fast path: exact duplicate check with set lookup before fuzzy matching

**Backward Compatibility:**
- Optional salary fields added at END of JobResult dataclass (after parse_confidence)
- All fields default to None (existing code doesn't need to provide them)
- Verified: all 174 existing tests pass without modification

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - straightforward implementation following established patterns.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for API fetcher implementation:**
- JobResult schema extended and backward compatible
- Text cleaning utilities available for description processing
- Location parsing ready for API location field normalization
- Deduplication module ready to integrate into fetch pipeline
- rapidfuzz installed and verified

**Foundation complete for:**
- 13-02: Adzuna API integration (can use salary fields, location parsing, HTML stripping)
- 13-03: Authentic Jobs API integration (same utilities available)
- 13-04: API pipeline integration (deduplicate_cross_source ready to call)

**No blockers or concerns.**

---
*Phase: 13-job-source-apis*
*Completed: 2026-02-10*
