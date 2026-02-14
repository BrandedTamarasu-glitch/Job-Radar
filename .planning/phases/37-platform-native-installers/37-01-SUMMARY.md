---
phase: 37-platform-native-installers
plan: 01
subsystem: infra
tags: [macos, dmg, installer, pyinstaller, create-dmg, pillow, file-association]

# Dependency graph
requires:
  - phase: 36-gui-uninstall-feature
    provides: Complete GUI uninstall flow with backup-preview-confirm-delete-quit workflow
provides:
  - macOS DMG installer build infrastructure with create-dmg automation
  - Programmatic DMG background image generation (800x500 branded)
  - .jobprofile file association registered in macOS app bundle Info.plist
  - Conditional code signing infrastructure (skip if certificates not present)
affects: [38-windows-nsis-installer, CI/CD, future-release-automation]

# Tech tracking
tech-stack:
  added: [create-dmg (shell script), PIL/Pillow (background generation)]
  patterns: [conditional-code-signing, branded-dmg-layout, file-association-registration]

key-files:
  created:
    - installers/macos/build-dmg.sh
    - installers/macos/generate-background.py
    - installers/macos/dmg-background.png
  modified:
    - job-radar.spec

key-decisions:
  - "DMG window size 800x500 (larger than standard 600x400 for better visibility on modern displays)"
  - "App icon at (200,190), Applications folder at (600,190) - horizontally aligned drag target"
  - "Conditional code signing: skip if MACOS_CERT_BASE64 not set, log clear instructions for unsigned DMG"
  - "Pillow-generated background using system fonts with fallback to defaults"
  - ".jobprofile file association via CFBundleDocumentTypes in Info.plist"
  - "LSHandlerRank 'Owner' - Job Radar is default handler for .jobprofile files"

patterns-established:
  - "Conditional signing pattern: check for env var, skip if missing, log bypass instructions"
  - "DMG background automation: Python script generates branded 800x500 PNG with logo/tagline/arrow"
  - "File association in PyInstaller spec: CFBundleDocumentTypes list with extensions/role/rank"

# Metrics
duration: 2min
completed: 2026-02-14
---

# Phase 37 Plan 01: Platform-Native Installers Summary

**macOS DMG installer infrastructure with Pillow-generated branded background (800x500), create-dmg automation, .jobprofile file association, and conditional code signing**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-14T19:23:46Z
- **Completed:** 2026-02-14T19:25:42Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- DMG build automation script using create-dmg with custom branded layout
- Programmatic background generation (Pillow) with Job Radar logo, tagline, and drag arrow
- macOS .jobprofile file association registered in app bundle Info.plist
- Conditional code signing infrastructure (skip if certificates not present, log user instructions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create DMG background generator and build script** - `ba0a641` (feat)
2. **Task 2: Add .jobprofile file association to macOS Info.plist** - `b225785` (feat)

## Files Created/Modified
- `installers/macos/build-dmg.sh` - create-dmg automation script with conditional signing
- `installers/macos/generate-background.py` - Pillow-based 800x500 background generator
- `installers/macos/dmg-background.png` - Generated branded background with arrow
- `job-radar.spec` - Updated BUNDLE info_plist with CFBundleDocumentTypes for .jobprofile

## Decisions Made

1. **DMG window size 800x500** - Larger than standard 600x400 to ensure background fully visible on macOS 11.0+ (title bar intrusion, path bar visibility)
2. **Icon positions: app at (200,190), Applications at (600,190)** - Horizontally aligned drag targets with clear visual arrow pointing right
3. **Conditional code signing** - Check MACOS_CERT_BASE64 env var, skip signing if not present, log clear Gatekeeper bypass instructions for users
4. **Pillow background generation** - Use system fonts (Helvetica.ttc) with fallback to PIL defaults for cross-platform build compatibility
5. **.jobprofile file association** - CFBundleDocumentTypes in Info.plist registers Job Radar as "Owner" (default handler) for .jobprofile files
6. **Version metadata in Info.plist** - Added CFBundleShortVersionString and CFBundleVersion (2.1.0) for macOS Finder Get Info display

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - DMG infrastructure complete. Future phases will wire into CI/CD release workflow.

**Note for unsigned DMG usage:**
- Users will see macOS Gatekeeper warning: "JobRadar cannot be opened because the developer cannot be verified"
- Bypass: Right-click DMG → Open → "Open anyway" button appears
- build-dmg.sh logs these instructions when MACOS_CERT_BASE64 not set

## Next Phase Readiness

- DMG build infrastructure ready for manual testing and CI/CD integration
- Next phase: Windows NSIS installer (37-02)
- Future phase: CI/CD automation to call build-dmg.sh in release workflow
- Blocker: Code signing certificates ($99/year Apple Developer) deferred - ship unsigned initially

---
*Phase: 37-platform-native-installers*
*Completed: 2026-02-14*
