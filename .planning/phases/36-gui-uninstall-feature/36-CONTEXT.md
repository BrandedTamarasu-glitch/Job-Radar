# Phase 36: GUI Uninstall Feature - Context

**Gathered:** 2026-02-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Add GUI uninstall button in Settings tab that cleanly removes Job Radar and all its data (profile, config, cache, rate limits, logs) from the user's system. Includes confirmation flow, optional backup, progress feedback, and platform-specific binary deletion.

</domain>

<decisions>
## Implementation Decisions

### Confirmation Flow
- Two-step confirmation: info dialog → final confirmation dialog
- First dialog shows paths with descriptions (e.g., "profile.json - Your search preferences")
- Final confirmation uses checkbox + button pattern: "I understand this cannot be undone" checkbox before red "Uninstall" button activates
- Cancellation just closes dialog silently (no toast/feedback)

### Backup Behavior
- Backup option presented first, before path preview dialog
- Backup includes just user data: profile and config only (exclude cache, rate limits, temp data)
- Format: ZIP file with native file picker for save location
- If backup fails: show error, offer "Continue without backup" option (don't block uninstall)

### Deletion Scope & Feedback
- Delete all app data: profile, config, cache, rate limits, logs - everything in app data directory
- Show progress dialog during deletion (modal with "Deleting..." and progress indicator)
- After successful deletion: show success message ("Uninstall complete. Goodbye!"), then app quits automatically
- Partial deletion failures: best effort approach - delete what's possible, report what failed with list of paths

### Two-Stage Cleanup (Running App)
- Platform-specific binary deletion:
  - macOS: move to Trash
  - Windows: self-delete on exit
  - Linux: rm on exit
- Create and execute cleanup script/task for binary deletion
- Success message includes manual deletion instructions: "Data removed. Move app to Trash when ready" (platform-specific)
- If binary can't be deleted: show final dialog before quit with manual deletion path

### Claude's Discretion
- Exact dialog text and wording
- Progress indicator type (spinner vs progress bar)
- Error message details for specific failure cases
- Cleanup script implementation details per platform

</decisions>

<specifics>
## Specific Ideas

- Checkbox pattern for final confirmation prevents accidental clicks
- File picker for backup gives users control over where backup is saved
- Best-effort deletion approach means users aren't stuck if one file is locked
- Platform-specific handling respects OS conventions (Trash on macOS, etc.)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 36-gui-uninstall-feature*
*Context gathered: 2026-02-14*
