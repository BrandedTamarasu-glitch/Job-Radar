---
phase: 36-gui-uninstall-feature
plan: 01
subsystem: gui-backend
status: complete
completed: 2026-02-14
duration: 225
wave: 1

# Dependencies
requires:
  - Phase 20 (GUI foundation)
  - job_radar.paths (directory resolution)
  - job_radar.rate_limits (_cleanup_connections)

provides:
  - Core uninstaller backend logic
  - Backup creation (ZIP of profile.json, config.json)
  - Best-effort data deletion with error collection
  - Platform-specific cleanup script generation (macOS/Windows/Linux)
  - Path enumeration for preview UI

affects:
  - Phase 36 Plan 02 (GUI dialogs will call these functions)

# Technical Details
tech-stack:
  added:
    - zipfile (stdlib, ZIP_DEFLATED compression)
    - subprocess.Popen (background cleanup scripts)
  patterns:
    - Best-effort deletion with onerror callback (Python 3.10+ compat)
    - Platform detection via sys.platform for cleanup scripts
    - macOS .app bundle resolution for Trash operations
    - SQLite connection cleanup before file deletion

key-files:
  created:
    - job_radar/uninstaller.py (257 lines, 5 exported functions)
    - tests/test_uninstaller.py (430 lines, 19 unit tests)

decisions:
  - use-shutil-onerror-for-py310-compat:
      context: "Python 3.12+ uses onexc parameter for rmtree, but we support 3.10+"
      decision: "Use onerror parameter (deprecated but still works in 3.12+)"
      rationale: "Maintains compatibility with Python 3.10-3.14 without version detection"
      alternatives: ["Version detection + conditional parameter", "Drop 3.10 support"]
      impact: "Backward compatible, no runtime version checks needed"

  - macos-app-bundle-resolution:
      context: "PyInstaller creates .app bundles on macOS, binary is deep inside"
      decision: "Walk up path to find .app directory, move entire bundle to Trash"
      rationale: "Moving just the binary leaves orphaned .app bundle structure"
      alternatives: ["Delete binary only", "Use shutil.rmtree on .app"]
      impact: "Clean uninstall on macOS, uses Finder API for Trash (respects user workflow)"

  - best-effort-deletion-vs-fail-fast:
      context: "Some files may be locked/permission-denied during uninstall"
      decision: "Continue deletion, collect all failures, return list at end"
      rationale: "Partial uninstall better than no uninstall; user sees what failed"
      alternatives: ["Stop at first error", "Ignore all errors"]
      impact: "Maximizes cleanup success, provides transparency via failure list"

  - cleanup-connections-before-deletion:
      context: "SQLite rate limiter DBs may be locked if connections open"
      decision: "Call _cleanup_connections() before shutil.rmtree()"
      rationale: "Prevents 'database is locked' errors during deletion"
      alternatives: ["Ignore locked files", "Wait with timeout"]
      impact: "Clean deletion of .rate_limits/ directory, no orphaned SQLite files"

tags: [gui, uninstaller, backup, cleanup, cross-platform, sqlite, pyinstaller]
---

# Phase 36 Plan 01: Core Uninstaller Module Summary

**One-liner:** Platform-aware uninstaller backend with ZIP backup, best-effort deletion, and background cleanup scripts for frozen binaries

## Objective

Create the core uninstaller module with backup, deletion, path enumeration, and platform-specific cleanup script generation. Provides testable backend logic that GUI dialogs will call.

## What Was Built

### Core Functions (job_radar/uninstaller.py)

**1. get_uninstall_paths() → list[tuple[str, str]]**
- Enumerates all app data paths with human-readable descriptions
- Checks: profile.json, config.json, backups/, .rate_limits/, cache/, log file
- Returns only paths that exist on disk (no phantom entries)
- Example output: `("/path/to/profile.json", "profile.json - Your search preferences")`

