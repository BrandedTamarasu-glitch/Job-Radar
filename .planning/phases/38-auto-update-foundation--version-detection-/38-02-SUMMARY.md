---
phase: 38-auto-update-foundation
plan: 02
subsystem: gui
tags: [customtkinter, update-notification, settings-ui, threading, webbrowser]

dependency-graph:
  requires:
    - job_radar.update_checker.UpdateChecker (plan 38-01)
    - job_radar.gui.main_window.MainWindow (grid layout modification)
    - job_radar.__version__ (current version display)
  provides:
    - UpdateBanner CTkFrame widget with dismiss/remind callbacks
    - Update notification UI in MainWindow (banner + Settings section)
    - Background update check on app launch
    - Manual check button with inline feedback
    - Auto-check toggle in Settings
  affects:
    - 40-auto-update-installation (will use UpdateBanner for download progress)

tech-stack:
  added:
    - webbrowser module (open GitHub Releases in browser)
  patterns:
    - Queue-based messaging for update check results
    - Inline button feedback pattern (Checking... -> result -> reset)
    - Per-version banner suppression (24h dismiss, 7d remind)
    - Background thread for non-blocking update checks

key-files:
  created:
    - job_radar/gui/update_banner.py (110 LOC, UpdateBanner widget)
  modified:
    - job_radar/gui/main_window.py (288 LOC added: banner integration, Settings Updates section)

