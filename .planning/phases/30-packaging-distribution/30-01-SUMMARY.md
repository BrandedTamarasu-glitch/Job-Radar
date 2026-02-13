---
phase: 30-packaging-distribution
plan: 01
subsystem: infra
tags: [pyinstaller, macos, code-signing, ci-cd, github-actions, entitlements]

# Dependency graph
requires:
  - phase: 28-gui-foundation-threading
    provides: "GUI executable (job-radar-gui) and CustomTkinter bundling configuration"
provides:
  - "macOS code signing entitlements for Python JIT memory allocation"
  - "PyInstaller spec configured with entitlements for CLI and GUI executables"
  - "CI smoke tests verifying executable functionality after build"
  - "macOS archive with symlink preservation for shared library compatibility"
affects: [30-02, release, distribution, macos-builds]

# Tech tracking
tech-stack:
  added: []
  patterns: ["CI smoke testing pattern for cross-platform executables", "macOS entitlements for Python JIT compilation"]

key-files:
  created: ["entitlements.plist"]
  modified: ["job-radar.spec", ".github/workflows/release.yml"]

key-decisions:
  - "Ad-hoc signing with entitlements is sufficient for GitHub releases (codesign_identity=None)"
  - "Smoke tests only verify CLI --version (headless-safe), skip GUI tests requiring display server"
  - "CustomTkinter asset verification runs on Linux only for CI visibility"

patterns-established:
  - "Pattern 1: Entitlements file referenced in all PyInstaller output blocks (exe, gui_exe, BUNDLE)"
  - "Pattern 2: Smoke tests run after build, before archive creation to catch packaging issues early"
  - "Pattern 3: macOS archives use --symlinks flag to prevent shared library duplication and breakage"

# Metrics
duration: 1min
completed: 2026-02-13
---

# Phase 30 Plan 01: Packaging & Distribution Summary

**macOS code signing entitlements for Python JIT, CI smoke tests for all platforms, and symlink preservation in macOS archives**

## Performance

- **Duration:** 1 minute (118 seconds)
- **Started:** 2026-02-13T15:29:12Z
- **Completed:** 2026-02-13T15:31:10Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created entitlements.plist with com.apple.security.cs.allow-unsigned-executable-memory for Python JIT compilation on macOS
- Updated PyInstaller spec to reference entitlements in all three output blocks (exe, gui_exe, BUNDLE)
- Added CI smoke tests for Linux, Windows, and macOS to verify CLI executable runs --version after build
- Fixed macOS archive to preserve symbolic links, preventing shared library failures and archive bloat
- Added CustomTkinter asset verification step to confirm themes and fonts are bundled

## Task Commits

Each task was committed atomically:

1. **Task 1: Create entitlements.plist and update PyInstaller spec for macOS code signing** - `972f1b8` (feat)
2. **Task 2: Add CI smoke tests and fix macOS archive symlink preservation** - `d4e6e4c` (feat)

## Files Created/Modified
- `entitlements.plist` - macOS code signing entitlements allowing unsigned executable memory for Python JIT
- `job-radar.spec` - Updated exe, gui_exe, and BUNDLE blocks to reference entitlements_file='entitlements.plist'
- `.github/workflows/release.yml` - Added smoke tests for all platforms, CustomTkinter asset verification, and --symlinks flag for macOS archive

## Decisions Made
- Ad-hoc signing (codesign_identity=None) is sufficient for GitHub releases distribution - full signing certificate not required
- Smoke tests only verify CLI --version flag (headless-safe) - GUI tests skipped because they require display server in CI
- CustomTkinter asset verification runs on Linux only for CI visibility - confirms themes/fonts bundled without testing all platforms

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Phase 30 Plan 02 (actual build verification). All build configuration is in place:
- Entitlements configured for macOS code signing
- CI workflow enhanced with smoke tests
- Archive creation fixed to preserve symlinks

No blockers or concerns.

## Self-Check: PASSED

All files created and commits verified:
- FOUND: entitlements.plist
- FOUND: 972f1b8 (Task 1 commit)
- FOUND: d4e6e4c (Task 2 commit)

---
*Phase: 30-packaging-distribution*
*Completed: 2026-02-13*
