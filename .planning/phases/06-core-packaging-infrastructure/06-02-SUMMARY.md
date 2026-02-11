---
phase: 06-core-packaging-infrastructure
plan: 02
subsystem: infra
tags: [pyinstaller, packaging, distribution, executable, macos, windows, linux]

# Dependency graph
requires:
  - phase: 06-01
    provides: Runtime infrastructure (paths.py, banner.py) for frozen builds
provides:
  - PyInstaller .spec file with onedir configuration
  - Updated entry point with SSL fix, banner, and error handling
  - Build scripts for all three platforms (macOS, Windows, Linux)
  - End-user README with installation and troubleshooting
  - Working standalone executables that bundle all dependencies
affects: [07-setup-wizard, 08-config-profiles, 11-distribution]

# Tech tracking
tech-stack:
  added: [pyinstaller]
  patterns:
    - "onedir mode with console=True for transparency"
    - "UPX disabled to reduce antivirus false positives"
    - "Hidden imports declared explicitly for all transitive dependencies"
    - "Platform-conditional macOS .app bundle generation"
    - "SSL certificate fix for frozen HTTPS requests"

key-files:
  created:
    - job-radar.spec
    - scripts/build.sh
    - scripts/build.bat
    - README-dist.txt
  modified:
    - job_radar/__main__.py

key-decisions:
  - "Use onedir mode (exclude_binaries=True) instead of onefile for faster startup"
  - "Disable UPX compression to avoid antivirus false positives"
  - "Pre-declare questionary/prompt_toolkit hidden imports for Phase 7 to avoid rebuild"
  - "Bundle profiles/_template.json so frozen app has starter profile"
  - "SSL fix runs before any imports to ensure HTTPS works in frozen mode"
  - "Banner displays on launch, errors log to ~/job-radar-error.log"

patterns-established:
  - "Entry point pattern: SSL fix → banner → main logic → error handling"
  - "Build script pattern: clean → install deps → build → add README → create archive"
  - "Platform-specific archive formats: ZIP (macOS), tar.gz (Linux), ZIP (Windows)"

# Metrics
duration: 3min
completed: 2026-02-09
---

# Phase 06 Plan 02: PyInstaller Configuration and Build Scripts Summary

**Working standalone executables with onedir PyInstaller builds, SSL certificate fix, startup banner, and cross-platform build scripts**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-09T19:20:59Z
- **Completed:** 2026-02-09T19:23:35Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- PyInstaller builds successfully producing dist/job-radar/ with all dependencies bundled
- Executable launches without Python installed, displays banner, responds to --help and --version
- SSL certificate fix ensures HTTPS requests work in frozen mode
- Build scripts automate compilation and distribution packaging for all platforms
- macOS .app bundle created with dock visibility

## Task Commits

Each task was committed atomically:

1. **Task 1: Update entry point and create .spec file** - `15ff8c6` (feat)
2. **Task 2: Create build scripts, README.txt, and run first build** - `c2bdf0b` (feat)

## Files Created/Modified
- `job_radar/__main__.py` - Entry point with SSL fix, banner display, error handling, KeyboardInterrupt catch
- `job-radar.spec` - PyInstaller spec file with onedir config, hidden imports, profile template bundling
- `scripts/build.sh` - macOS/Linux build script with archive packaging
- `scripts/build.bat` - Windows build script with ZIP creation
- `README-dist.txt` - End-user installation, requirements, and troubleshooting documentation

## Decisions Made
- **onedir mode**: Chose exclude_binaries=True (onedir) over onefile for faster startup time per PKG-04 requirements
- **UPX disabled**: Disabled UPX compression to reduce antivirus false positive rates based on research recommendations
- **Pre-declared Phase 7 imports**: Added questionary/prompt_toolkit to hidden imports now to avoid rebuild in Phase 7
- **SSL fix placement**: SSL certificate fix runs before any imports to ensure HTTPS works in frozen mode (critical for job source fetching)
- **README location**: Created README-dist.txt in project root (not dist/) so it's tracked in git and copied by build scripts

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Build completed successfully on first attempt. Executable tested with --help, --version, and --dry-run - all work correctly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Standalone executables working on macOS (tested)
- Build scripts ready for Windows and Linux (untested but follow standard patterns)
- Phase 7 (Setup Wizard) can now proceed - questionary/prompt_toolkit already declared in hidden imports
- Phase 11 (Distribution) has working build artifacts (dist/job-radar/, archives)

**Blockers:**
- Windows and Linux builds untested (will test when those platforms are available)
- Code signing deferred until v1.1 user feedback (macOS Gatekeeper and Windows SmartScreen warnings expected)

**Concerns:**
- Antivirus false positives possible on Windows - README-dist.txt documents workaround
- macOS Gatekeeper will block unsigned .app - README-dist.txt documents right-click workaround

---
*Phase: 06-core-packaging-infrastructure*
*Completed: 2026-02-09*