decisions:
  - Use blue/teal accent color (#3498DB/#2874A6) for banner to match VS Code update style
  - Place Updates section before API Key Settings (more important to users)
  - Show banner only on launch checks, not manual checks (manual check shows inline feedback)
  - Reset manual check button text after 3 seconds for clean UI
  - Guard Settings widget updates with null checks (lazy tab building)
  - Corrected GitHub repo URL from coryebert to BrandedTamarasu-glitch during verification

metrics:
  duration: 1067
  tasks: 3
  commits: 3
  files_created: 1
  files_modified: 1
  completed: 2026-02-16
---

# Phase 38 Plan 02: Update Notification UI Summary

**Full-width VS Code-style update banner with Download/Remind/Dismiss buttons, Settings Updates section with manual check and auto-check toggle, all integrated into MainWindow via background threading.**

## Performance

- **Duration:** 17 min 47 sec
- **Started:** 2026-02-16T15:04:08Z (first commit: 6d4672f)
- **Completed:** 2026-02-16T15:21:55Z (last commit: c026919)
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 2

## Accomplishments

- **Update notification banner** displays full-width at top of app when update available, with Download (opens browser), Remind Later (7d suppress), and X (24h suppress) buttons
- **Background update check** runs on app launch via daemon thread, app loads immediately without blocking
- **Settings Updates section** shows current version, last check time, status, manual Check for Updates button with inline feedback, and auto-check toggle
- **Network failure handling** shows subtle status indicator in Settings (no error dialog crash)
- **Per-version suppression** ensures new versions always show even if older dismissed

## Task Commits

Each task was committed atomically:

1. **Task 1: Create UpdateBanner widget and integrate into main_window** - `6d4672f` (feat)
   - Created UpdateBanner CTkFrame with blue/teal accent, 4-column grid layout
   - Modified MainWindow grid from 2-row to 3-row layout (header, banner slot, content)
   - Added UpdateChecker instance, background thread launch, queue message handling
   - Implemented _show_update_banner and _dismiss_update methods

2. **Task 2: Add Updates section to Settings tab** - `02e7959` (feat)
   - Added Updates section before API Key Settings with title and visual separator
   - Display current version, last check time (relative format), and status (color-coded)
   - Manual Check for Updates button with inline feedback (Checking... -> result)
   - Auto-check toggle persists preference via UpdateChecker.set_auto_check()
   - Guard all Settings widget updates with null checks for lazy tab building

3. **Task 3: Verify update notification flow** - Human verification checkpoint (approved)
   - User tested banner display, dismiss/remind behavior, Settings integration
   - Fixed GitHub API URL during verification: `c026919` (fix)

## Files Created/Modified

### Created
- `job_radar/gui/update_banner.py` - UpdateBanner CTkFrame widget
  - Full-width banner with blue/teal accent color (light/dark mode support)
  - Message label: "Version X.Y.Z available" in white text
  - Download button opens GitHub Releases page via webbrowser.open()
  - Remind Later button dismisses for 7 days (168 hours)
  - X button dismisses for 24 hours
  - Grid layout with expanding message column and 3 fixed-width button columns

### Modified
- `job_radar/gui/main_window.py` - Banner integration and Settings Updates section
  - Modified grid layout from 2 rows to 3 rows (header at row 0, banner slot at row 1, content at row 2)
  - Added UpdateChecker instance and _manual_check_pending flag
  - Added _start_update_check() method: launches background check if should_check() returns True
  - Extended _check_queue() to handle update_available, up_to_date, check_failed messages
  - Added _show_update_banner() to create banner at row 1 with dismiss/remind callbacks
  - Added _dismiss_update() to call UpdateChecker.dismiss_version() and destroy banner
  - Added Updates section to Settings tab with status label, manual check button, auto-check toggle
  - Added _on_manual_check_click() to trigger background check and set pending flag
  - Added _on_auto_check_toggle() to persist user preference
  - Added _refresh_update_status_initial() to populate status on Settings tab build
  - Manual check results update button text ("Checking..." -> "Up to date!" / "Update available!" / "Check failed") and status label, reset button text after 3 seconds

- `job_radar/update_checker.py` - Corrected GitHub repo URL
  - Changed from coryebert/Job-Radar to BrandedTamarasu-glitch/Job-Radar

## Decisions Made

1. **Blue/teal accent color for banner**
   - Rationale: Matches VS Code update notification style, non-intrusive but visible
   - Implementation: `fg_color=("#3498DB", "#2874A6")` for light/dark mode support

2. **Updates section placement before API Key Settings**
   - Rationale: Version updates more important to users than API configuration
   - Impact: Better UX, updates prominently displayed

3. **Banner only on launch checks, inline feedback for manual checks**
   - Rationale: Manual check initiated by user, inline feedback more appropriate than banner
   - Implementation: _manual_check_pending flag distinguishes launch vs manual check

4. **Reset manual check button text after 3 seconds**
   - Rationale: Clean UI, avoids stuck button text states
   - Implementation: `self.after(3000, lambda: ...)` to restore default text

5. **Guard Settings widget updates with null checks**
   - Rationale: Settings tab is lazily built (only on first access), widgets may not exist
   - Implementation: `if self._manual_check_button is not None:` before updates

6. **GitHub repo URL correction**
   - Found during human verification: API URL pointed to wrong repo
   - Corrected from coryebert/Job-Radar to BrandedTamarasu-glitch/Job-Radar
   - Committed as separate fix (c026919)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected GitHub API repository URL**
- **Found during:** Task 3 (Human verification checkpoint)
- **Issue:** UpdateChecker was querying `/repos/coryebert/Job-Radar/releases/latest` instead of correct repository `BrandedTamarasu-glitch/Job-Radar`, causing API 404 errors
- **Fix:** Changed repository URL in update_checker.py from coryebert to BrandedTamarasu-glitch
- **Files modified:** job_radar/update_checker.py
- **Verification:** User confirmed update check now works correctly, shows actual releases
- **Committed in:** c026919 (fix)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential correction for functionality. Update checker would not work without correct repository URL.

## Issues Encountered

None during implementation. The plan was clear and complete. Human verification revealed the repository URL bug which was fixed immediately.

## User Setup Required

None - no external service configuration required. Update check uses public GitHub Releases API (no authentication needed).

## Next Phase Readiness

**Ready for Plan 03 or Phase 40 (Auto-Update Installation):**
- Update detection and notification flow complete
- Banner UI established with clear action buttons
- Settings integration provides user control over update behavior
- Background threading pattern in place for future download worker
- UpdateBanner widget can be reused/extended for download progress display

**No blockers.**

## Self-Check: PASSED

✅ Created files exist:
- `/home/corye/Claude/Job-Radar/job_radar/gui/update_banner.py` - FOUND

✅ Modified files exist:
- `/home/corye/Claude/Job-Radar/job_radar/gui/main_window.py` - FOUND
- `/home/corye/Claude/Job-Radar/job_radar/update_checker.py` - FOUND

✅ Commits exist:
- `6d4672f` (Task 1: UpdateBanner widget) - FOUND
- `02e7959` (Task 2: Settings Updates section) - FOUND
- `c026919` (Fix: GitHub API URL) - FOUND

✅ Imports work:
- `from job_radar.gui.update_banner import UpdateBanner` - SUCCESS
- `from job_radar.gui.main_window import MainWindow` - SUCCESS

✅ Must-haves verified:
- Full-width blue/teal banner above all content: ✅
- Banner shows version, Download, Remind Later, X buttons: ✅
- Download opens GitHub Releases in browser: ✅
- X dismisses for 24h, Remind Later for 7d: ✅
- Background check on launch via thread: ✅
- Settings Updates section with version, last check, status: ✅
- Check for Updates button with inline feedback: ✅
- Auto-check toggle persists preference: ✅
- Network failures show subtle indicator in Settings: ✅
- All key_links present: ✅

✅ Human verification approved:
- User confirmed banner appearance, dismiss/remind behavior, Settings functionality
- GitHub API URL bug found and fixed during verification
- All flows working as expected

---
*Phase: 38-auto-update-foundation*
*Completed: 2026-02-16*
