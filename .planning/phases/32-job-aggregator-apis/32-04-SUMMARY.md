---
phase: 32-job-aggregator-apis
plan: 04
subsystem: gui-api-settings-and-tests
tags: [gui, settings, api-configuration, testing, jsearch, usajobs, deduplication]

# Dependency graph
requires:
  - phase: 32-job-aggregator-apis
    plan: 01
    provides: JSearch and USAJobs fetch functions with rate limiting
  - phase: 32-job-aggregator-apis
    plan: 02
    provides: API setup wizard extensions and federal profile fields
  - phase: 32-job-aggregator-apis
    plan: 03
    provides: JSearch/USAJobs integration into search pipeline with dedup stats
provides:
  - GUI Settings tab with API key configuration for all sources
  - Inline API key validation with test buttons
  - Comprehensive test suite covering JSearch, USAJobs, dedup stats
affects: [gui, testing, api-setup]

# Tech tracking
tech-stack:
  added: []
  patterns: [gui-api-settings, inline-validation, atomic-env-writes, comprehensive-test-coverage]

key-files:
  created: []
  modified:
    - job_radar/gui/main_window.py
    - tests/test_sources_api.py
    - tests/test_deduplication.py

key-decisions:
  - "GUI Settings tab provides non-technical users with API configuration interface"
  - "API keys masked by default with Show/Hide toggle for security"
  - "Test buttons validate credentials via inline API requests before saving"
  - "Atomic .env writes using tempfile + replace prevent corruption"
  - "Tip displayed when JSearch not configured to educate users"
  - "All existing dedup tests updated to handle new dict return type"

patterns-established:
  - "GUI API settings pattern: section per source with fields, test button, status indicator"
  - "Inline validation: test API key, show status (✓ Valid, ✗ Invalid, ⚠ Network error)"
  - "Test parameterization for source attribution variants (LinkedIn/Indeed/Glassdoor/Other)"
  - "Fetch function mocking via fetch_with_retry to avoid network calls in tests"

# Metrics
duration: 426s
completed: 2026-02-13T20:18:14Z
---

# Phase 32 Plan 04: GUI API Settings and Comprehensive Tests Summary

**GUI Settings tab with API configuration and full test coverage for JSearch, USAJobs, and deduplication stats**

## Performance

- **Duration:** 7 min 6 sec
- **Started:** 2026-02-13T20:11:08Z
- **Completed:** 2026-02-13T20:18:14Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- GUI Settings tab provides API key configuration for non-technical users
- Inline API validation with test buttons for immediate feedback
- JSearch tip displayed when not configured to drive adoption
- Comprehensive test suite: 18+ new tests covering JSearch, USAJobs, dedup stats
- All 22 existing dedup tests updated for new dict return type
- 482 tests passing (up from 460 baseline)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add API key configuration to GUI Settings tab** - `f96f645` (feat)
2. **Task 2: Add comprehensive tests for JSearch, USAJobs, dedup stats** - `aa4bced` (test)

## Files Created/Modified

### Modified

- `job_radar/gui/main_window.py` (+482 lines)
  - Added Settings tab to main window tabview
  - Created `_build_settings_tab()` method with scrollable API configuration UI
  - JSearch section: API key field with test button and status indicator
  - USAJobs section: email and API key fields with dual-credential validation
  - Adzuna section: App ID and App Key fields
  - Authentic Jobs section: API key field
  - Keys masked by default with Show/Hide toggle buttons
  - Test buttons run validation in background threads (non-blocking)
  - Status indicators: ✓ Valid (green), ✗ Invalid (red), ⚠ Network error (yellow)
  - Tip displayed when JSearch not configured
  - `_save_api_keys()` writes atomically to .env file
  - Individual test methods for each API: `_test_jsearch()`, `_test_usajobs()`, `_test_adzuna()`, `_test_authentic_jobs()`
  - Info dialog for successful save confirmation

