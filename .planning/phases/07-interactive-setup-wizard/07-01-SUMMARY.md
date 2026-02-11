---
phase: 07-interactive-setup-wizard
plan: 01
subsystem: ui
tags: [questionary, prompt_toolkit, cli, wizard, first-run]

# Dependency graph
requires:
  - phase: 06-core-packaging-infrastructure
    provides: platformdirs data paths via get_data_dir()
  - phase: 02-config-file-support
    provides: config.json structure and KNOWN_KEYS
provides:
  - Interactive setup wizard with sequential prompts and validation
  - Mid-wizard back navigation via /back command
  - Post-summary field editing via select menu
  - Atomic JSON file writing helper
  - is_first_run() check for first-time users
affects: [08-cli-entrypoint-wiring, phase-8, phase-9]

# Tech tracking
tech-stack:
  added: [questionary, prompt_toolkit, wcwidth]
  patterns: [atomic-json-writes, sequential-wizard-flow, manual-state-management-for-back-nav]

key-files:
  created: [job_radar/wizard.py]
  modified: [pyproject.toml]

key-decisions:
  - "Use /back text command instead of keybindings for cross-platform compatibility"
  - "No default values on profile fields (name, titles, skills, location, dealbreakers)"
  - "Score defaults to 2.8 per WIZ-08 research decision"
  - "Post-summary editing via select menu as ADDITIONAL option beyond mid-wizard /back"
  - "Atomic file writes with temp file + os.replace() to prevent corruption"

patterns-established:
  - "Atomic JSON writes: tempfile.mkstemp() + os.fsync() + Path.replace()"
  - "Sequential wizard with manual state management: while loop + index-based navigation"
  - "Questionary validation: custom Validator subclasses with inline error messages"
  - "Cross-platform emoji usage: section headers only, not critical UI elements"

# Metrics
duration: 2min
completed: 2026-02-09
---

# Phase 7 Plan 01: Interactive Setup Wizard Summary

**Complete first-run wizard with questionary: sequential prompts, /back navigation, field editing, atomic JSON writes to platformdirs**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-09T20:26:03Z
- **Completed:** 2026-02-09T20:28:18Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Interactive wizard collects profile (name, titles, skills, location, dealbreakers) and preferences (min_score, new_only)
- Mid-wizard back navigation via /back command enables correction without restart
- Post-summary field editing via select menu for final review
- Atomic JSON file writing prevents corruption on crash/interrupt
- Profile and config JSON structures match existing scoring.py and config.py expectations

## Task Commits

Each task was committed atomically:

1. **Task 1: Create wizard module with prompts, validators, back navigation, and file output** - `8d9579b` (feat)

## Files Created/Modified
- `job_radar/wizard.py` - Complete setup wizard with run_setup_wizard(), is_first_run(), three validators, atomic JSON writing
- `pyproject.toml` - Added questionary dependency

## Decisions Made

**1. Back navigation via /back text command**
- Questionary doesn't support custom keybindings natively without prompt_toolkit extensions
- Typing "/back" (case-insensitive) is cross-platform compatible and simple to implement
- Users get hint at wizard start: "Tip: Type /back at any prompt to return to the previous question"
- Tradeoff: Slightly clunky UX vs guaranteed cross-platform compatibility (Windows cmd, PowerShell, macOS Terminal, Linux terminals)

**2. No default values on profile fields**
- Per CONTEXT.md decision WIZ-04: "No default values - all fields start empty, user must provide everything"
- Forces conscious choices instead of accepting defaults blindly
- Optional fields (location, dealbreakers) accept empty input (press Enter to skip) - this is NOT a default, it's accepting empty
- Score gets default="2.8" per WIZ-08 because it's a preference with sensible starting point
- new_only gets default=True as a preference starting state

**3. Post-summary editing as ADDITIONAL to mid-wizard back**
- Per CONTEXT.md: "Back button navigation - user can press a key to go back and change previous answers"
- Also implemented post-summary editing: after seeing celebration summary, user can select "Edit a field" to change any answer
- TWO editing flows: mid-wizard /back for immediate corrections, post-summary for final review
- This exceeds plan requirements but provides better UX

**4. Atomic file writes for reliability**
- Direct json.dump() can corrupt files on crash (power loss, kill -9, Ctrl+C)
- Pattern: tempfile.mkstemp() in same directory + json.dump() + os.fsync() + Path.replace()
- Atomic rename (os.replace) ensures either old file exists or new file exists, never partial write
- Critical for profile.json - if corrupted, app can't launch

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - questionary integration straightforward, all validators worked as expected, atomic file writing pattern proven.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Phase 8 (CLI entrypoint wiring):
- run_setup_wizard() function returns bool (True=saved, False=cancelled)
- is_first_run() checks for profile.json existence
- Wizard writes profile.json and config.json to platformdirs data directory
- Plan 08-02 will integrate wizard into main() with first-run check

No blockers or concerns.

---
*Phase: 07-interactive-setup-wizard*
*Completed: 2026-02-09*
