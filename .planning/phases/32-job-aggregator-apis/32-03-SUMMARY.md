---
phase: 32-job-aggregator-apis
plan: 03
subsystem: search-pipeline
tags: [jsearch, usajobs, deduplication, source-ordering, multi-source-tracking]

# Dependency graph
requires:
  - phase: 32-job-aggregator-apis
    plan: 01
    provides: JSearch and USAJobs fetch functions with rate limiting
  - phase: 32-job-aggregator-apis
    plan: 02
    provides: API setup wizard extensions and federal profile fields
provides:
  - JSearch and USAJobs integrated into main search workflow
  - Three-phase source ordering (scrapers -> APIs -> aggregators)
  - Enhanced deduplication with multi-source tracking and stats reporting
  - JSearch source splitting for accurate progress display
affects: [cli-output, gui-progress, reporting, deduplication]

# Tech tracking
tech-stack:
  added: []
  patterns: [three-phase-source-ordering, multi-source-dedup-tracking, source-attribution-splitting]

key-files:
  created: []
  modified:
    - job_radar/sources.py
    - job_radar/deduplication.py
    - job_radar/search.py
    - job_radar/gui/worker_thread.py
    - tests/test_deduplication.py
    - tests/test_ux.py

key-decisions:
  - "Three-phase source ordering ensures native sources win in dedup (scrapers -> APIs -> aggregators)"
  - "JSearch display sources (linkedin/indeed/glassdoor) tracked separately for accurate progress"
  - "Deduplication returns dict with results, stats, and multi-source map for enhanced reporting"
  - "Dedup stats displayed in CLI when duplicates found (improves transparency)"
  - "USAJobs added to API_SOURCES (native federal source runs before JSearch aggregator)"

patterns-established:
  - "Source priority through execution order: scrapers first, APIs second, aggregators last"
  - "Progress display source splitting: JSearch query source != result source for accurate tracking"
  - "Deduplication stats tracking: original count, deduped count, sources involved, multi-source map"

# Metrics
duration: 330s
completed: 2026-02-13T20:07:37Z
---

# Phase 32 Plan 03: JSearch and USAJobs Integration into Search Pipeline Summary

**Three-phase source ordering with enhanced deduplication stats for accurate job tracking**

## Performance

- **Duration:** 5 min 30 sec
- **Started:** 2026-02-13T20:02:07Z
- **Completed:** 2026-02-13T20:07:37Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- JSearch and USAJobs fully integrated into main search workflow with query generation from profile
- Three-phase fetch ordering ensures native sources win in dedup (scrapers -> APIs -> aggregators)
- Enhanced deduplication tracks multi-source matches and reports detailed statistics
- CLI displays dedup stats when duplicates found for improved transparency
- JSearch results split by actual source (linkedin/indeed/glassdoor) for accurate progress display
- All 460 tests passing with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Update query builder and fetch_all for JSearch and USAJobs integration** - `f67d896` (feat)
2. **Task 2: Enhance deduplication with multi-source tracking and stats** - `8b80a14` (feat)

## Files Created/Modified

### Modified

- `job_radar/sources.py` (+56/-7 lines)
  - Updated `build_search_queries` to generate jsearch and usajobs queries
  - JSearch queries map location from profile arrangement (remote/city)
  - USAJobs queries include location when specified
  - Updated `fetch_all` to three-phase execution with AGGREGATOR_SOURCES
  - USAJobs added to API_SOURCES (native federal source)
  - Updated `run_query` dispatch to handle jsearch and usajobs
  - JSearch results tracked by actual source for split display
  - Source names replaced jsearch with individual display sources
  - Phase 3 executes aggregator queries after APIs
  - Updated to return (results, dedup_stats) tuple

- `job_radar/deduplication.py` (+73/-9 lines)
  - Changed return type from list to dict with results/stats/multi_source
  - Multi-source tracking records sources for duplicate jobs
  - Stats include original_count, deduped_count, duplicates_removed, sources_involved
  - Handles empty list and single job edge cases with proper dict structure

