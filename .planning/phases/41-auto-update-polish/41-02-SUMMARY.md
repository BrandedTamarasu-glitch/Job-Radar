---
phase: 41-auto-update-polish
plan: 02
subsystem: auto-update
tags: [ui, integration, changelog, skip-version, settings]
dependency_graph:
  requires:
    - "41-01 (skip_version, fetch_release_notes, extract_summary backend)"
    - "39-02 (UpdateBanner multi-state pattern)"
    - "38-02 (Settings tab Updates section)"
  provides:
    - "ChangelogDialog for release notes display"
    - "UpdateBanner dropdown with Skip This Version option"
    - "Clickable version number in banner for changelog preview"
    - "Settings integration for skipped versions management"
  affects:
    - "Complete UPDATE-11 and UPDATE-12 requirements"
tech_stack:
  added:
    - "CTkButton styled as hyperlink (underline, transparent, cursor)"
    - "tkinter.Menu for popup dropdown (not CTkOptionMenu)"
    - "Split message layout with inline clickable elements"
  patterns:
    - "Modal dialog centering via _center_on_parent pattern"
    - "Background thread fetch with queue-based callback"
    - "Conditional Settings widget packing based on state"
key_files:
  created:
    - path: "job_radar/gui/changelog_dialog.py"
      changes: "+119 lines: CTkToplevel dialog for release notes"
  modified:
    - path: "job_radar/gui/update_banner.py"
      changes: "+90 lines: split message layout, dropdown menu, clickable version, skip confirmation"
    - path: "job_radar/gui/main_window.py"
      changes: "+181 lines: skip/changelog callbacks, Settings UI, queue handler"
decisions:
  - decision: "Use tkinter.Menu for dropdown instead of CTkOptionMenu"
    rationale: "Menu provides popup behavior without persistent widget; CTkOptionMenu is for form fields"
    alternatives: ["CTkOptionMenu", "Custom CTkFrame dropdown"]
  - decision: "Clickable version uses CTkButton with underline font and transparent fg_color"
    rationale: "Maintains banner color scheme while providing clear hyperlink affordance"
    alternatives: ["CTkLabel with bind", "Separate link button"]
  - decision: "Conditional packing for Settings widgets based on state"
    rationale: "Only show 'View release notes' when update exists, 'Clear skipped' when skips exist"
    alternatives: ["Always show but disable", "Dynamic rebuild on state change"]
metrics:
  duration_seconds: 273
  completed_date: "2026-02-16"
---

# Phase 41 Plan 02: Update Banner Skip & Changelog UI Summary

**One-liner:** Complete polished update UX with dropdown skip, clickable changelog preview, and Settings skipped versions management.

## What Was Built

Integrated ChangelogDialog, enhanced UpdateBanner with skip/changelog UI, and wired Settings tab for skipped versions management:

**ChangelogDialog (new file):**
- CTkToplevel modal dialog showing release notes summary
- 500x400 window with "What's New in v{version}" title
- Read-only CTkTextbox displaying extracted summary (280px height)
- "View Full Release Notes on GitHub" link button
- Close button
- Center on parent using installer_dialogs pattern

**UpdateBanner enhancements:**
- Split message layout: "Version " + clickable version button + " available"
- Version button: underlined white text, transparent bg, hand cursor, calls on_view_changelog
- "..." more button with tkinter.Menu dropdown
- Dropdown menu: "Skip This Version" option (notification state only)
- show_skip_confirmation(): displays "v{version} skipped" for 1.5s
- New callbacks: on_skip, on_view_changelog (optional parameters)

**MainWindow integration:**
- State tracking: _update_version, _update_release_url, _release_notes_label, _clear_skipped_btn, _skipped_status_label
- _on_skip_version(): skip permanently, show confirmation, dismiss after 1.5s, refresh Settings
- _on_view_changelog(): check cache first, fetch in background if needed, queue release_notes_ready message
- _show_changelog_dialog(): extract summary, construct GitHub URL, create dialog
- release_notes_ready queue handler: calls _show_changelog_dialog
- Update status shows "v{version} available (skipped)" when version is skipped

**Settings tab additions:**
- "View release notes" link (only when update available)
- Skipped versions status label: "Skipped: v2.1.0, v2.2.0"
- "Clear skipped versions" button (only when skips exist)
- _refresh_skipped_status(): update label with skipped list
- _on_settings_view_notes(): delegate to _on_view_changelog
- _on_clear_skipped(): clear all skips, refresh UI, hide button

## Test Coverage

