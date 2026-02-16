# Phase 40: Auto-Update Installation - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can launch platform-specific installers from within the app after download completes. Includes the "Install Now" button wiring, platform-specific launch behavior (DMG mount, NSIS exe launch, Linux instructions), confirmation before close, and error handling for failed launches. Version skipping and changelog preview are Phase 41 scope.

</domain>

<decisions>
## Implementation Decisions

### Install Now behavior
- App auto-closes before launching installer — no conflicts with files in use
- Brief confirmation dialog before closing: "Ready to install v{version}? The app will restart."
- After spawning installer, show brief "Installer launched. Closing app..." status message, then exit
- Downloaded installer file kept until next app start (delete on next launch) — ensures installer had time to read the file

### Platform-specific experience
- Platform-specific messages explaining what's about to happen (not generic)
  - macOS: "Opening installer DMG..."
  - Windows: "Launching installer..."
  - Linux: different flow (see Linux handling)
- macOS DMG: mount DMG and open the volume in Finder so user sees drag-to-Applications window
- Windows NSIS: just launch the exe — let Windows show the UAC prompt naturally
- Quarantine handling on macOS: Claude's discretion on whether to strip xattr

### Failure & edge cases
- SHA256 mismatch: show Retry button AND "Download manually" link to GitHub releases page
- Missing installer file (temp cleaned up): "Installer file not found. Download again?" — user clicks to re-download
- Installer launch failure (permissions): error message with file path AND retry button — "Couldn't launch installer. File saved at: [path]"
- Trust download-time SHA256 verification — no re-verify before launch

### Linux handling
- Button label says "Open Download" instead of "Install Now" (honest about what it does)
- Clicking shows instructions dialog with extraction commands
- Include one-liner command with "Copy" button for easy terminal pasting
- "Open Folder" button in the dialog to open containing directory in file manager
- Instructions show: tar extraction command + where to move files

### Claude's Discretion
- macOS quarantine attribute handling (strip or leave)
- Exact delay before app exit after showing status message
- Linux extraction command format and path references
- How to detect and open platform file manager on Linux (xdg-open)

</decisions>

<specifics>
## Specific Ideas

- Confirmation dialog before close gives user a chance to save work or back out
- "Installer launched. Closing app..." provides reassurance that something happened before the window disappears
- Linux "Open Download" label sets correct expectations — no auto-install promise
- Cleanup on next launch is safer than immediate deletion since installer may still be reading the file

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 40-auto-update-installation*
*Context gathered: 2026-02-16*
