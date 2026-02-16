---
phase: 40-auto-update-installation
plan: 01
subsystem: auto-update
tags: [installer, subprocess, platform-specific, dialogs, GUI]
dependencies:
  requires:
    - "39-01: DownloadWorker with SHA256 verification"
    - "39-02: UpdateBanner with download UI states"
  provides:
    - "launch_installer() function for platform-specific installer launching"
    - "cleanup_old_installers() function for temp directory cleanup"
    - "InstallConfirmDialog for pre-install confirmation"
    - "LinuxInstallInstructionsDialog for Linux tar.gz extraction"
  affects:
    - "job_radar/update_checker.py: Added installer launch and cleanup functions"
    - "job_radar/gui/installer_dialogs.py: New dialog module"
tech_stack:
  added:
    - subprocess: Platform-specific process launching (macOS hdiutil, Windows Popen)
    - tkinter.clipboard: Clipboard operations for Linux Copy Command button
  patterns:
    - Platform detection via sys.platform checks
    - CTkToplevel modal dialogs with transient/grab_set
    - Subprocess timeout and error handling
    - Cleanup on startup pattern (delete old installer files)
key_files:
  created:
    - job_radar/gui/installer_dialogs.py: InstallConfirmDialog and LinuxInstallInstructionsDialog classes
    - tests/test_installer_launch.py: 16 tests covering launch, cleanup, and dialog imports
  modified:
    - job_radar/update_checker.py: Added launch_installer() and cleanup_old_installers()
decisions:
  - decision: "macOS quarantine attribute left intact (trust notarization per 40-RESEARCH)"
    rationale: "Notarized DMGs pass Gatekeeper, stripping xattr unnecessary and reduces security"
  - decision: "Windows uses DETACHED_PROCESS and CREATE_NEW_PROCESS_GROUP flags"
    rationale: "Allows installer to run independently after app closes, prevents premature termination"
  - decision: "Linux raises RuntimeError instead of launching installer"
    rationale: "Linux uses instructions dialog flow, not direct launch like macOS/Windows"
  - decision: "Cleanup old installers on startup, not immediately after launch"
    rationale: "Avoids race condition where installer process hasn't read file yet"
  - decision: "Use tkinter clipboard instead of pyperclip"
    rationale: "No external dependency required, tkinter clipboard methods sufficient for copy functionality"
metrics:
  duration: 221
  tasks_completed: 2
  files_created: 2
  files_modified: 1
  tests_added: 16
  completed_at: "2026-02-16"
---

# Phase 40 Plan 01: Installer Launch Backend & Dialogs Summary

Platform-specific installer launching with subprocess (macOS DMG mount, Windows exe detach, Linux error), cleanup function, and confirmation/instructions dialogs.

## What Was Built

### Core Functions

**launch_installer(installer_path, platform=None) -> str**
- Platform detection from sys.platform if not specified
- macOS: hdiutil attach with mount point parsing (primary + fallback detection), opens in Finder
- Windows: Popen with DETACHED_PROCESS and CREATE_NEW_PROCESS_GROUP flags
- Linux: Raises RuntimeError directing to instructions dialog
- Timeout: 30 seconds on subprocess calls
- Error handling: TimeoutExpired, CalledProcessError, FileNotFoundError, OSError
- Returns: Mount point for macOS, empty string for Windows

**cleanup_old_installers() -> int**
- Globs temp directory for: Job-Radar-v*-installer.dmg, Job-Radar-Setup-v*.exe, job-radar-v*-installer.tar.gz
- Deletes matching files, catches OSError (file in use)
- Returns count of successfully deleted files
- Called on app startup to clean previous session installers

### Dialog Classes

**InstallConfirmDialog(CTkToplevel)**
- Constructor: parent, version, platform_message, on_confirm callback
- Displays: "Ready to install v{version}? The app will close and restart."
- Platform hint in gray: "Opening installer DMG..." / "Launching installer... Windows may show a security prompt."
- Buttons: Cancel (destroys), Install Now (calls on_confirm then destroys)
- Modal: transient + grab_set, centers on parent
- result attribute: True on confirm, None on cancel