- `tests/test_sources_api.py` (+224 lines)
  - Added JSearch mapper tests: 6 parametrized tests for source attribution
  - Added JSearch validation tests: required field checks (title/company/url)
  - Added JSearch feature tests: remote location mapping, salary formatting
  - Added JSearch fetch tests: auth error handling, missing API key handling
  - Added USAJobs mapper tests: nested descriptor extraction, salary mapping
  - Added USAJobs validation tests: dual credential requirement, empty results
  - Added USAJobs fetch tests: federal filter passing (gs_grade_min/max, agencies)
  - Added query builder tests: jsearch/usajobs generation, remote location mapping
  - Total: 18 new tests added

- `tests/test_deduplication.py` (+155 lines, -41 lines)
  - Updated all 22 existing tests to use `dedup["results"]` instead of `result`
  - Added 3 new tests for stats dict validation
  - `test_dedup_returns_stats()`: validates original_count, deduped_count, duplicates_removed, sources_involved
  - `test_dedup_tracks_multi_source()`: validates multi_source map tracks duplicate sources
  - `test_dedup_empty_returns_stats()`: validates empty input returns valid stats with zeros

## Decisions Made

**GUI API Configuration:**
- Settings tab placement: third tab after Profile and Search for discoverability
- Masked keys by default: security best practice, toggle to reveal when needed
- Test button per source: immediate validation feedback prevents configuration errors
- Atomic .env writes: tempfile + replace pattern prevents corruption on crashes
- Status indicators with emojis: ✓ ✗ ⚠ provide clear visual feedback

**Test Coverage Strategy:**
- Parametrize source attribution tests: cover all known sources (LinkedIn/Indeed/Glassdoor) plus unknown (Monster/ZipRecruiter)
- Mock fetch_with_retry: avoid network calls, focus on logic validation
- Update all existing dedup tests: ensure zero regressions with new return type
- Add stats validation: verify dict structure, counts, multi-source tracking

**User Experience:**
- Tip for JSearch: displayed when not configured to educate users about LinkedIn/Indeed/Glassdoor access
- Non-blocking validation: threads prevent GUI freezes during API tests
- Informative status messages: clear communication of validation results

## Deviations from Plan

None - plan executed exactly as written.

## Testing Results

- All 482 tests passing (up from 460 baseline)
- 18+ new tests added:
  - 6 parametrized JSearch source attribution tests
  - 3 JSearch validation tests
  - 2 JSearch feature tests
  - 2 JSearch fetch tests
  - 4 USAJobs mapper/validation tests
  - 1 USAJobs fetch test
  - 3 query builder tests
  - 3 dedup stats tests
- 22 existing dedup tests updated for new return type
- Zero regressions across full test suite
- Test execution time: 14.64 seconds

## Files Changed

**GUI Settings Implementation:**
```python
# New Settings tab with API configuration
_build_settings_tab(parent)
  -> _add_api_section(title, fields, signup_url)
    -> API key entry fields (masked)
    -> Show/Hide toggle buttons
    -> Test button with status indicator
  -> _save_api_keys() - atomic .env write
  -> _test_jsearch/usajobs/adzuna/authentic_jobs() - inline validation
```

**Test Coverage:**
```python
# JSearch tests
test_jsearch_maps_job_publisher_to_source  # 6 variants
test_jsearch_requires_title_company_url
test_jsearch_maps_remote_location
test_jsearch_maps_salary
test_fetch_jsearch_handles_auth_error
test_fetch_jsearch_handles_missing_api_key

# USAJobs tests
test_usajobs_maps_nested_descriptor
test_usajobs_maps_salary_from_remuneration
test_usajobs_requires_both_credentials
test_usajobs_handles_empty_search_result
test_fetch_usajobs_passes_federal_filters

# Query builder tests
test_build_queries_includes_jsearch
test_build_queries_includes_usajobs
test_build_queries_jsearch_remote_location

# Dedup stats tests
test_dedup_returns_stats
test_dedup_tracks_multi_source
test_dedup_empty_returns_stats
```

## Technical Notes

