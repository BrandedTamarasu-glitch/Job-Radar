---
phase: 07-interactive-setup-wizard
plan: 02
subsystem: testing
tags: [pytest, pytest-mock, wizard-tests, entry-point, first-run]

# Dependency graph
requires:
  - phase: 07-01
    provides: wizard module with run_setup_wizard() and is_first_run()
  - phase: 06-02
    provides: PyInstaller spec with questionary hidden imports
provides:
  - Comprehensive wizard test suite with 20 test cases
  - Mocked questionary prompts for CI-friendly testing
  - First-run wizard integration in __main__.py entry point
  - Graceful fallback handling for missing questionary or wizard failures
affects: [08-cli-entrypoint-wiring, phase-8]

# Tech tracking
tech-stack:
  added: [pytest-mock]
  patterns: [mock-questionary-prompts, sequential-mock-answers, side-effect-functions]

key-files:
  created: [tests/test_wizard.py]
  modified: [job_radar/__main__.py]

key-decisions:
  - "Patch job_radar.paths.get_data_dir instead of wizard.get_data_dir (import target)"
  - "Use side_effect functions with *args, **kwargs to accept questionary call signatures"
  - "ImportError catch for missing questionary enables dev mode without extras"
  - "Generic Exception catch for wizard failures ensures --profile flag still works"
  - "Welcome message in __main__.py, wizard module owns only interactive prompts"

patterns-established:
  - "Mock questionary pattern: side_effect function returns Mock with .ask() method"
  - "Sequential answers: pop from list in side_effect, return None when empty"
  - "First-run flow: SSL fix -> banner -> first-run check -> wizard -> search"

# Metrics
duration: 3min
completed: 2026-02-09
---

# Phase 7 Plan 02: Wizard Tests and Entry Point Integration Summary

**Comprehensive wizard testing with mocked prompts and first-run detection wired into application entry point**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-09T20:30:50Z
- **Completed:** 2026-02-09T20:34:07Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- 20 comprehensive wizard tests covering all validators, flows, and edge cases
- All tests use pytest-mock to avoid interactive prompts (CI-friendly)
- First-run detection triggers wizard before search in __main__.py
- Graceful fallback handling for missing questionary or wizard crashes
- Wizard failure is non-critical - user can still use --profile flag

## Task Commits

Each task was committed atomically:

1. **Task 1: Create wizard test suite with mocked questionary prompts** - `96c6679` (test)
2. **Task 2: Wire wizard into __main__.py entry point with first-run detection** - `6813e6f` (feat)

## Files Created/Modified
- `tests/test_wizard.py` - 20 test cases: validators (6), first-run detection (2), atomic writes (2), wizard flows (10)
- `job_radar/__main__.py` - First-run check triggers wizard between banner and search

## Decisions Made

**1. Patch import target, not local reference**
- Issue: wizard.py imports get_data_dir() inside functions, not at module level
- Solution: Patch `job_radar.paths.get_data_dir` (where it's defined) instead of `job_radar.wizard.get_data_dir` (doesn't exist)
- This is standard pytest mocking practice - patch where the function is imported from, not where it's used

**2. Side effect functions must accept positional arguments**
- Issue: questionary.text("message", ...) passes positional args to side_effect function
- Solution: Define side_effect functions with `*args, **kwargs` instead of just `**kwargs`
- Matches how unittest.mock calls side_effect functions

**3. Install pytest-mock for mocker fixture**
- pytest-mock not in base pytest, needed for `mocker.patch()` fixture
- Added to dev environment (not pyproject.toml dependencies - dev-only)
- Alternative would be unittest.mock.patch decorator, but mocker fixture is cleaner

**4. ImportError catch enables dev mode without extras**
- Questionary might not be installed in dev environments that didn't `pip install questionary`
- Wizard is nice-to-have for first run, not a blocker for development
- Developers can still use --profile flag to point at manually created profile

**5. Generic Exception catch for wizard failures**
- If wizard crashes for any reason, app still works via --profile flag
- Don't let a wizard bug block the entire application
- Wizard is a convenience feature, not a critical path

## Deviations from Plan

### Auto-added Issues

**[Rule 2 - Missing Critical] Install pytest-mock for mocker fixture**
- **Found during:** Task 1 testing
- **Issue:** pytest doesn't include pytest-mock by default, `mocker` fixture not available
- **Fix:** Ran `pip install pytest-mock` in venv
- **Files modified:** .venv (not tracked in git)
- **Commit:** Not applicable (dev environment change)

No other deviations - plan executed as written.

## Issues Encountered

**Mock patching strategy required adjustment**
- Initial patches targeted `job_radar.wizard.get_data_dir` (doesn't exist)
- Corrected to `job_radar.paths.get_data_dir` (actual import source)
- Side effect functions needed `*args` in addition to `**kwargs`
- Resolved quickly once pattern understood

All tests pass, no regressions.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Phase 8 (CLI Entrypoint Wiring):
- Wizard tests ensure wizard works without manual interaction
- First-run detection functional in __main__.py
- Wizard triggered on first launch (no profile.json)
- Repeat launches skip wizard (profile.json exists)
- Phase 8 will make --profile optional when wizard creates profile.json

Currently: wizard creates profile.json, but search.py still requires --profile flag.
Phase 8: search.py will auto-detect wizard-created profile.json and use it.

No blockers or concerns.

---
*Phase: 07-interactive-setup-wizard*
*Completed: 2026-02-09*
