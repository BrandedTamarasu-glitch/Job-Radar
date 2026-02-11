# Phase 6: Core Packaging Infrastructure - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Create working standalone executables (Windows .exe, macOS .app, Linux binary) that run without Python installation required. Users should be able to double-click and launch the application with bundled dependencies accessible.

</domain>

<decisions>
## Implementation Decisions

### Executable behavior on launch
- **Console visibility:** Show console window on all platforms for transparency and debuggability
- **Startup failure handling:** Write errors to job-radar-error.log in user's directory with brief console message
- **Startup banner:** Display "Job Radar v1.1" banner with ASCII art or decoration on launch
- **macOS dock behavior:** Show app icon in dock while running (standard macOS convention)

### Platform-specific adaptations
- **Data storage location:** Use platform standards
  - Windows: %APPDATA%\JobRadar
  - macOS: ~/Library/Application Support/JobRadar
  - Linux: ~/.job-radar
- **Executable naming:** Consistent naming across platforms
  - Windows: job-radar.exe
  - macOS: JobRadar.app
  - Linux: job-radar
- **Terminal/console behavior:** Consistent output, colors, and formatting across all platforms
- **Path separators:** Claude's discretion (native vs forward slashes in generated output)

### Bundled resource handling
- **Resources are read-only:** Frozen at build time, never modified at runtime
- **Missing resource handling:** Claude's discretion (fail fast vs fallback vs self-repair)
- **Startup verification:** Claude's discretion (verify on startup vs on-demand)
- **sys._MEIPASS path handling:** Claude's discretion (automatic detection is standard PyInstaller pattern)

### Build and distribution structure
- **Windows distribution:** Folder (onedir) - job-radar/ folder with .exe + dependencies, distributed as ZIP
- **macOS distribution:** Claude's discretion (DMG vs ZIP vs .app only)
- **Linux distribution:** Folder (onedir) - job-radar/ folder with binary + dependencies, distributed as tar.gz
- **Documentation:** Include README.txt with basic usage instructions, requirements, and troubleshooting

### Claude's Discretion
- Path separator handling in generated output (native vs universal forward slashes)
- Missing bundled resource failure strategy (fail fast, fallback, or self-repair)
- Resource verification timing (startup vs on-demand)
- sys._MEIPASS path detection (implement standard PyInstaller pattern)
- macOS distribution format (DMG, ZIP, or .app only)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-core-packaging-infrastructure*
*Context gathered: 2026-02-09*