**LinuxInstallInstructionsDialog(CTkToplevel)**
- Constructor: parent, tar_path, version
- Displays: tar extraction instructions in CTkTextbox (read-only)
- Commands shown: `tar -xzf {filename} -C ~/Applications/` and custom location variant
- Copy Command button: Uses tkinter clipboard (clipboard_clear, clipboard_append, update)
- Copy feedback: Button text changes to "Copied!" for 2 seconds
- Open Folder button: subprocess.Popen with xdg-open, catches FileNotFoundError gracefully
- Modal: transient + grab_set, centers on parent

## Tests

16 tests added to tests/test_installer_launch.py:

**Launch tests (10):**
- test_launch_macos_dmg_success: Verify hdiutil + open calls, mount point returned
- test_launch_macos_dmg_mount_failure: Verify RuntimeError on non-zero returncode
- test_launch_macos_dmg_no_mount_point: Verify RuntimeError when mount point not found
- test_launch_macos_dmg_timeout: Verify RuntimeError on TimeoutExpired
- test_launch_macos_dmg_fallback_mount_point: Verify fallback /Volumes/{stem} detection
- test_launch_windows_exe: Verify Popen with correct flags
- test_launch_linux_raises: Verify RuntimeError with instructions message
- test_launch_file_not_found: Verify RuntimeError on FileNotFoundError
- test_launch_os_error: Verify RuntimeError on OSError
- test_launch_unsupported_platform: Verify RuntimeError on unknown platform

**Cleanup tests (4):**
- test_cleanup_deletes_matching_files: Verify 3 patterns deleted, others preserved
- test_cleanup_ignores_errors: Verify OSError doesn't raise, returns 0
- test_cleanup_no_files: Verify returns 0 on empty directory
- test_cleanup_multiple_versions: Verify all versions deleted

**Dialog tests (3):**
- test_dialog_stores_attributes: Verify InstallConfirmDialog is importable
- test_dialog_importable: Verify class name correct
- test_linux_dialog_copy_command_format: Verify LinuxInstallInstructionsDialog copy command format

## Deviations from Plan

None - plan executed exactly as written.

## Integration Notes

**For Plan 02 (Wiring into MainWindow/UpdateBanner):**
- UpdateBanner "Install Now" button → MainWindow._on_install_now()
- MainWindow callback sequence:
  1. Show InstallConfirmDialog (or LinuxInstallInstructionsDialog on Linux)
  2. On confirm: call launch_installer(installer_path)
  3. Show brief status message: "Installer launched. Closing app..."
  4. Schedule app exit: self.after(1500, self.destroy)
- MainWindow.__init__ should call cleanup_old_installers() early

**Platform messages for InstallConfirmDialog:**
- macOS: "Opening installer DMG..."
- Windows: "Launching installer... Windows may show a security prompt."
- Linux: Not used (shows LinuxInstallInstructionsDialog instead)

## Success Criteria Met

- [x] launch_installer() correctly dispatches to platform-specific subprocess calls
- [x] macOS: hdiutil attach + open mount point, with fallback detection
- [x] Windows: Popen with DETACHED_PROCESS and CREATE_NEW_PROCESS_GROUP
- [x] Linux: Raises RuntimeError with instructions dialog message
- [x] cleanup_old_installers() removes temp installer files matching patterns
- [x] InstallConfirmDialog is modal CTkToplevel with version, platform hint, buttons
- [x] LinuxInstallInstructionsDialog shows tar instructions with Copy/Open Folder buttons
- [x] Copy Command uses tkinter clipboard (no external dependency)
- [x] 16 tests covering all launch paths, error handling, cleanup, dialog basics
- [x] All code compiles without errors
- [x] Functions are importable

## Self-Check: PASSED

**Created files exist:**
```
FOUND: job_radar/gui/installer_dialogs.py
FOUND: tests/test_installer_launch.py
```

**Modified files exist:**
```
FOUND: job_radar/update_checker.py
```

**Commits exist:**
```
FOUND: db9be13 (Task 1 - launch_installer and cleanup_old_installers)
FOUND: 865a6cf (Task 2 - InstallConfirmDialog and LinuxInstallInstructionsDialog)
```

**Imports verified:**
```
from job_radar.update_checker import launch_installer, cleanup_old_installers  # OK
from job_radar.gui.installer_dialogs import InstallConfirmDialog, LinuxInstallInstructionsDialog  # Syntax OK
```

All claims in summary verified against codebase.
