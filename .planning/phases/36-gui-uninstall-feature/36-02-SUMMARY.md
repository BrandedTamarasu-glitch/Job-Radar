---
phase: 36-gui-uninstall-feature
plan: 02
subsystem: gui-frontend
status: complete
completed: 2026-02-14
duration: 213
wave: 2

# Dependencies
requires:
  - Phase 36 Plan 01 (core uninstaller backend)
  - Phase 20 (GUI foundation with modal dialog patterns)
  - customtkinter (CTkToplevel, CTkProgressBar, CTkCheckBox)

provides:
  - Complete GUI uninstall experience (backup -> preview -> confirm -> delete -> quit)
  - Four specialized dialogs: BackupOfferDialog, PathPreviewDialog, FinalConfirmationDialog, DeletionProgressDialog
  - Settings tab integration with red "Uninstall Job Radar" button
  - Full orchestration of uninstall flow with threading and error handling

affects:
  - End-user uninstall experience (completes PKG-01, PKG-02, PKG-03, PKG-06)

# Technical Details
tech-stack:
  added:
    - tkinter.filedialog (native file picker for backup ZIP)
    - threading.Thread (background deletion to prevent GUI freeze)
  patterns:
    - Modal dialog pattern with transient(parent) + grab_set() + wait_window()
    - Checkbox-gated destructive action (disabled red button until checkbox checked)
    - Background thread with polling via self.after() for GUI updates
    - Two-step confirmation (path preview + final checkbox confirm)

key-files:
  created:
    - job_radar/gui/uninstall_dialog.py (413 lines, 4 dialog classes)
  modified:
    - job_radar/gui/main_window.py (+158 lines: imports, Danger Zone UI, orchestration)
    - tests/test_uninstaller.py (+144 lines: 4 integration tests)

decisions:
  - native-file-picker-for-backup:
      context: "User needs to choose backup ZIP location"
      decision: "Use tkinter.filedialog.asksaveasfilename with defaultextension='.zip'"
      rationale: "Native OS file picker is familiar, handles paths/permissions correctly"
      alternatives: ["Custom CTk file browser", "Fixed backup location"]
      impact: "Better UX, no path validation needed, works cross-platform"

  - threading-for-deletion:
      context: "delete_app_data() may take several seconds, can freeze GUI"
      decision: "Run deletion in background thread, poll with self.after(100, check_completion)"
      rationale: "Keeps GUI responsive, allows progress dialog to show indeterminate animation"
      alternatives: ["Blocking call with update() loop", "asyncio/async callbacks"]
      impact: "Smooth UX, no freeze, simple polling pattern matches existing codebase"

  - checkbox-gated-red-button:
      context: "Final confirmation needs strong safety signal before destructive action"
      decision: "Red 'Uninstall' button starts disabled, checkbox enables it"
      rationale: "Forces deliberate action, red color signals danger, common pattern"
      alternatives: ["Type 'DELETE' to confirm", "Double-click confirmation"]
      impact: "Clear intent verification, prevents accidental clicks"

  - three-step-confirmation:
      context: "Uninstall is destructive and irreversible"
      decision: "Path preview (can cancel) -> Final confirmation with checkbox (can cancel) -> Progress"
      rationale: "User sees exactly what will be deleted, multiple escape hatches"
      alternatives: ["Single confirmation dialog", "No preview, just checkbox"]
      impact: "Maximum transparency, reduces support burden (users know what's removed)"

  - partial-failure-reporting:
      context: "Some files may fail to delete (locked, permissions)"
      decision: "Show error dialog with list of failed paths (first 5, with count of remainder)"
      rationale: "User knows what needs manual cleanup, better than silent failure"
      alternatives: ["Silent ignore failures", "Fail-fast on first error"]
      impact: "Transparency, user can manually clean up locked files"

tags: [gui, uninstall, dialogs, threading, confirmation, ux, settings]
---

# Phase 36 Plan 02: GUI Uninstall Dialogs Summary

**One-liner:** Complete GUI uninstall flow with backup offer (native file picker), path preview, checkbox-gated red button, threaded deletion, and auto-quit

## Objective

Create GUI uninstall dialogs and wire them into the Settings tab with full orchestration of the backup-preview-confirm-delete-quit flow. This completes the user-facing uninstall experience for GUI users.

## What Was Built

### Dialog Classes (job_radar/gui/uninstall_dialog.py)

