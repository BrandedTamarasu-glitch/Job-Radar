---
phase: 25-profile-preview
plan: 02
subsystem: cli
tags: [argparse, profile-preview, cli-integration, view-profile]

# Dependency graph
requires:
  - phase: 25-profile-preview
    plan: 01
    provides: "display_profile() function in profile_display.py"
  - phase: 24-profile-infrastructure
    provides: "profile_manager.py with load/save/validate, _Colors class in search.py"
provides:
  - "--view-profile CLI flag for standalone profile display with edit prompt"
  - "Startup profile preview in main() flow (suppressed by --no-wizard)"
  - "16 tests covering display module and CLI integration"
affects: [26-interactive-quick-edit]

# Tech tracking
tech-stack:
  added: []
  patterns: [early-exit-handler-pattern, startup-preview-pattern]

key-files:
  created: [tests/test_profile_display.py]
  modified: [job_radar/search.py]

key-decisions:
  - "Reuse --no-wizard flag for both wizard suppression and profile preview suppression (one flag for quiet mode)"
  - "Use input() for edit prompt instead of questionary (simple y/N, no library needed)"

patterns-established:
  - "Early exit handler pattern: resolve profile path, load, display, exit -- before main search flow"
  - "Startup preview pattern: display profile after load, before search banner, gated by --no-wizard"

# Metrics
duration: 3min
completed: 2026-02-12
---

# Phase 25 Plan 02: CLI Integration Summary

**--view-profile flag with standalone display/edit prompt and startup preview wired into search.py main flow, with 16 tests**

## Performance

- **Duration:** 3 min (206s)
- **Started:** 2026-02-12T17:54:46Z
- **Completed:** 2026-02-12T17:58:12Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added --view-profile flag to CLI with standalone display, wizard launch for missing profiles, and "Want to edit? (y/N)" prompt
- Integrated startup profile preview into main() after profile load, suppressed by --no-wizard flag
- Updated help text: description mentions --view-profile, epilog has profile management section with examples
- Updated --no-wizard help text to mention profile preview suppression
- Created 16 tests covering display output, field filtering, NO_COLOR compliance, and CLI integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Add --view-profile flag and integrate preview into main()** - `5917405` (feat)
2. **Task 2: Create tests for profile_display module and CLI integration** - `72d4a4c` (test)

## Files Created/Modified
- `job_radar/search.py` - Added --view-profile flag, startup preview, updated help text and epilog
- `tests/test_profile_display.py` - New test file with 16 tests covering display and CLI integration

## Decisions Made
- Reuse --no-wizard flag for both wizard suppression and profile preview suppression -- keeps one flag for "quiet mode" operation
- Use plain input() for the "Want to edit?" prompt rather than questionary -- simple y/N confirmation doesn't need a full interactive library

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 5 VIEW requirements implemented (VIEW-01 through VIEW-05)
- Phase 25 (Profile Preview) is complete -- both plans delivered
- --view-profile "Want to edit?" prompt returns placeholder message; Phase 26 (Interactive Quick-Edit) will implement actual editing
- No blockers for Phase 26

## Self-Check: PASSED

- FOUND: job_radar/search.py
- FOUND: tests/test_profile_display.py
- FOUND: 25-02-SUMMARY.md
- FOUND: 5917405 (Task 1 commit)
- FOUND: 72d4a4c (Task 2 commit)

---
*Phase: 25-profile-preview*
*Completed: 2026-02-12*
