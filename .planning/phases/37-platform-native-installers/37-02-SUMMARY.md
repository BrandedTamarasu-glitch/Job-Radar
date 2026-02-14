---
phase: 37-platform-native-installers
plan: 02
subsystem: packaging
tags: [nsis, windows-installer, modern-ui, code-signing, pillow]

# Dependency graph
requires:
  - phase: 36-gui-uninstall-feature
    provides: GUI uninstall orchestration (job-radar-gui.exe --uninstall)
  - phase: 30-packaging-distribution
    provides: PyInstaller Windows executables (job-radar.exe, job-radar-gui.exe)
provides:
  - Windows NSIS installer with Modern UI wizard
  - Dual uninstall support (GUI with backup + NSIS quick remove)
  - Add/Remove Programs integration
  - .jobprofile file association
  - Conditional code signing infrastructure
  - Branding asset generation
affects: [37-03-ci-integration, future-auto-update]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "NSIS Modern UI 2 installer scripting"
    - "Conditional code signing with base64 certificates"
    - "Pillow-based branding asset generation"
    - "Windows file association with SHChangeNotify shell refresh"

key-files:
  created:
    - installers/windows/installer.nsi
    - installers/windows/build-installer.bat
    - installers/windows/license.txt
    - installers/windows/generate-assets.py
    - installers/windows/header.bmp
    - installers/windows/sidebar.bmp
    - installers/windows/icon.ico
  modified: []

key-decisions:
  - "NSIS Modern UI 2 for professional wizard interface"
  - "Dual uninstall: UninstallString launches job-radar-gui.exe --uninstall (GUI with backup), QuietUninstallString uses Uninstall.exe /S (NSIS direct)"
  - "Custom shortcuts page with Desktop and Quick Launch checkboxes (both default checked)"
  - "SetCompressor /SOLID lzma for best compression ratio"
  - "Conditional code signing checks WINDOWS_CERT_BASE64 env var (skip if not present, sign automatically when added)"
  - "Pillow-based asset generation creates header.bmp (150x57), sidebar.bmp (164x314), and icon.ico (multi-size)"
  - ".jobprofile file association with SHChangeNotify for shell refresh"
  - "Full Add/Remove Programs registry integration (DisplayName, UninstallString, QuietUninstallString, DisplayVersion, Publisher, URLInfoAbout, DisplayIcon, EstimatedSize, NoModify, NoRepair)"

patterns-established:
  - "NSIS installer pattern: MUI2 wizard with license, directory, custom shortcuts page, install, finish"
  - "Dual uninstall pattern: Primary GUI uninstall (with backup) + NSIS QuietUninstallString for silent removal"
  - "Conditional build pattern: Check for env var, skip step if not present, run automatically when added"
  - "Asset generation pattern: Python script creates all branding images from source icon programmatically"

# Metrics
duration: 176
completed: 2026-02-14
---

# Phase 37 Plan 02: Windows NSIS Installer Summary

**Windows NSIS Modern UI installer with wizard, dual uninstall (GUI with backup + quick NSIS remove), Add/Remove Programs integration, .jobprofile file association, conditional code signing, and programmatic branding asset generation**

## Performance

- **Duration:** 2.9 min (176 seconds)
- **Started:** 2026-02-14T19:23:57Z
- **Completed:** 2026-02-14T19:26:53Z
- **Tasks:** 2/2
- **Files created:** 7

## Accomplishments

- Windows users get professional NSIS Modern UI installer with wizard flow (welcome, license, directory, shortcuts, install, finish)
- Dual uninstall approach: Add/Remove Programs UninstallString launches job-radar-gui.exe --uninstall (GUI with backup option), QuietUninstallString provides Uninstall.exe /S (NSIS direct removal for quick/silent uninstall)
- Custom shortcuts page allows users to choose Desktop shortcut and Quick Launch shortcut (both default checked), Start Menu shortcuts always created
- .jobprofile file association registered with SHChangeNotify shell refresh (Windows recognizes association immediately)
- Full Add/Remove Programs integration with all standard registry entries (DisplayName, UninstallString, QuietUninstallString, DisplayVersion, Publisher, URLInfoAbout, DisplayIcon, EstimatedSize, NoModify, NoRepair)
- Conditional code signing infrastructure: build-installer.bat checks WINDOWS_CERT_BASE64 env var, skips if not present, signs automatically with signtool when certificate added
- Branding assets generated programmatically: generate-assets.py creates header.bmp (150x57), sidebar.bmp (164x314), and icon.ico (multi-size: 16, 32, 48, 256) from icon.png using Pillow
- SetCompressor /SOLID lzma for best compression ratio (per research pitfall 6)
- Version injection via /DVERSION= compile flag enables CI/CD automation
- MIT License displayed in installer wizard from project LICENSE file

