---
phase: 31-rate-limiter-infrastructure
plan: 02
subsystem: rate-limiting
tags: [configuration, dynamic-config, config-validation]

dependency_graph:
  requires: [31-01, config-module]
  provides: [config-driven-rate-limits, rate-limit-overrides]
  affects: [rate-limiter-infrastructure, config-system]

tech_stack:
  added: []
  patterns: [config-merge, validation-with-fallback, defensive-loading]

key_files:
  created: []
  modified:
    - job_radar/config.py
    - job_radar/rate_limits.py
    - tests/test_config.py
    - tests/test_rate_limits.py
    - tests/test_browser.py

decisions:
  - decision: Merge config overrides with hardcoded defaults
    rationale: Partial overrides allow users to customize only specific APIs while keeping defaults for others
    alternatives: [replace-all, require-complete-config]
    impact: better-ux
  - decision: Validate config structure and values, warn on invalid entries
    rationale: Invalid configs should not crash application - graceful degradation with warnings
    alternatives: [fail-fast, silent-ignore]
    impact: robustness
  - decision: Config format uses limit (int) and interval (seconds)
    rationale: Matches pyrate-limiter Rate structure directly, clear semantics
    alternatives: [duration-strings, rate-per-minute-syntax]
    impact: simplicity

metrics:
  duration_seconds: 213
  completed_date: 2026-02-13T18:31:13Z
  tasks_completed: 1
  files_modified: 5
  tests_added: 4
  tests_passing: 460
---

# Phase 31 Plan 02: Configuration-Driven Rate Limits Summary

**One-liner:** Dynamic rate limit configuration from config.json with validation, merge behavior, and graceful fallback to defaults

## What Was Built

Implemented dynamic rate limit loading from config.json, allowing users to customize rate limits for their API tier (e.g., premium Adzuna users) without editing source code. Config overrides merge with hardcoded defaults, and invalid configs show clear warnings while falling back to safe defaults.

### Task 1: Add rate limit config loading to config.py and rate_limits.py

**Commit:** e3351a1

Enabled rate limits to be loaded from config.json with validation and merge behavior.

**Implementation:**

1. **Updated config.py:**
   - Added "rate_limits" to KNOWN_KEYS set (line 21)
   - No other changes needed (load_config already handles arbitrary keys)

