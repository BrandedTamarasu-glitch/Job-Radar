---
phase: 32-job-aggregator-apis
plan: 02
subsystem: API Integration
tags: [api, setup-wizard, profile-schema, jsearch, usajobs, federal-jobs]
dependency_graph:
  requires: [31-rate-limiter-infrastructure]
  provides: [jsearch-api-setup, usajobs-api-setup, federal-profile-fields]
  affects: [api-setup-wizard, profile-schema, credential-management]
tech_stack:
  added: []
  patterns: [inline-validation, atomic-writes, forward-compatible-schemas]
key_files:
  created: []
  modified:
    - job_radar/api_setup.py
    - profiles/_template.json
decisions:
  - "Validate API keys during setup with inline test requests (immediate feedback)"
  - "Store keys even on validation failure (network issues shouldn't block setup)"
  - "Show tips when JSearch not configured (user education)"
  - "Profile schema forward-compatible design accepts new optional fields without code changes"
metrics:
  duration_seconds: 158
  tasks_completed: 2
  files_modified: 2
  tests_added: 0
  tests_passing: 460
  completed_at: "2026-02-13T19:57:56Z"
---

# Phase 32 Plan 02: API Setup Extensions Summary

**One-liner:** Extended setup wizard for JSearch and USAJobs with inline credential validation, added federal job filter fields to profile schema

## What Was Built

Extended the API setup wizard (`--setup-apis`) and profile schema to support JSearch (LinkedIn/Indeed/Glassdoor aggregator) and USAJobs (federal government jobs) as new job sources.

### Task 1: API Setup Wizard Extensions

Added JSearch and USAJobs credential collection to both `setup_apis()` and `test_apis()` functions:

**JSearch Setup (Section 3):**
- Single API key from RapidAPI platform
- Inline validation with test request to `jsearch.p.rapidapi.com/search`
- Headers follow exact case requirements: `X-RapidAPI-Key`, `X-RapidAPI-Host`
- Validation reports: ✓ valid, ✗ invalid (401/403), or ⚠ network error
- Keys stored even on validation failure (network issues shouldn't block setup)
- Tip shown when JSearch skipped: "Set up JSearch API key to search LinkedIn, Indeed, and Glassdoor"

**USAJobs Setup (Section 4):**
- Two credentials: email (User-Agent) + API key (Authorization-Key)
- Both required together (skip both if either missing)
- Inline validation with test request to `data.usajobs.gov/api/search`
- Headers follow USAJobs spec: `Host`, `User-Agent` (email), `Authorization-Key`
- Same validation feedback pattern as JSearch

**Updated Components:**
- Summary section now displays JSearch and USAJobs configured sources
- .env file builder writes JSearch and USAJobs credential sections
- `test_apis()` includes JSearch and USAJobs validation tests
- Tip displayed in both setup and test commands when JSearch not configured

### Task 2: Federal Job Profile Fields

Added optional USAJobs-specific filter fields to profile schema:

**New Fields in `_template.json`:**
- `gs_grade_min`: integer or null (GS grade 1-15, e.g., 12)
- `gs_grade_max`: integer or null (GS grade 1-15, e.g., 14)
- `preferred_agencies`: list of strings (agency codes like "TREAS", "DD")
- `security_clearance`: string or null ("None", "Secret", "Top Secret")

**Implementation Notes:**
- All fields optional with null/empty defaults
- `_comment_federal` field provides inline documentation (ignored by loader)
- Profile manager's forward-compatible validation silently accepts new fields
- No code changes needed in `profile_manager.py` (design validated)

## Deviations from Plan

None - plan executed exactly as written.

## Key Decisions Made

1. **Inline validation during setup:** Test API keys immediately after collection and report status before saving. Provides instant feedback but still saves keys on network errors (user might have temporary network issues).

2. **Graceful validation failure handling:** On network/timeout errors during setup, still save the key with warning "⚠ Could not validate (network error) — key saved anyway". Prevents blocking setup due to transient issues.

3. **Educational tips for JSearch:** Show tip when JSearch not configured in both `setup_apis()` summary and `test_apis()` skip message. Increases discoverability of LinkedIn/Indeed/Glassdoor sources.

4. **Forward-compatible profile schema:** New federal fields leverage existing forward-compatible validation design. `profile_manager.py` silently accepts unknown fields per line 84 comment, requiring zero code changes.

## Testing Results

- All 460 tests passing (no regressions)
- Profile manager tests: 22/22 passing with new fields
- No new tests added (setup wizard has manual testing pattern)
- Verified:
  - api_setup.py compiles without syntax errors
  - JSearch sections appear 9 times (setup + test + summary + .env + tips)
  - USAJobs sections appear 6 times (setup + test + summary + .env)
  - Template JSON validates and includes all 4 new fields
  - Profile manager accepts new fields via forward-compatible validation

## Files Changed

### Modified
- `job_radar/api_setup.py` (+196 lines)
  - Added JSearch setup section with inline validation
  - Added USAJobs setup section with inline validation
  - Updated summary to show JSearch and USAJobs configured sources
  - Updated .env builder to write JSearch and USAJobs sections
  - Added JSearch and USAJobs tests to `test_apis()`
  - Added JSearch tip when not configured

- `profiles/_template.json` (+6 lines)
  - Added `gs_grade_min`, `gs_grade_max`, `preferred_agencies`, `security_clearance` fields
  - Added `_comment_federal` documentation field

## Technical Notes

**API Key Validation Pattern:**
```python
print("  Testing...", end=" ", flush=True)
try:
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        print("✓ Key is valid")
    elif response.status_code in (401, 403):
        print("✗ Invalid key")
    else:
        print("⚠ Could not validate — key saved anyway")
    credentials["KEY"] = key.strip()  # Always save
except (requests.Timeout, requests.RequestException):
    print("⚠ Could not validate (network error) — key saved anyway")
    credentials["KEY"] = key.strip()
```

**USAJobs Header Requirements (Critical):**
- `Host: data.usajobs.gov` (required)
- `User-Agent: {email}` (must be email from API registration)
- `Authorization-Key: {api_key}` (not "Authorization")

**JSearch Header Requirements (Critical):**
- `X-RapidAPI-Key: {api_key}` (exact case)
- `X-RapidAPI-Host: jsearch.p.rapidapi.com` (exact case)

## Integration Points

**Downstream (will use this):**
- Plan 32-01 (already implemented): JSearch and USAJobs fetchers in `sources.py` use these credentials
- Future source implementations can follow same inline validation pattern

**Upstream (depends on this):**
- Users must run `job-radar --setup-apis` to configure new sources
- Profile templates now support federal job filters for USAJobs queries

## Next Steps

Plan 32-03 will integrate JSearch and USAJobs sources into the main job search workflow, using the credentials configured here.

## Self-Check

Verifying file existence and commit references:

**Files:**
- ✓ FOUND: /home/corye/Claude/Job-Radar/job_radar/api_setup.py
- ✓ FOUND: /home/corye/Claude/Job-Radar/profiles/_template.json

**Commits:**
- ✓ FOUND: d7f61fb (Task 1: API setup wizard extensions)
- ✓ FOUND: 32642c1 (Task 2: Profile schema federal fields)

## Self-Check: PASSED