**1. BackupOfferDialog**
- Modal dialog offering backup before uninstall
- Three buttons: "Create Backup" (opens native file picker), "Skip Backup", "Cancel"
- Native file picker defaults to `job-radar-backup.zip`, filters to ZIP files
- Shows "Backup saved!" success message briefly (1 second) before proceeding
- If backup fails: shows error, allows "Continue without backup" or cancel
- Returns `result` attribute: "backup_done", "skip", or "cancel"

**2. PathPreviewDialog**
- Modal dialog showing scrollable list of files/directories to be deleted
- Receives paths from `get_uninstall_paths()` as list of (path, description) tuples
- Each entry shows: path in bold/monospace, description in gray below
- "Continue" and "Cancel" buttons
- Returns `result` attribute: True (continue) or False (cancel)

**3. FinalConfirmationDialog**
- Modal dialog with red warning text and checkbox-gated button
- Warning: "This will permanently delete all Job Radar data. This action cannot be undone."
- CTkCheckBox: "I understand this cannot be undone" (unchecked by default)
- Red "Uninstall" button: starts disabled, enabled when checkbox checked
- "Cancel" button
- Returns `result` attribute: True (confirmed) or False (cancelled)

**4. DeletionProgressDialog**
- Modal dialog with indeterminate progress bar during deletion
- Status label (starts as "Deleting application data...")
- Progress bar animates continuously
- Prevents window close via `protocol("WM_DELETE_WINDOW", lambda: None)`
- `update_status(message)` method updates label text
- `close()` method stops progress bar and destroys dialog

### Settings Tab Integration (job_radar/gui/main_window.py)

**Danger Zone Section**
- Added after scoring config widget in Settings tab
- Red "Danger Zone" title (bold, size 16)
- Description: "Remove Job Radar and all associated data from your system"
- Red "Uninstall Job Radar" button (height 40, width 200, fg_color="red", hover_color="darkred")

**Orchestration Method: _start_uninstall()**

Full flow:
1. **Backup offer** - Show BackupOfferDialog
   - If cancelled: return silently (no side effects)
   - If backup selected: open native file picker, create ZIP
   - If backup fails: show error in dialog, offer continue-without-backup option
2. **Path preview** - Get paths via `get_uninstall_paths()`, show PathPreviewDialog
   - If no paths found: show error "No application data found to uninstall"
   - If cancelled: return silently
3. **Final confirmation** - Show FinalConfirmationDialog with checkbox
   - If cancelled: return silently
4. **Deletion** - Show DeletionProgressDialog, run `delete_app_data()` in background thread
   - Thread stores failures in result_container
   - Poll every 100ms via `self.after(100, check_completion)`
   - When complete: close progress dialog, handle results
5. **Results handling**
   - If partial failures: show error dialog with list of failed paths (first 5 + "...and N more")
   - Check if binary cleanup needed via `get_binary_path()`
   - If frozen: call `create_cleanup_script(binary_path)`, use returned message
   - If not frozen: message = "Data removed successfully"
6. **Final success dialog and quit**
   - Show success dialog with message + "Goodbye!"
   - OK button destroys dialog and calls `self.quit()` to exit app

### Integration Tests (tests/test_uninstaller.py)

Added 4 integration-level tests:

1. **test_delete_app_data_full_flow** - Realistic directory structure (profile.json, config.json, backups/, rate_limits.db, log), verifies complete deletion
2. **test_create_backup_then_delete_preserves_backup** - Creates backup at external location, deletes data, verifies backup survives, validates ZIP contents
3. **test_get_uninstall_paths_returns_correct_descriptions** - Verifies human-readable descriptions match file types (search preferences, settings, error log, etc.)
4. **test_integration_delete_with_locked_file_continues** - Simulates locked file, verifies deletion continues, collects failure in results list

## Key Decisions Made

**1. Native file picker for backup**
- Used `tkinter.filedialog.asksaveasfilename` instead of custom file browser
- Provides familiar OS-native experience, handles permissions/validation automatically
- Defaults to `job-radar-backup.zip` with `.zip` extension filter

**2. Background threading for deletion**
- Runs `delete_app_data()` in background thread to prevent GUI freeze
- Polls completion every 100ms via `self.after(100, check_completion)` pattern
- Matches existing codebase patterns (search worker uses similar approach)

