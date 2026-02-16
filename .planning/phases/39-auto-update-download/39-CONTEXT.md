# Phase 39: Auto-Update Download - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can download platform-specific installers from GitHub Releases with visual progress feedback. Includes download initiation with confirmation, progress bar in the banner, cancel/retry behavior, temp file management, and SHA256 integrity verification. Launching the installer is Phase 40 scope.

</domain>

<decisions>
## Implementation Decisions

### Download trigger & flow
- Confirmation dialog before download starts: "Download v{version}? ~{size}MB"
- After confirmation, banner transforms to show progress inline (replaces notification buttons with progress bar)
- Download runs in background thread — user can use app normally, navigate tabs, while banner shows progress
- On completion, banner shows "Download complete!" with "Install Now" button (wired in Phase 40)

### Progress visualization
- Progress bar displayed inline in the transformed banner (replaces Download/Remind Later/X buttons)
- Shows: progress bar + percentage + downloaded/total size (e.g., "45% (12 MB / 25 MB)")
- Progress bar uses same blue/teal accent color as the notification banner — cohesive look
- Cancel button displayed alongside progress bar on the right side

### Cancel & failure behavior
- Cancel button in banner during download — clicking cancels immediately
- On cancel: suppress banner until next program start (not 24h/7d suppress — just session dismiss)
- Partial file deleted on cancel — clean slate
- On download failure: banner shows "Download failed" with Retry and Dismiss buttons
- Retry restarts download from scratch (no resume/range requests) — simpler, always works
- Retry limit: Claude's discretion on auto-retry behavior

### File management
- Downloaded installers saved to system temp directory (OS temp folder)
- Auto-detect platform: pick correct asset from GitHub release (DMG for macOS, NSIS exe for Windows, tar.gz for Linux)
- SHA256 hash verification after download completes (check against hash from GitHub release assets)
- If hash mismatch: treat as download failure, show Retry button
- Cleanup: delete downloaded installer after install is launched (Phase 40 handles cleanup trigger)

### Claude's Discretion
- Progress update frequency (visual refresh rate)
- Retry strategy (manual-only vs auto-retry once then manual)
- Confirmation dialog exact layout and styling
- How to extract/match SHA256 hashes from GitHub release assets
- Temp file naming convention
- Banner transition animation between notification and progress states

</decisions>

<specifics>
## Specific Ideas

- Banner transforms in-place: notification state -> progress state -> completion state -> back to notification (on cancel/dismiss)
- "Install Now" button in completion state bridges to Phase 40 (installer launch)
- Cancel dismisses for session only — softer than 24h suppress since user may want to try again soon

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 39-auto-update-download*
*Context gathered: 2026-02-16*