2. **Updated rate_limits.py:**
   - Added import: `from .config import load_config`
   - Created `_load_rate_limits()` function with:
     - Hardcoded defaults as fallback
     - Config file loading via `load_config()`
     - Type validation for dict/list/dict entries
     - Value validation for positive int limits and positive number intervals
     - Warning logs for invalid entries (skips bad entries, doesn't crash)
     - Merge logic: config overrides replace defaults for specified backends only
     - Debug log when custom limits loaded
   - Replaced `RATE_LIMITS = {...}` with `RATE_LIMITS = _load_rate_limits()`
   - Updated module docstring with config.json format example

3. **Added tests:**
   - **tests/test_config.py:**
     - `test_config_recognizes_rate_limits_key()` - Verifies "rate_limits" in KNOWN_KEYS
     - Updated `test_known_keys_membership` parametrization to include rate_limits
     - Updated `test_known_keys_exact_size` to expect 6 keys

   - **tests/test_rate_limits.py:**
     - `test_rate_limits_loaded_from_config()` - Verifies custom limits override defaults
     - `test_rate_limits_invalid_config_uses_defaults()` - Verifies graceful fallback with warnings
     - `test_rate_limits_config_override_merges_with_defaults()` - Verifies partial override behavior

   - **tests/test_browser.py:**
     - Updated `test_config_known_keys_count()` to expect 6 keys instead of 5

**Files modified:**
- `job_radar/config.py` - Added "rate_limits" to KNOWN_KEYS
- `job_radar/rate_limits.py` - Added dynamic config loading with validation
- `tests/test_config.py` - Added rate_limits key test, updated size checks
- `tests/test_rate_limits.py` - Added 3 config loading tests
- `tests/test_browser.py` - Updated KNOWN_KEYS count expectation

**Config format:**
```json
{
  "rate_limits": {
    "adzuna": [{"limit": 200, "interval": 60}],
    "jsearch": [{"limit": 100, "interval": 60}, {"limit": 500, "interval": 3600}]
  }
}
```

**Validation behavior:**
- `rate_limits` must be a dict → warning + use defaults
- Each backend value must be a list → warning + skip backend
- Each rate entry must be a dict → warning + skip entry
- `limit` must be positive int → warning + skip entry
- `interval` must be positive number → warning + skip entry
- Valid entries create Rate objects and override defaults

**Merge behavior:**
- Defaults: `{"adzuna": [...], "authentic_jobs": [...]}`
- Config: `{"adzuna": [...]}`
- Result: `{"adzuna": [config], "authentic_jobs": [default]}`

Only specified backends are overridden; unspecified backends keep defaults.

**Why this design:**
- Users with premium API tiers can increase limits without code changes
- Invalid configs don't crash the application (robustness)
- Partial overrides are user-friendly (don't have to specify all backends)
- Validation ensures only valid Rate objects are created
- Warning logs help users debug config issues
- Backward compatible (missing config = defaults work)

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

**All verifications passed:**

1. **Full test suite:** 460 tests passing (no regressions)

2. **New tests added:**
   - `test_config_recognizes_rate_limits_key` - PASSED
   - `test_rate_limits_loaded_from_config` - PASSED
   - `test_rate_limits_invalid_config_uses_defaults` - PASSED
   - `test_rate_limits_config_override_merges_with_defaults` - PASSED

3. **Manual verification:**
   ```bash
   # Created config with custom adzuna limit (200/min)
   python -c "from job_radar.rate_limits import RATE_LIMITS; print(RATE_LIMITS['adzuna'])"
   # Output: [limit=200/60]  (custom limit applied)
   ```

4. **Invalid config test:**
   - Config with `"rate_limits": "not_a_dict"` → warnings logged, defaults used
   - Config with negative/zero limits → entries skipped, warnings logged

5. **Log output verified:**
   - "Loaded custom rate limits for adzuna: 1 rate(s)" appears in debug logs when config present

## Success Criteria Met

- [x] Rate limit configurations loadable from config.json (INFRA-03)
- [x] Invalid configs show clear warnings and fall back to defaults
- [x] Config format documented in rate_limits.py module docstring
- [x] All tests pass including new config loading tests
- [x] Backward compatible - missing config uses hardcoded defaults
- [x] Config overrides merge with defaults (partial overrides supported)
- [x] KNOWN_KEYS includes "rate_limits" key

## Technical Notes

### Config Merge Strategy

The implementation uses a **merge** strategy rather than a **replace** strategy:

```python
result = defaults.copy()
for backend_api, rate_configs in config_limits.items():
    # ... validation ...
    if rates:
        result[backend_api] = rates  # Override only this backend
```

This means:
- Users only need to specify backends they want to customize
- Unspecified backends retain safe defaults
- Adding new backends to code doesn't require config updates

### Validation Philosophy: Warn and Skip

Invalid config entries are skipped with warnings rather than failing fast:

```python
if not isinstance(limit, int) or limit <= 0:
    log.warning("Config rate_limits[%s] limit must be positive int - skipping", backend_api)
    continue  # Skip this entry, try next one
```

This ensures:
- Application doesn't crash on bad config
- Users see clear warnings about what's wrong
- Defaults provide safe fallback behavior
- Partial configs with some invalid entries still work

### Module-Level Loading

Rate limits are loaded at module import time via `RATE_LIMITS = _load_rate_limits()`:

**Pros:**
- Simple, no global state management
- Config read once at startup (fast)
- No race conditions

**Cons:**
- Config changes require application restart
- Tests need module reload to pick up config changes

For a CLI tool (not a long-running service), this tradeoff is acceptable.

## Impact on Future Work

**Phase 32 (Job Aggregator APIs - JSearch):**
- Users with JSearch premium tiers can now configure custom rate limits:
  ```json
  {
    "rate_limits": {
      "jsearch": [{"limit": 200, "interval": 60}]
    }
  }
  ```
- Shared backend limiter (from Plan 01) + config-driven limits = full customization

**General:**
- Pattern established for any config-driven behavior
- Validation approach can be reused for other config keys
- Documentation template in module docstring

## Files Changed

**Modified:**
- `/home/corye/Claude/Job-Radar/job_radar/config.py` (78 → 78 lines, +1 key to KNOWN_KEYS)
- `/home/corye/Claude/Job-Radar/job_radar/rate_limits.py` (229 → 296 lines, +67 lines)
  - Added load_config import
  - Added _load_rate_limits() function
  - Updated module docstring
  - Changed RATE_LIMITS to dynamic loading
- `/home/corye/Claude/Job-Radar/tests/test_config.py` (205 → 218 lines, +13 lines)
  - Added test_config_recognizes_rate_limits_key
  - Updated test_known_keys_membership parametrization
  - Updated test_known_keys_exact_size
- `/home/corye/Claude/Job-Radar/tests/test_rate_limits.py` (193 → 304 lines, +111 lines)
  - Added test_rate_limits_loaded_from_config
  - Added test_rate_limits_invalid_config_uses_defaults
  - Added test_rate_limits_config_override_merges_with_defaults
- `/home/corye/Claude/Job-Radar/tests/test_browser.py` (180 → 180 lines, 1 line changed)
  - Updated test_config_known_keys_count to expect 6 keys

**Created:**
- None

## Commits

1. `e3351a1` - feat(31-rate-limiter-infrastructure): add configuration-driven rate limits

## Self-Check

Verifying all claims in this summary:

**Files exist:**
- `/home/corye/Claude/Job-Radar/job_radar/config.py` - FOUND
- `/home/corye/Claude/Job-Radar/job_radar/rate_limits.py` - FOUND
- `/home/corye/Claude/Job-Radar/tests/test_config.py` - FOUND
- `/home/corye/Claude/Job-Radar/tests/test_rate_limits.py` - FOUND
- `/home/corye/Claude/Job-Radar/tests/test_browser.py` - FOUND

**Commits exist:**
- e3351a1 - FOUND

**Tests pass:**
- test_config_recognizes_rate_limits_key - PASSED
- test_rate_limits_loaded_from_config - PASSED
- test_rate_limits_invalid_config_uses_defaults - PASSED
- test_rate_limits_config_override_merges_with_defaults - PASSED
- Full suite (460 tests) - PASSED

**Key features verified:**
- "rate_limits" in KNOWN_KEYS - FOUND
- _load_rate_limits() function exists - FOUND
- Config loading from load_config() - FOUND
- Validation and warning logs - VERIFIED (via test)
- Module docstring with config format - FOUND

## Self-Check: PASSED

All claims verified. Summary is accurate.