- `job_radar/search.py` (+8/-1 lines)
  - Destructures new fetch_all return value (results, dedup_stats)
  - Displays dedup stats when duplicates found
  - Updated sources_searched to include LinkedIn, Indeed, Glassdoor, USAJobs (Federal)

- `job_radar/gui/worker_thread.py` (+4/-1 lines)
  - Destructures new fetch_all return value
  - Updated sources_searched list with new sources

- `tests/test_deduplication.py` (+31/-31 lines)
  - Updated all test assertions to use result["results"] instead of result
  - Added stats validation to edge case tests

- `tests/test_ux.py` (+1/-1 lines)
  - Updated fetch_all mock to return proper tuple format

## Decisions Made

**Three-Phase Source Ordering:**
- Phase 1: Scrapers (dice, hn_hiring, remoteok, weworkremotely)
- Phase 2: APIs (adzuna, authentic_jobs, usajobs)
- Phase 3: Aggregators (jsearch)
- Native sources run before aggregators to ensure dedup keeps original posting
- USAJobs is native federal source (not an aggregator), runs in Phase 2

**JSearch Source Splitting:**
- JSearch queries use source="jsearch" but results have source="linkedin"/"indeed"/"glassdoor"
- Progress tracking displays individual sources (not "jsearch")
- Source job counts tracked by actual result source (r.source) not query source
- Source names list replaces "jsearch" with display sources for accurate total count

**Deduplication Enhancement:**
- Return type changed from list to dict with results/stats/multi_source
- Multi-source map tracks jobs found on 2+ sources (for future badge feature)
- Stats provide visibility into dedup effectiveness
- CLI displays stats when duplicates found: "N duplicates removed across M sources"

**Sources Searched List:**
- Updated to include all new sources for accurate reporting
- LinkedIn, Indeed, Glassdoor shown as separate sources (not "JSearch")
- USAJobs displayed as "USAJobs (Federal)" for clarity

## Deviations from Plan

None - plan executed exactly as written.

## Testing Results

- All 460 tests passing (no regressions)
- Deduplication tests: 22/22 passing with new return type
- UX tests: updated mock to match new fetch_all signature
- CLI tests: verify update flags don't call fetch_all
- Integration verified: query generation includes jsearch and usajobs sources

## Technical Notes

**Query Generation:**
```python
# JSearch queries: each target title (aggregates LinkedIn, Indeed, Glassdoor)
for title in titles:
    jsearch_query = {"source": "jsearch", "query": title}
    # Location mapping: match location_preference
    arrangement = profile.get("arrangement", [])
    if "remote" in [a.lower() for a in arrangement]:
        jsearch_query["location"] = "remote"
    elif location:
        jsearch_query["location"] = location
    queries.append(jsearch_query)

# USAJobs queries: each target title
for title in titles:
    usajobs_query = {"source": "usajobs", "query": title}
    if location:
        usajobs_query["location"] = location
    queries.append(usajobs_query)
```

**Three-Phase Execution:**
```python
# Split queries into three phases
SCRAPER_SOURCES = {"dice", "hn_hiring", "remoteok", "weworkremotely"}
API_SOURCES = {"adzuna", "authentic_jobs", "usajobs"}  # USAJobs is native
AGGREGATOR_SOURCES = {"jsearch"}  # JSearch runs LAST

# Phase 1: Scrapers
scraper_results = _run_queries_parallel(scraper_queries, "scraper")
all_results.extend(scraper_results)

# Phase 2: APIs
api_results = _run_queries_parallel(api_queries, "api")
all_results.extend(api_results)

# Phase 3: Aggregators (run last — native sources win in dedup)
aggregator_results = _run_queries_parallel(aggregator_queries, "aggregator")
all_results.extend(aggregator_results)
```