**GUI API Settings Pattern:**
```python
# Section structure
Title label (bold)
Signup URL (gray, small)
Field 1: Label + Entry (masked) + Show button
Field 2: Label + Entry (masked) + Show button
Test button + Status label

# Validation flow
1. User clicks Test button
2. Background thread created
3. Status set to "Testing..." (gray)
4. API request made with entered credentials
5. Response checked: 200 -> ✓ Valid (green), 401/403 -> ✗ Invalid (red), network error -> ⚠ Network error (yellow)
6. Main thread updated via self.after(0, lambda: ...)
```

**Atomic .env Write:**
```python
# Pattern prevents corruption
fd, temp_path = tempfile.mkstemp()
os.write(fd, content.encode("utf-8"))
os.close(fd)
Path(temp_path).replace(dotenv_path)  # Atomic on POSIX
load_dotenv(dotenv_path, override=True)  # Reload env vars
```

**Test Mocking Patterns:**
```python
# Mock fetch_with_retry to avoid network calls
monkeypatch.setattr("job_radar.sources.fetch_with_retry", lambda *args, **kwargs: None)

# Capture URL for param validation
captured_url = []
def mock_fetch(url, headers=None, use_cache=None):
    captured_url.append(url)
    return '{"SearchResult": {"SearchResultItems": []}}'
monkeypatch.setattr("job_radar.sources.fetch_with_retry", mock_fetch)

# Parametrize for multiple variants
@pytest.mark.parametrize("job_publisher,expected_source", [
    ("LinkedIn", "linkedin"),
    ("Indeed", "indeed"),
    ("Glassdoor", "glassdoor"),
    ("Monster", "jsearch_other"),
])
```

## Integration Points

**Upstream (depends on):**
- Plan 32-01: JSearch/USAJobs fetch functions
- Plan 32-02: API setup wizard extensions
- Plan 32-03: Dedup stats dict return type

**Downstream (will use this):**
- Users can configure API keys via GUI without terminal
- Non-technical users get inline validation feedback
- Test suite validates all Phase 32 functionality

## User Impact

**Visible Changes:**
- New Settings tab in GUI main window
- API key configuration fields for all 4 sources (JSearch, USAJobs, Adzuna, Authentic Jobs)
- Test buttons provide immediate validation feedback
- Tip displayed when JSearch not configured
- Save button writes to .env atomically

**User Benefits:**
- No terminal required for API setup
- Immediate feedback on credential validity
- Educational tips drive adoption of new sources
- Secure key handling with masked fields
- Atomic writes prevent .env corruption

**Setup Required:**
- None - GUI provides self-service API configuration

## Next Steps

Phase 32 complete. All 4 plans executed successfully:
- Plan 01: JSearch and USAJobs API integration
- Plan 02: API setup wizard extensions
- Plan 03: JSearch/USAJobs search pipeline integration
- Plan 04: GUI API settings and comprehensive tests

Ready for:
- Phase 33: Additional source integrations (if planned)
- Phase 34: End-to-end integration testing
- Milestone completion: v2.1.0 Source Expansion & Polish

## Self-Check

Verifying file existence and commit references:

**Files:**
- ✓ FOUND: /home/corye/Claude/Job-Radar/job_radar/gui/main_window.py
- ✓ FOUND: /home/corye/Claude/Job-Radar/tests/test_sources_api.py
- ✓ FOUND: /home/corye/Claude/Job-Radar/tests/test_deduplication.py

**Commits:**
- ✓ FOUND: f96f645 (Task 1: GUI API settings)
- ✓ FOUND: aa4bced (Task 2: Comprehensive tests)

**Verification Commands:**
```bash
# Verify GUI imports without errors
source .venv/bin/activate && python -c "from job_radar.gui.main_window import MainWindow; print('GUI import OK')"
# Output: GUI import OK

# Verify JSearch fields exist
grep -c "JSearch" job_radar/gui/main_window.py
# Output: 8

# Verify all tests pass
source .venv/bin/activate && python -m pytest tests/ -x -q
# Output: 482 passed in 14.64s
```

## Self-Check: PASSED

---
*Phase: 32-job-aggregator-apis*
*Completed: 2026-02-13T20:18:14Z*
