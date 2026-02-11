---
phase: 08-entry-point-integration
plan: 01
subsystem: cli
tags: [config, wizard, profile, argparse, error-recovery]

# Dependency graph
requires:
  - phase: 07-interactive-setup-wizard
    provides: wizard that creates profile.json
  - phase: 02-config-file-support
    provides: config.py with KNOWN_KEYS for recognized fields
provides:
  - Automatic profile path resolution (wizard -> config.json -> search)
  - Profile corruption recovery with wizard re-run
  - Developer flags (--no-wizard, --validate-profile)
  - Wizard-to-search data flow via config.json profile_path field
affects: [09-reporting-overhaul, 10-job-tracker-enhancements]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Config-based profile path resolution with CLI override"
    - "Wizard recovery pattern: backup corrupt files before re-running wizard"
    - "Local imports to avoid circular dependencies (wizard in search.py)"

key-files:
  created: []
  modified:
    - job_radar/config.py
    - job_radar/wizard.py
    - job_radar/search.py
    - job_radar/__main__.py
    - tests/test_config.py

key-decisions:
  - "Profile path resolution order: CLI --profile > config.json profile_path > default location"
  - "load_profile_with_recovery uses local wizard imports to avoid circular imports"
  - "Corrupt profiles backed up to .bak before wizard re-run (prevents data loss)"
  - "--no-wizard bypasses wizard in both __main__.py and search.py for testing"
  - "Max 2 retry attempts in load_profile_with_recovery to prevent infinite loops"

patterns-established:
  - "Two-mode profile loading: load_profile (strict) vs load_profile_with_recovery (auto-fix)"
  - "Pre-parse argparse pattern for flags needed before main arg parsing"

# Metrics
duration: 11min
completed: 2026-02-09
---

# Phase 8 Plan 1: Entry Point Integration Summary

**Wizard-generated profiles auto-flow into search via config.json bridge with corruption recovery, validation flags, and no more required --profile flag**

## Performance

- **Duration:** 11 min
- **Started:** 2026-02-09T20:54:55Z
- **Completed:** 2026-02-09T21:05:37Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Profile path automatically resolved from config.json (wizard writes it, search reads it)
- Corrupt/missing profiles trigger wizard re-run with backup of corrupt file
- Developer flags added: --no-wizard (skip wizard) and --validate-profile (validate and exit)
- Backward compatibility: CLI --profile still works and overrides config.json

## Task Commits

Each task was committed atomically:

1. **Task 1: Add profile_path to config.py and wizard.py config output** - `df35369` (feat)
2. **Task 2: Refactor search.py with profile path resolution, recovery, and developer flags** - `d64dbac` (feat)

## Files Created/Modified
- `job_radar/config.py` - Added profile_path to KNOWN_KEYS, updated comment
- `job_radar/wizard.py` - Writes profile_path (absolute path) to config.json
- `job_radar/search.py` - Added load_profile_with_recovery(), --no-wizard, --validate-profile flags, profile path resolution
- `job_radar/__main__.py` - Pre-parses --no-wizard flag to skip first-run wizard check
- `tests/test_config.py` - Updated test to expect 4 KNOWN_KEYS (was 3)

## Decisions Made

**Profile path resolution order:** CLI --profile > config.json profile_path > default location
- Rationale: CLI override preserves existing workflows, config.json enables wizard flow, default location provides fallback

**Circular import prevention:** load_profile_with_recovery uses local wizard imports
- Rationale: search.py imports wizard in function scope (not module scope) to avoid circular dependency (wizard -> search.main(), search -> wizard.run_setup_wizard)

**Corruption recovery with backup:** Corrupt profiles backed up to .bak before wizard re-run
- Rationale: Prevents data loss if user had manually edited profile with syntax error

**Max 2 retry attempts:** load_profile_with_recovery limits recursion to 2 attempts
- Rationale: Prevents infinite loop if wizard repeatedly produces invalid profiles (edge case)

**Two-mode loading:** load_profile (strict) vs load_profile_with_recovery (auto-fix)
- Rationale: --no-wizard mode uses strict loader for testing, normal mode uses recovery for user-friendly error handling

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_config.py to expect 4 KNOWN_KEYS**
- **Found during:** Task 2 verification (pytest run)
- **Issue:** test_known_keys_exact_size() expected 3 members but KNOWN_KEYS now has 4 (added profile_path)
- **Fix:** Changed assertion from `assert len(KNOWN_KEYS) == 3` to `assert len(KNOWN_KEYS) == 4`, updated docstring
- **Files modified:** tests/test_config.py
- **Verification:** All 104 tests pass
- **Committed in:** d64dbac (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test fix necessary for test suite to pass with new feature. No scope creep.

## Issues Encountered

None - plan executed smoothly. Circular import prevention strategy (local imports) worked as designed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 9 (Reporting Overhaul):**
- Profile path resolution complete - reports can assume profile is always loaded
- Wizard integration tested - first-run experience smooth
- Error recovery functional - corrupt profiles don't block users

**No blockers.**

**Note for future phases:**
- Profile path is now in config.json - reports can read it from there if needed
- load_profile_with_recovery available for robust profile loading in any module
- --validate-profile flag useful for testing profile changes without running full search

---
*Phase: 08-entry-point-integration*
*Completed: 2026-02-09*
