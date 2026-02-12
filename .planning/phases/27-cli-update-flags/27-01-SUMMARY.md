---
phase: 27-cli-update-flags
plan: 01
subsystem: cli
tags: [argparse, cli-flags, validators, profile-update, config-update]

# Dependency graph
requires:
  - phase: 24-profile-infrastructure
    provides: "save_profile(), load_profile(), validate_profile(), _write_json_atomic(), ProfileValidationError"
provides:
  - "Three CLI update flags: --update-skills, --set-min-score, --set-titles"
  - "Custom argparse type validators: comma_separated_skills, comma_separated_titles, valid_score_range"
  - "Handler functions: handle_update_skills, handle_set_min_score, handle_set_titles"
  - "Path resolution helpers: _resolve_profile_path, _resolve_config_path"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [argparse-type-validators, mutually-exclusive-update-group, manual-cross-group-exclusion]

key-files:
  created:
    - tests/test_cli_update_flags.py
  modified:
    - job_radar/search.py

key-decisions:
  - "Handlers return on success, sys.exit(1) only on errors -- main() calls sys.exit(0) after handler"
  - "Update flags use argparse mutually exclusive group; cross-group exclusion with --view/edit-profile is manual check in main()"
  - "handle_set_min_score takes config_arg (--config flag value), not config dict, for path resolution consistency"
  - "Titles cannot be cleared with empty string (validation requires non-empty target_titles)"

patterns-established:
  - "argparse type validators: parse + validate at parse time, raise ArgumentTypeError with friendly messages"
  - "CLI update handler pattern: resolve path -> check exists -> load -> store old -> update -> save -> print diff"
  - "Manual mutual exclusion: check in main() when argparse groups can't express the constraint"

# Metrics
duration: 6min
completed: 2026-02-12
---

# Phase 27 Plan 01: CLI Update Flags Summary

**Three CLI update flags (--update-skills, --set-min-score, --set-titles) with custom argparse validators, diff output, and mutually exclusive groups**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-12T19:34:50Z
- **Completed:** 2026-02-12T19:40:50Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added three custom argparse type validators (comma_separated_skills, comma_separated_titles, valid_score_range) with friendly error messages
- Added three handler functions with profile/config path resolution, old/new diff display, and validation error handling
- Wired mutually exclusive update group in parse_args() and manual cross-group exclusion with --view/edit-profile in main()
- Created comprehensive test suite (40 tests, 487 lines) covering validators, handlers, parsing, mutual exclusion, and integration
- Updated epilog with Quick Updates section replacing "(coming soon)" placeholder

## Task Commits

Each task was committed atomically:

1. **Task 1: Add CLI update flags with validators and handlers** - `a40b635` (feat)
2. **Task 2: Add comprehensive tests for CLI update flags** - `dfbae8b` (test)

## Files Created/Modified
- `job_radar/search.py` - Added validators (comma_separated_skills, comma_separated_titles, valid_score_range), handlers (handle_update_skills, handle_set_min_score, handle_set_titles), path helpers (_resolve_profile_path, _resolve_config_path), mutually exclusive group, and early exit wiring
- `tests/test_cli_update_flags.py` - 40 tests across 5 categories: validators (18), handlers (11), flag parsing (4), mutual exclusion (4), integration (3)

## Decisions Made
- Handlers return on success rather than calling sys.exit(0) -- the exit is in main() after the handler call, keeping handlers testable without catching SystemExit on success
- handle_set_min_score takes the raw --config flag value (string or None) for path resolution, not the loaded config dict -- consistent with how handlers resolve paths
- Titles cannot be cleared with empty string, unlike skills -- validate_profile requires non-empty target_titles, so the validator rejects "" upfront
- argparse type validators exit with code 2 (argparse standard) on parse-time validation errors; handler runtime errors use exit code 1

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All Phase 27 functionality delivered in this single plan
- CLI update flags are fully functional and tested
- Full test suite passes: 452 tests (412 existing + 40 new), zero failures
- v1.5.0 milestone profile management features are complete

## Self-Check: PASSED

- [x] job_radar/search.py exists with validators, handlers, and flag wiring
- [x] tests/test_cli_update_flags.py exists (487 lines, >= 150 min)
- [x] Commit a40b635 exists (Task 1)
- [x] Commit dfbae8b exists (Task 2)
- [x] All 6 verification steps passed
- [x] Full test suite: 452 tests passed, zero failures

---
*Phase: 27-cli-update-flags*
*Completed: 2026-02-12*