**3. Checkbox-gated red button**
- Red "Uninstall" button starts disabled until checkbox checked
- Forces deliberate action, prevents accidental clicks
- Common pattern for destructive actions (GitHub, GitLab, etc.)

**4. Three-step confirmation**
- Path preview (cancellable) → Final confirmation with checkbox (cancellable) → Progress
- User sees exact paths before confirming
- Multiple escape hatches reduce risk of unintended uninstall

**5. Partial failure reporting**
- Shows first 5 failed paths with error messages + count of remaining failures
- User knows what needs manual cleanup vs silent failure
- Better support experience (transparent about locked/permission-denied files)

## Testing Results

```
============================= 566 passed in 14.98s =============================
```

- 4 new integration tests (100% pass rate)
- 19 existing uninstaller unit tests (all passing)
- 0 regressions in 543 other tests
- All verification criteria met

## Task Breakdown

| Task | Description | Commit | Files | Lines |
|------|-------------|--------|-------|-------|
| 1 | Create uninstall_dialog.py with 4 dialog classes | d1ef217 | job_radar/gui/uninstall_dialog.py | 413 |
| 2 | Wire uninstall button and orchestration to Settings tab | fd026bd | job_radar/gui/main_window.py, tests/test_uninstaller.py | 307 |

**Total:** 2 tasks, 3 files modified, 720 lines added

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Blockers:** None

**Concerns:** None

**Ready for:** Phase 36 complete - GUI uninstall feature fully delivered

The uninstall experience is now complete for GUI users:
- Settings tab has red "Uninstall Job Radar" button in Danger Zone section
- Full flow: backup offer → path preview → checkbox confirmation → deletion → quit
- Each step can be cancelled (no side effects until final confirmation)
- Backup uses native OS file picker
- Deletion runs in background thread with progress feedback
- Partial failures reported with specific file paths
- Binary cleanup scripts generated for frozen apps (macOS/Windows/Linux)
- App quits automatically after successful uninstall

## Files Changed

**Created:**
- `job_radar/gui/uninstall_dialog.py` - Four dialog classes for uninstall flow

**Modified:**
- `job_radar/gui/main_window.py` - Added Danger Zone section, uninstall button, orchestration method
- `tests/test_uninstaller.py` - Added 4 integration tests for full-flow verification

**Dependencies Added:** None (all stdlib + existing dependencies)

## Verification Commands

```bash
# Dialog imports
python -c "from job_radar.gui.uninstall_dialog import BackupOfferDialog, PathPreviewDialog, FinalConfirmationDialog, DeletionProgressDialog; print('All dialog imports OK')"

# Uninstaller tests
pytest tests/test_uninstaller.py -v

# Full test suite
pytest tests/ -x -q

# Verify UI elements
grep "Uninstall Job Radar" job_radar/gui/main_window.py
grep "_start_uninstall" job_radar/gui/main_window.py
```

## Metrics

- **Duration:** 213 seconds (~3.55 minutes)
- **Test count:** 4 new integration tests (23 total uninstaller tests)
- **Code added:** 720 lines (413 dialog code, 307 orchestration + tests)
- **Dialog classes:** 4 (BackupOfferDialog, PathPreviewDialog, FinalConfirmationDialog, DeletionProgressDialog)
- **Confirmation steps:** 3 (backup offer, path preview, final checkbox)
- **Platforms supported:** macOS, Windows, Linux (via Phase 36-01 backend)

## User Experience Flow

1. User clicks red "Uninstall Job Radar" button in Settings → Danger Zone
2. Backup offer dialog appears with 3 options
3. If "Create Backup": native file picker opens, saves ZIP
4. Path preview shows exact files to be deleted with descriptions
5. User clicks "Continue" (or cancels)
6. Final confirmation requires checking "I understand" box
7. Red "Uninstall" button enables only after checkbox checked
8. Progress dialog shows during deletion (indeterminate spinner)
9. If failures: error dialog lists specific paths that couldn't be deleted
10. Success dialog shows "Data removed. Goodbye!" (or platform-specific message)
11. User clicks OK → app quits immediately

**Silent cancellation:** All steps before final confirmation can be cancelled with no side effects. No error messages, no state changes - user simply returns to Settings tab.

**Transparency:** User sees exact paths, exact errors, exact cleanup status. No surprises.

**Safety:** Three confirmation steps, red color coding, disabled-by-default button, multiple escape hatches.
