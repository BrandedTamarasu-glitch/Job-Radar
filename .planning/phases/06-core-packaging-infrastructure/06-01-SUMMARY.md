---
phase: 06-core-packaging-infrastructure
plan: 01
subsystem: infra
tags: [pyinstaller, platformdirs, pyfiglet, pathlib, frozen-mode]

# Dependency graph
requires:
  - phase: 05-test-coverage-completion
    provides: Complete test suite (84 tests) for regression safety
provides:
  - Runtime infrastructure for dev/frozen mode execution
  - Platform-appropriate data directory management
  - ASCII banner display with graceful fallback
  - Error logging to ~/job-radar-error.log
  - Backward-compatible config path migration
affects: [06-02, 06-03, packaging, executable-distribution]

# Tech tracking
tech-stack:
  added: [platformdirs>=4.0, pyfiglet, colorama, certifi]
  patterns: [pathlib-exclusive path handling, lazy imports for graceful degradation, sys._MEIPASS frozen mode detection]

key-files:
  created: [job_radar/paths.py, job_radar/banner.py, tests/test_paths.py]
  modified: [job_radar/config.py, pyproject.toml, job_radar/__init__.py, tests/test_config.py]

key-decisions:
  - "Use platformdirs for platform-appropriate data directories instead of hardcoded ~/.job-radar"
  - "Lazy import pyfiglet inside display_banner() for graceful degradation"
  - "Add legacy config path fallback for v1.0 backward compatibility"
  - "Use pathlib exclusively (no os.sep) per PyInstaller best practices"

patterns-established:
  - "is_frozen() pattern: getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')"
  - "Resource path resolution: sys._MEIPASS in frozen mode, Path(__file__).parent in dev"
  - "Config migration: check new platform path first, fall back to legacy path if missing"

# Metrics
duration: 2min
completed: 2026-02-09
---

# Phase 6 Plan 1: Runtime Infrastructure Setup Summary

**Platform-aware path resolution with dev/frozen mode support, ASCII banner, and backward-compatible config migration to platformdirs**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-09T16:23:30Z
- **Completed:** 2026-02-09T16:25:43Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Created paths.py with resource path resolution for both development and PyInstaller frozen modes
- Created banner.py with ASCII art startup banner (pyfiglet) and error logging
- Migrated config.py to use platform-appropriate data directories (platformdirs)
- Added backward compatibility for v1.0 users (legacy ~/.job-radar/config.json fallback)
- Bumped version to 1.1.0 across project
- Added 6 new tests for path resolution (84 total tests passing)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create paths.py and banner.py modules** - `8bc4420` (feat)
2. **Task 2: Update dependencies and config.py for platformdirs** - `3fb211e` (feat)

## Files Created/Modified
- `job_radar/paths.py` - Resource path resolution with is_frozen(), get_resource_path(), get_data_dir(), get_log_file()
- `job_radar/banner.py` - Startup banner display and error logging with graceful degradation
- `job_radar/config.py` - Updated to use platform data directories with legacy fallback
- `pyproject.toml` - Version bump to 1.1.0, added platformdirs, pyfiglet, colorama, certifi
- `job_radar/__init__.py` - Version bump to 1.1.0
- `tests/test_paths.py` - 6 tests for path resolution in dev/frozen modes
- `tests/test_config.py` - Fixed import (DEFAULT_CONFIG_PATH → LEGACY_CONFIG_PATH)

## Decisions Made

**Platform directory strategy:**
- Use platformdirs for platform-appropriate paths (Windows: %APPDATA%\JobRadar, macOS: ~/Library/Application Support/JobRadar, Linux: ~/.local/share/JobRadar)
- Keep legacy ~/.job-radar/config.json fallback for v1.0 backward compatibility
- This ensures existing users' configs migrate seamlessly

**Graceful degradation pattern:**
- pyfiglet imported inside display_banner() function, not at module level
- Falls back to simple "===" banner if pyfiglet unavailable or fails
- Ensures executable works even if pyfiglet bundling fails

**Path resolution best practices:**
- Use pathlib exclusively throughout (no os.sep or string concatenation)
- Follows PyInstaller research recommendations for cross-platform reliability
- get_data_dir() creates directory on access (mkdir parents=True, exist_ok=True)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed broken test imports after config.py refactoring**
- **Found during:** Task 2 (running pytest after config.py changes)
- **Issue:** test_config.py tried to import DEFAULT_CONFIG_PATH which was renamed to LEGACY_CONFIG_PATH
- **Fix:** Updated import and all references in test_config.py from DEFAULT_CONFIG_PATH to LEGACY_CONFIG_PATH
- **Files modified:** tests/test_config.py
- **Verification:** All 84 tests pass
- **Committed in:** 3fb211e (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix to maintain test coverage. No scope creep.

## Issues Encountered

**Python environment setup:**
- System Python is externally managed (macOS Homebrew)
- Found existing .venv in project and used it successfully
- All dependencies installed via .venv/bin/pip

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 6 Plan 2 (PyInstaller configuration):**
- paths.py provides get_resource_path() for bundled resources
- is_frozen() check ready for conditional PyInstaller behavior
- All 84 tests passing (78 existing + 6 new)
- New dependencies installed and tested

**Validation complete:**
- ✓ Resource path resolution works in dev mode
- ✓ Platform data directories created on access
- ✓ ASCII banner displays with pyfiglet
- ✓ Config migration with legacy fallback tested
- ✓ CLI backward compatibility verified (--help works)
- ✓ All tests pass

**Known concerns for packaging:**
- Hidden imports: platformdirs, pyfiglet need explicit PyInstaller hooks (addressed in Plan 2)
- Frozen mode tested via mocks only - real frozen testing in Plan 3

---
*Phase: 06-core-packaging-infrastructure*
*Completed: 2026-02-09*