**2. create_backup(save_path: str) → None**
- Creates ZIP at save_path with profile.json and config.json
- Uses ZIP_DEFLATED compression
- Stores files at ZIP root (no nested directories)
- Skips missing files gracefully (doesn't error if profile.json missing)
- Raises on write failure (caller handles error presentation)

**3. delete_app_data() → list[tuple[str, str]]**
- Calls `_cleanup_connections()` first to close SQLite rate limiter connections
- Deletes entire data directory via `shutil.rmtree` with onerror callback
- Deletes log file (`~/job-radar-error.log`)
- Best-effort: continues on failure, collects errors
- Returns list of (path, error_msg) tuples (empty = success)

**4. get_binary_path() → Path | None**
- Returns `Path(sys.executable)` if frozen (PyInstaller bundle)
- Returns None in dev mode
- Used by GUI to determine if binary cleanup needed

**5. create_cleanup_script(binary_path: Path) → tuple[str, str | None]**
- Generates platform-specific script to delete binary after app exits
- Returns (message, script_path_or_none)

Platform behaviors:
- **macOS:** Resolves to .app bundle, creates shell script with osascript to move to Trash
- **Windows:** Creates .bat with timeout + del, runs with CREATE_NO_WINDOW flag
- **Linux:** Creates shell script with sleep + rm -f, self-deletes
- **All:** Executes in background via subprocess.Popen(start_new_session=True)
- **Failure:** Returns manual instruction message with path, None for script

### Test Coverage (tests/test_uninstaller.py)

**19 unit tests covering:**
- Path enumeration (existing files, empty dirs, backups/cache, descriptions)
- Backup creation (valid ZIP, contents verification, missing files, invalid paths, empty dir)
- Deletion (directory + log removal, failure collection, cleanup call order)
- Binary path detection (frozen vs dev mode)
- Cleanup scripts (macOS/Windows/Linux script generation, failure handling)

All tests use tmp_path fixtures and monkeypatching to isolate behavior.

## Key Decisions Made

**1. Python 3.10+ compatibility for shutil.rmtree**
- Used `onerror` parameter (not `onexc`) for deletion error handling
- Python 3.12+ deprecates onerror but still supports it
- Avoids version detection code while supporting Python 3.10-3.14

**2. macOS .app bundle handling**
- Walks path upward to find `.app` directory when inside PyInstaller bundle
- Moves entire .app to Trash (not just binary) for clean removal
- Uses osascript + Finder API to respect user Trash workflow

**3. Best-effort deletion strategy**
- Continues deletion even when individual files fail
- Collects all failures in list with error messages
- User sees what succeeded vs what needs manual cleanup
- Better UX than all-or-nothing failure

**4. SQLite connection cleanup integration**
- Calls `rate_limits._cleanup_connections()` before file deletion
- Prevents "database is locked" errors on .rate_limits/ directory
- Critical for clean uninstall when rate limiters have been used

## Testing Results

```
============================= 562 passed in 15.29s =============================
```

- 19 new tests for uninstaller module (100% pass rate)
- 0 regressions in existing 543 tests
- All verification criteria met

## Task Breakdown

| Task | Description | Commit | Files | Lines |
|------|-------------|--------|-------|-------|
| 1 | Create uninstaller.py with 5 core functions | 4ca86a2 | job_radar/uninstaller.py | 257 |
| 2 | Add comprehensive unit tests | 3a76c02 | tests/test_uninstaller.py | 430 |

**Total:** 2 tasks, 2 files created, 687 lines

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Blockers:** None

**Concerns:** None

**Ready for:** Phase 36 Plan 02 (GUI uninstall dialogs)

The GUI can now call these functions to:
1. Preview paths with `get_uninstall_paths()`
2. Offer backup with `create_backup()`
3. Delete data with `delete_app_data()`
4. Clean up binary with `get_binary_path()` + `create_cleanup_script()`

All edge cases handled (missing files, locked files, platform differences, dev vs frozen).

## Files Changed

**Created:**
- `job_radar/uninstaller.py` - Core uninstaller backend (5 functions)
- `tests/test_uninstaller.py` - Unit tests (19 tests)

**Modified:** None

**Dependencies Added:** None (all stdlib)

## Verification Commands

```bash
# Import check
python -c "from job_radar.uninstaller import get_uninstall_paths, create_backup, delete_app_data, get_binary_path, create_cleanup_script"

# Unit tests
pytest tests/test_uninstaller.py -v

# Full suite (verify no regressions)
pytest tests/ -v
```

## Metrics

- **Duration:** 225 seconds (~3.75 minutes)
- **Test count:** 19 new tests
- **Code added:** 687 lines
- **Functions exported:** 5
- **Platforms supported:** macOS, Windows, Linux
