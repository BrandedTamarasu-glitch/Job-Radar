# Phase 37: Platform-Native Installers - Context

**Gathered:** 2026-02-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Create professional installation packages for distributing Job Radar: DMG installer for macOS with drag-to-Applications workflow, and NSIS installer for Windows with setup wizard and Add/Remove Programs integration. Installers deliver the PyInstaller-built executables to users' systems with proper branding and system integration. Code signing will be added in a future phase.

</domain>

<decisions>
## Implementation Decisions

### DMG Design (macOS)
- Custom background image (not minimal/system default)
- Background shows: app icon → drag arrow → Applications folder, plus Job Radar logo/branding
- Horizontal icon layout: app icon on left, Applications folder on right, arrow between them
- Larger window for visibility (800x500 or similar, not standard 600x400)

### NSIS Wizard Flow (Windows)
- Include license agreement screen (display license text, require "I agree" checkbox)
- Install location: default to Program Files, but show "Advanced" option for power users to customize
- Create all three shortcut types:
  - Start Menu shortcut (always)
  - Desktop shortcut (optional, checkbox during install)
  - Quick Launch / pin to taskbar option (Windows 10/11)
- Modern branded visual style: custom header image with Job Radar logo, branded colors throughout wizard

### Code Signing Strategy
- **Ship unsigned for now** — code signing certificates will be obtained in a future phase
- Documentation must include **clear warnings** about security messages users will see (macOS Gatekeeper, Windows SmartScreen)
- README explains how to bypass warnings: right-click → Open on macOS, "Run anyway" on Windows
- **Prepare build scripts for future signing**: include signing steps with environment variables for certificates, make them conditional (skip if certs not present)
- **CI/CD automated**: GitHub Actions builds installers on tag/release, uploads to GitHub Releases

### System Integration
- Windows Add/Remove Programs entry includes:
  - Uninstall button (required)
  - Version number
  - Publisher info and support URL
  - Install size estimate
- **Dual uninstall approach**: Add/Remove Programs offers both "Launch full uninstall" (GUI with backup) and "Quick remove" (NSIS direct uninstall)
- **File association**: Register .jobprofile file extension (for profile sharing/import in future)
- **Auto-update preparation**: Include update check URL in config, prepare infrastructure for future auto-update feature (don't implement update mechanism yet, just foundation)

### Claude's Discretion
- Exact background image design and color scheme (match app branding)
- DMG window positioning and view settings (icon size, grid spacing)
- Specific NSIS script optimizations and error handling
- Build script implementation details (Makefile, shell scripts, or Python)
- CI/CD workflow specifics (matrix builds, artifact naming, release notes)

</decisions>

<specifics>
## Specific Ideas

- DMG should look professional — custom background makes it clear this is Job Radar, not just a random app
- Windows wizard should feel polished with branding, not generic installer
- Unsigned installer warnings are temporary — set up scripts now so adding certificates later is easy
- Dual uninstall (full GUI vs quick remove) respects different user preferences — power users can skip dialogs
- .jobprofile association enables future "share your profile" workflow
- Auto-update infrastructure now means we can add the feature later without installer changes

</specifics>

<deferred>
## Deferred Ideas

- Actual code signing with purchased certificates — future phase when ready to invest in certs
- Auto-update implementation — future phase, but infrastructure prepared
- Linux packaging (DEB/RPM) — noted in REQUIREMENTS.md as out of scope, .tar.gz acceptable for Linux users

</deferred>

---

*Phase: 37-platform-native-installers*
*Context gathered: 2026-02-14*