**Deduplication Stats:**
```python
# Return format
{
    "results": [JobResult, ...],
    "stats": {
        "original_count": 150,
        "deduped_count": 120,
        "duplicates_removed": 30,
        "sources_involved": 4
    },
    "multi_source": {
        ("software engineer", "google"): ["dice", "linkedin", "indeed"]
    }
}
```

**JSearch Source Splitting:**
```python
# Track by actual source (for JSearch split display)
for r in results:
    key = (r.title.lower().strip(), r.company.lower().strip())
    if key not in seen:
        seen.add(key)
        phase_results.append(r)
        # Use actual source from result, not query source
        actual_source = r.source  # "linkedin", "indeed", etc.
        source_job_counts[actual_source] = source_job_counts.get(actual_source, 0) + 1
```

## Integration Points

**Upstream (depends on):**
- Plan 32-01: fetch_jsearch and fetch_usajobs functions
- Plan 32-02: API setup wizard for credential configuration
- Phase 31: Rate limiter infrastructure

**Downstream (will use this):**
- CLI: Displays dedup stats in progress output
- GUI: Uses enhanced worker_thread with new sources
- Reports: sources_searched includes all new sources
- Future: Multi-source badges can use multi_source map

## User Impact

**Visible Changes:**
- LinkedIn, Indeed, Glassdoor jobs now appear in automated results (via JSearch)
- Federal jobs from USAJobs appear when profile includes federal filters
- Progress display shows individual source names (not "JSearch aggregator")
- Dedup stats displayed when duplicates found: "30 duplicates removed across 4 sources"
- Sources searched list shows all individual sources for transparency

**Setup Required:**
- Run `job-radar --setup-apis` to configure JSearch and USAJobs credentials
- (Optional) Add federal filter fields to profile for USAJobs targeting

## Next Steps

Plan 32-04 (if exists) or Phase 33 will build on this foundation. Source integration complete. Ready for:
- GUI API settings panel (Phase 33)
- Source integration testing (Phase 34)
- Additional aggregator sources (future phases)

## Self-Check

Verifying file existence and commit references:

**Files:**
- ✓ FOUND: /home/corye/Claude/Job-Radar/job_radar/sources.py
- ✓ FOUND: /home/corye/Claude/Job-Radar/job_radar/deduplication.py
- ✓ FOUND: /home/corye/Claude/Job-Radar/job_radar/search.py
- ✓ FOUND: /home/corye/Claude/Job-Radar/job_radar/gui/worker_thread.py
- ✓ FOUND: /home/corye/Claude/Job-Radar/tests/test_deduplication.py
- ✓ FOUND: /home/corye/Claude/Job-Radar/tests/test_ux.py

**Commits:**
- ✓ FOUND: f67d896 (Task 1: JSearch and USAJobs integration)
- ✓ FOUND: 8b80a14 (Task 2: Enhanced deduplication)

**Verification Commands:**
```bash
# Verify query generation includes jsearch and usajobs
source .venv/bin/activate && python -c "from job_radar.sources import build_search_queries; profile = {'target_titles': ['Engineer'], 'target_market': 'Remote', 'core_skills': ['Python'], 'arrangement': ['remote']}; qs = build_search_queries(profile); sources = [q['source'] for q in qs]; assert 'jsearch' in sources; assert 'usajobs' in sources; print('Query generation: OK')"
# Output: Query sources: {'weworkremotely', 'authentic_jobs', 'dice', 'hn_hiring', 'adzuna', 'usajobs', 'remoteok', 'jsearch'}

# Verify deduplication new return type
source .venv/bin/activate && python -c "from job_radar.deduplication import deduplicate_cross_source; result = deduplicate_cross_source([]); assert isinstance(result, dict); assert 'results' in result; assert 'stats' in result; print('Dedup return type: OK')"
# Output: Dedup return type: OK

# Verify all tests pass
source .venv/bin/activate && python -m pytest tests/ -x -q
# Output: 460 passed in 14.54s
```

## Self-Check: PASSED

---
*Phase: 32-job-aggregator-apis*
*Completed: 2026-02-13T20:07:37Z*
