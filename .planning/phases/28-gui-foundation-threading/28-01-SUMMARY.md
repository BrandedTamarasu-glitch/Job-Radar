---
phase: 28-gui-foundation-threading
plan: 01
subsystem: ui
tags: [customtkinter, gui, desktop, threading]

# Dependency graph
requires:
  - phase: 27-cli-profile-management
    provides: profile_manager.py with load_profile/save_profile functions
  - phase: 03-config-profiledirs
    provides: paths.py with get_data_dir() for profile location detection
provides:
  - CustomTkinter GUI package (job_radar/gui/) with main window
  - Dual-mode entry point routing (CLI vs GUI auto-detection)
  - Welcome screen for first-time users
  - Profile summary display for returning users
  - PyInstaller configuration for both CLI and GUI executables
affects: [29-gui-profile-forms, 30-gui-search-integration]

# Tech tracking
tech-stack:
  added: [customtkinter]
  patterns:
    - "Dual-mode entry point: GUI when no args, CLI when args present"
    - "ImportError fallback: graceful degradation to CLI if GUI deps missing"
    - "Profile-aware routing: welcome screen vs main tabs based on profile existence"

key-files:
  created:
    - job_radar/gui/__init__.py
    - job_radar/gui/main_window.py
  modified:
    - job_radar/__main__.py
    - pyproject.toml
    - job-radar.spec

key-decisions:
  - "Dual-mode entry point uses len(sys.argv) > 1 to detect CLI mode - simple, reliable, no argparse overhead"
  - "ImportError fallback to CLI ensures graceful degradation when customtkinter not installed"
  - "Profile detection uses (get_data_dir() / profile.json).exists() to route welcome vs tabs view"
  - "Both CLI and GUI executables in single PyInstaller spec (console=True vs console=False)"

patterns-established:
  - "GUI routing pattern: check profile existence at init, route to welcome vs main tabs"
  - "Entry point pattern: _run_cli() and _run_gui() functions for clean separation"
  - "PyInstaller dual-exe pattern: shared Analysis/PYZ, separate EXE blocks, combined COLLECT"

# Metrics
duration: 15min
completed: 2026-02-12
---

# Phase 28 Plan 01: GUI Foundation & Threading Summary

**CustomTkinter GUI shell with dual-mode entry point, welcome screen, profile summary, and PyInstaller configuration for both CLI and GUI executables**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-12T23:10:10Z
- **Completed:** 2026-02-12T23:13:12Z
- **Tasks:** 2
- **Files created:** 2
- **Files modified:** 3

## Accomplishments

- Created GUI package with CustomTkinter main window (700x500, system theme, resizable)
- Implemented dual-mode entry point: GUI launches when no args, CLI when args present
- Welcome screen for first-time users with "Get Started" button (stub for Phase 29)
- Profile summary display in tabbed interface for returning users
- Updated PyInstaller spec to bundle CustomTkinter assets and create both CLI/GUI executables

## Task Commits

Each task was committed atomically:

1. **Task 1: Create GUI package with main window shell, welcome screen, and profile summary** - `e71576a` (feat)
2. **Task 2: Wire dual-mode entry point and update build configuration** - `58be3cc` (feat)

## Files Created/Modified

### Created
- `job_radar/gui/__init__.py` - GUI package marker with docstring
- `job_radar/gui/main_window.py` - MainWindow class with system theme, header, tabs, welcome screen, profile summary display, and launch_gui() entry point

### Modified
- `job_radar/__main__.py` - Dual-mode detection logic, extracted _run_cli() and added _run_gui() with ImportError fallback
- `pyproject.toml` - Added customtkinter dependency, added job_radar.gui to packages, added [project.gui-scripts] entry point
- `job-radar.spec` - Removed tkinter from excludes, added customtkinter hidden imports, added CustomTkinter assets bundling, added gui_exe EXE block (console=False)

## Decisions Made

1. **Dual-mode detection via len(sys.argv) > 1** - Simple and reliable. No argparse parsing overhead. Any CLI flag routes to existing CLI experience unchanged.

2. **ImportError fallback to CLI** - If customtkinter not installed (dev environment, partial install), GUI mode gracefully falls back to CLI with helpful error message. Ensures tool remains usable.

3. **Profile existence routing** - Main window checks (get_data_dir() / "profile.json").exists() at init and routes to welcome screen (first launch) or main tabs (returning user). Clean separation of first-time vs returning user experience.

4. **Separate EXE blocks in PyInstaller spec** - Single Analysis/PYZ shared between job-radar (console=True) and job-radar-gui (console=False). Both collected in same directory. Allows users to choose console-visible (CLI) or console-hidden (GUI) executable.

5. **CustomTkinter assets bundled conditionally** - try/except ImportError wrapper so spec file works even if customtkinter not installed at build time. Safe for CI/CD environments.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All tasks completed as specified.

## User Setup Required

None - no external service configuration required.

Users will need to install customtkinter dependency:
```bash
pip install customtkinter
```

This is already in pyproject.toml dependencies, so `pip install -e .` or `pip install job-radar` will handle it automatically.

## Next Phase Readiness

**Ready for Phase 28 Plan 02 (Threading infrastructure):**
- GUI shell established with working window and routing
- Entry point detection working (verified with --help test)
- Search tab placeholder ready for threading integration

**Ready for Phase 29 (Profile forms):**
- Welcome screen "Get Started" button ready to wire to profile wizard form
- Profile tab structure ready for edit button and form overlay

**Blockers:** None

## Self-Check: PASSED

**Verified created files exist:**
```
FOUND: job_radar/gui/__init__.py
FOUND: job_radar/gui/main_window.py
```

**Verified commits exist:**
```
FOUND: e71576a
FOUND: 58be3cc
```

**Verified key integrations:**
- CLI mode works: `python -m job_radar --help` prints help without launching GUI ✓
- GUI package imports: `import job_radar.gui` succeeds ✓
- Dependencies configured: customtkinter in pyproject.toml ✓
- PyInstaller spec updated: tkinter not excluded, customtkinter in hidden imports ✓

---
*Phase: 28-gui-foundation-threading*
*Plan: 01*
*Completed: 2026-02-12*
