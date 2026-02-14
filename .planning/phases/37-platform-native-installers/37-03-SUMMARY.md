---
phase: 37-platform-native-installers
plan: 03
subsystem: infra
tags: [ci-cd, github-actions, dmg, nsis, auto-update, installer-docs]

# Dependency graph
requires:
  - phase: 37-01-macos-dmg-installer
    provides: macOS DMG build infrastructure with create-dmg automation
  - phase: 37-02-windows-nsis-installer
    provides: Windows NSIS installer with Modern UI wizard
  - phase: 30-packaging-distribution
    provides: PyInstaller build artifacts for macOS and Windows
provides:
  - GitHub Actions release workflow with automated installer builds
  - Installer documentation with macOS Gatekeeper and Windows SmartScreen bypass instructions
  - Auto-update configuration infrastructure with version comparison utilities
  - Conditional code signing in CI/CD (runs when secrets present, skips cleanly when absent)
affects: [future-auto-update, release-automation, code-signing]

# Tech tracking
tech-stack:
  added: []
  patterns: [github-actions-matrix-build, conditional-code-signing, auto-update-infrastructure]

key-files:
  created:
    - installers/README.md
    - job_radar/update_config.py
  modified:
    - .github/workflows/release.yml

key-decisions:
  - "build-installers job runs AFTER build job and BEFORE release job (sequential dependency)"
  - "Matrix strategy builds DMG on macos-latest and NSIS on windows-latest in parallel"
  - "Installers extract PyInstaller archives, run platform-specific build scripts (build-dmg.sh, build-installer.bat)"
  - "Conditional signing via GitHub Secrets environment variables (MACOS_CERT_BASE64, WINDOWS_CERT_BASE64)"
  - "Installer artifacts uploaded separately (installer-macos, installer-windows) for GitHub Releases"
  - "README documents bypass steps for unsigned installers (macOS Gatekeeper, Windows SmartScreen)"
  - "Auto-update config disabled by default (enabled: false) until feature implemented"
  - "Version comparison utilities (parse_version, is_update_available, is_version_supported) ready for future auto-update"
  - "Update manifest JSON schema documented in update_config.py for GitHub Pages hosting"

patterns-established:
  - "CI/CD installer build pattern: build PyInstaller archives → build-installers job downloads and extracts → run platform build scripts → upload installer artifacts → release job includes all artifacts"
  - "Conditional signing pattern: check for env var in GitHub Secrets, skip if not present, sign automatically when added"
  - "Auto-update infrastructure pattern: disabled-by-default config with version utilities ready for future implementation"

# Metrics
duration: 121
completed: 2026-02-14
---

# Phase 37 Plan 03: CI/CD Installer Integration Summary

**GitHub Actions release workflow builds DMG and NSIS installers automatically on tagged releases, with installer documentation for unsigned warnings and auto-update config infrastructure**

## Performance

- **Duration:** 2.0 min (121 seconds)
- **Started:** 2026-02-14T19:28:38Z
- **Completed:** 2026-02-14T19:30:39Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- CI/CD release workflow extended with build-installers job that builds DMG (macOS) and NSIS installer (Windows) after PyInstaller build
- Installer artifacts automatically included in GitHub Releases alongside existing .zip/.tar.gz archives
- installers/README.md created with clear bypass instructions for macOS Gatekeeper and Windows SmartScreen warnings on unsigned installers
- job_radar/update_config.py created with version comparison utilities (parse_version, is_update_available, is_version_supported) and update manifest JSON schema for future auto-update feature
- Conditional code signing infrastructure in CI/CD runs when GitHub Secrets present, skips cleanly when absent
- Auto-update config disabled by default (enabled: false) until feature implemented

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend release workflow with installer builds** - `1e28d64` (feat)
2. **Task 2: Create installer README and auto-update config** - `cf6178b` (feat)

**Plan metadata:** (pending - will be added after this summary)

## Files Created/Modified

**Created:**
- `installers/README.md` - Documentation for macOS Gatekeeper and Windows SmartScreen bypass steps, local build instructions, CI/CD signing secrets documentation
- `job_radar/update_config.py` - Auto-update config module with version comparison utilities, update manifest JSON schema, disabled-by-default config

**Modified:**
- `.github/workflows/release.yml` - Added build-installers job with macOS/Windows matrix, updated release job to include installer artifacts

## Decisions Made

1. **build-installers job runs AFTER build job and BEFORE release job** - Sequential dependency ensures PyInstaller archives built first, then installers, then GitHub Release created with all artifacts
2. **Matrix strategy builds DMG on macos-latest and NSIS on windows-latest in parallel** - Both platform installers build simultaneously for faster CI/CD execution
3. **Installers extract PyInstaller archives, run platform-specific build scripts** - build-installers job downloads job-radar-macos and job-radar-windows artifacts, extracts them to dist/, then runs installers/macos/build-dmg.sh or installers/windows/build-installer.bat
4. **Conditional signing via GitHub Secrets environment variables** - MACOS_CERT_BASE64, MACOS_CERT_PASSWORD, MACOS_SIGNING_IDENTITY for macOS; WINDOWS_CERT_BASE64, WINDOWS_CERT_PASSWORD for Windows. Scripts check for presence, skip signing if not set, sign automatically when added.
5. **Installer artifacts uploaded separately for GitHub Releases** - installer-macos/*.dmg and installer-windows/*.exe uploaded as separate artifacts, included in release files glob alongside job-radar-*/*.zip archives
6. **README documents bypass steps for unsigned installers** - Clear step-by-step instructions for macOS Gatekeeper (right-click → Open, or System Settings → Privacy & Security) and Windows SmartScreen (More info → Run anyway)
7. **Auto-update config disabled by default (enabled: false)** - get_update_config() returns enabled: False until auto-update feature implemented in future phase
8. **Version comparison utilities ready for future auto-update** - parse_version() converts "2.1.0" to (2, 1, 0) tuple, is_update_available() compares tuples, is_version_supported() checks minimum version
9. **Update manifest JSON schema documented in update_config.py** - Defines expected structure for update.json hosted on GitHub Pages (version, min_version, release_url, platform-specific download URLs, changelog)
10. **Pillow installed in CI for asset generation** - build-installers job installs Pillow to run generate-background.py (macOS) and generate-assets.py (Windows) for branding images

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

**Note for future code signing:**
- Add GitHub Secrets for macOS (MACOS_CERT_BASE64, MACOS_CERT_PASSWORD, MACOS_SIGNING_IDENTITY) and Windows (WINDOWS_CERT_BASE64, WINDOWS_CERT_PASSWORD)
- Installers will automatically sign on next release build (no code changes needed)
- Certificates cost $99/year (Apple Developer) + $100-400/year (Windows Code Signing)

## Next Phase Readiness

**Phase 37 Complete:** Platform-native installers infrastructure finished

**Blockers:** None

**Concerns:** None

**What's available:**
- Complete CI/CD pipeline builds DMG and NSIS installers automatically on tagged releases
- Installers appear in GitHub Releases alongside existing .zip/.tar.gz archives
- Clear documentation for unsigned installer bypass (macOS Gatekeeper, Windows SmartScreen)
- Auto-update config infrastructure ready for future implementation
- Conditional code signing infrastructure ready for certificates

**What v2.1.0 milestone needs next:**
- Phase 37 complete - ready to tag v2.1.0 release
- All v2.1.0 features shipped (source expansion, staffing firm control, scoring customization, uninstall, installers)
- Manual testing of installers before release tagging recommended

---
*Phase: 37-platform-native-installers*
*Completed: 2026-02-14*