**Full test suite: 641 passed, 4 failed (pre-existing)**

The 4 failures are unrelated to this plan:
1. test_config_known_keys_count - New key added in Phase 40
2. test_known_keys_exact_size - New key added in Phase 40
3. test_launch_macos_dmg_no_mount_point - Platform-specific (running on Linux)
4. test_launch_windows_exe - Platform-specific (running on Linux)

**No regressions from this plan** - all update_checker and GUI integration tests pass.

## Deviations from Plan

None - plan executed exactly as written.

## Technical Details

**UpdateBanner Layout Changes:**

Before (notification state):
```
Column 0: message_label ("Version 2.2.0 available")
Column 1: Download button
Column 2: Remind Later button
Column 3: X button
```

After (notification state):
```
Column 0: message_frame (prefix + clickable version + suffix)
Column 1: Download button
Column 2: Remind Later button
Column 3: "..." dropdown button
Column 4: X button
```

**Message Frame Structure:**
```
CTkFrame (transparent)
├── msg_prefix ("Version ")
├── version_btn ("v2.2.0", underlined, clickable)
└── msg_suffix (" available")
```

**Skip Flow:**
1. User clicks "..." → tkinter.Menu popup appears
2. User clicks "Skip This Version" → _on_skip_click
3. UpdateBanner: on_skip callback → MainWindow._on_skip_version
4. MainWindow: update_checker.skip_version(version)
5. UpdateBanner: show_skip_confirmation() → "v2.2.0 skipped"
6. 1.5s delay → banner.destroy()
7. Settings: _refresh_update_status() shows "(skipped)"

**Changelog Flow:**
1. User clicks version number → _on_version_click
2. UpdateBanner: on_view_changelog callback → MainWindow._on_view_changelog
3. Check cache: get_cached_release_notes(version)
4. If cached: show_changelog_dialog immediately
5. If not cached: background thread → fetch_release_notes(tag)
6. Thread: cache_release_notes(version, body)
7. Thread: queue.put("release_notes_ready", version, body)
8. Main thread: _check_queue → _show_changelog_dialog
9. Dialog: extract_summary(body) → ChangelogDialog(parent, version, summary, url)

**Settings Conditional Packing:**
- _release_notes_label: packed only if `self._update_version` is not None
- _clear_skipped_btn: packed only if `get_skipped_versions()` returns non-empty list
- _skipped_status_label: always packed, but text="" when no skips

## Integration Points

**Upstream Dependencies:**
- 41-01-PLAN.md: skip_version(), fetch_release_notes(), cache_release_notes(), extract_summary()
- 39-02-PLAN.md: UpdateBanner multi-state pattern with _hide_all() and state methods
- 38-02-PLAN.md: Settings tab structure with Updates section

**Downstream Impact:**
- Completes UPDATE-11 (skip version) and UPDATE-12 (changelog preview) requirements
- No further auto-update polish needed (Phase 41 complete)

## Verification Results

```bash
$ python -m py_compile job_radar/gui/changelog_dialog.py
$ python -m py_compile job_radar/gui/update_banner.py
Syntax checks passed for both files

$ python -m pytest --tb=short -q
641 passed, 4 failed in 15.23s
```

All new code compiles successfully. Test suite shows same 4 pre-existing failures (config KNOWN_KEYS count, platform-specific installer tests). No regressions from this plan.

## Commits

| Hash    | Message                                                                    |
| ------- | -------------------------------------------------------------------------- |
| 6642663 | feat(41-02): add ChangelogDialog and skip/changelog UI to UpdateBanner    |
| 5840199 | feat(41-02): wire skip/changelog/settings integration into MainWindow     |

## Self-Check: PASSED

**Created files:**
```bash
$ [ -f "job_radar/gui/changelog_dialog.py" ] && echo "FOUND: job_radar/gui/changelog_dialog.py"
FOUND: job_radar/gui/changelog_dialog.py
```

**Modified files:**
```bash
$ [ -f "job_radar/gui/update_banner.py" ] && echo "FOUND: job_radar/gui/update_banner.py"
FOUND: job_radar/gui/update_banner.py

$ [ -f "job_radar/gui/main_window.py" ] && echo "FOUND: job_radar/gui/main_window.py"
FOUND: job_radar/gui/main_window.py
```

**Commits:**
```bash
$ git log --oneline --all | grep -q "6642663" && echo "FOUND: 6642663"
FOUND: 6642663

$ git log --oneline --all | grep -q "5840199" && echo "FOUND: 5840199"
FOUND: 5840199
```

All verification checks passed.