## Task Commits

Each task was committed atomically:

1. **Task 1: Create NSIS installer script with Modern UI** - `aff0b73` (feat)
2. **Task 2: Create Windows build script and branding asset generator** - `be5af20` (feat)

**Plan metadata:** (pending - will be added after this summary)

## Files Created/Modified

**Created:**
- `installers/windows/installer.nsi` - NSIS Modern UI 2 installer script (177 lines) with dual uninstall, shortcuts page, file association, Add/Remove Programs registry
- `installers/windows/build-installer.bat` - Windows batch build script with NSIS compilation, pre-flight checks, conditional code signing
- `installers/windows/license.txt` - MIT License text from project LICENSE file
- `installers/windows/generate-assets.py` - Python script using Pillow to generate header.bmp (150x57), sidebar.bmp (164x314), icon.ico (multi-size)
- `installers/windows/header.bmp` - NSIS wizard header image (150x57) with dark navy background, right-aligned "Job Radar" text, target icon
- `installers/windows/sidebar.bmp` - NSIS welcome/finish sidebar image (164x314) with dark navy gradient, centered logo, version text
- `installers/windows/icon.ico` - Multi-size Windows icon (16, 32, 48, 256) converted from icon.png

**Modified:** None

## Decisions Made

1. **NSIS Modern UI 2 for professional wizard interface** - Industry standard for Windows installers (used by Firefox, VLC, 7-Zip), provides consistent wizard UX across Windows versions
2. **Dual uninstall approach** - UninstallString points to job-radar-gui.exe --uninstall (GUI with backup option per Phase 36), QuietUninstallString provides Uninstall.exe /S (NSIS direct removal for quick/silent uninstall). Gives users choice between full GUI with backup or fast silent removal.
3. **Custom shortcuts page with Desktop and Quick Launch checkboxes** - Both default checked for maximum discoverability, Start Menu shortcuts always created (standard Windows pattern)
4. **SetCompressor /SOLID lzma** - Best compression ratio per research pitfall 6, reduces installer size (balances build time vs download size)
5. **Conditional code signing infrastructure** - build-installer.bat checks WINDOWS_CERT_BASE64 env var, skips signing if not present (shows warning about SmartScreen), signs automatically when certificate added. No code changes needed to add signing later.
6. **Pillow-based asset generation** - generate-assets.py creates all branding images programmatically from icon.png, no manual image editing needed. Includes fallback placeholder icon if icon.png not found.
7. **.jobprofile file association with SHChangeNotify** - Registers .jobprofile extension, calls SHChangeNotify for shell refresh (Windows recognizes association immediately without reboot)
8. **Full Add/Remove Programs registry integration** - All standard registry entries (DisplayName, UninstallString, QuietUninstallString, DisplayVersion, Publisher, URLInfoAbout, DisplayIcon, EstimatedSize, NoModify, NoRepair) per NSIS best practices
9. **Version injection via /DVERSION= compile flag** - Enables CI/CD automation (GitHub Actions can pass version from git tag), no hardcoded versions in installer script
10. **icon.ico for MUI_ICON/MUI_UNICON** - NSIS requires .ico format (not .png), generate-assets.py converts from icon.png with multi-size ICO (16, 32, 48, 256)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 37 Plan 03:** CI/CD integration, installer README with bypass instructions, and auto-update config infrastructure

**Blockers:** None

**Concerns:** None

**What's available:**
- Complete Windows NSIS installer with Modern UI wizard
- Dual uninstall support (GUI with backup + NSIS quick remove)
- Conditional code signing infrastructure (ready for certificates when available)
- Programmatic branding asset generation
- .jobprofile file association
- Full Add/Remove Programs integration

**What Phase 37 Plan 03 needs:**
- CI/CD workflow extension for installer builds (GitHub Actions)
- Installer README documenting SmartScreen bypass for unsigned installers
- Auto-update config infrastructure (update check URL in config, JSON manifest schema)

---
*Phase: 37-platform-native-installers*
*Completed: 2026-02-14*
