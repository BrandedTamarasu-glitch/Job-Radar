# Phase 36: GUI Uninstall Feature - Research

**Researched:** 2026-02-14
**Domain:** Desktop GUI application uninstallation with Python
**Confidence:** HIGH

## Summary

This phase implements a complete GUI-driven uninstall feature for the Job Radar desktop application. The research confirms that Python's standard library provides robust tools for file/directory deletion (shutil.rmtree), backup creation (zipfile), and platform detection (sys.platform). CustomTkinter already provides modal dialog patterns used elsewhere in the codebase. The key technical challenge is platform-specific binary deletion for running applications, which requires two-stage cleanup approaches on all platforms.

The application currently uses platformdirs for user data storage, stores multiple file types (profile.json, config.json, SQLite rate limit databases, HTTP cache), and runs as a PyInstaller bundle on macOS/Windows/Linux. The uninstall feature must handle deletion while the app is running, which is technically impossible for the executable itself—requiring cleanup scripts that execute after the app quits.

**Primary recommendation:** Use shutil.rmtree with custom error handlers for best-effort deletion, zipfile for backup, tkinter.filedialog for save location picker, and platform-specific cleanup scripts (AppleScript on macOS, batch file on Windows, shell script on Linux) for binary deletion after quit.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| shutil | stdlib | Directory deletion with error handling | Built-in, cross-platform, widely used for recursive deletion |
| zipfile | stdlib | Create backup archives | Built-in, supports compression, mature API |
| pathlib | stdlib | Path manipulation | Modern Python standard for file paths |
| tkinter.filedialog | stdlib | Native file picker dialogs | Built-in, platform-native dialogs |
| customtkinter | current | Modal confirmation dialogs | Already in use, provides modern UI components |
| platformdirs | current | User data directory resolution | Already in use for get_data_dir() |
| sys | stdlib | Platform detection, executable path | Built-in, reliable for frozen app detection |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| send2trash | 1.8+ | Move to Trash/Recycle Bin | Optional enhancement for binary deletion (better UX than manual instructions) |
| tempfile | stdlib | Atomic file operations | For safe .env writing (already in use) |
| subprocess | stdlib | Execute cleanup scripts | For running platform-specific deletion scripts |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| shutil.rmtree | os.walk + os.remove | shutil.rmtree is higher-level and handles edge cases better |
| zipfile | tarfile | ZIP is more familiar to users, better Windows support |
| tkinter.filedialog | CTk custom file picker | No CustomTkinter native file picker exists, tkinter dialogs integrate fine |
| subprocess scripts | send2trash | send2trash cleaner but still can't delete running executable on Windows |

**Installation:**
```bash
# Core libraries are stdlib (no installation needed)
# Optional enhancement:
pip install send2trash
```

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── gui/
│   ├── main_window.py         # Add uninstall button to Settings tab
│   └── uninstall_dialog.py    # NEW: Modal dialogs for uninstall flow
├── paths.py                    # Already has get_data_dir()
└── uninstaller.py              # NEW: Core uninstall logic (delete, backup, cleanup script)
```

### Pattern 1: Multi-Stage Confirmation Flow
**What:** Two-step dialog confirmation prevents accidental uninstall
**When to use:** Destructive operations that cannot be undone
**Example:**
```python
# Stage 1: Backup offer + path preview
backup_result = show_backup_dialog()
if backup_result == "cancel":
    return

# Stage 2: Final confirmation with checkbox
if not show_final_confirmation():
    return

# Execute uninstall
perform_uninstall()
```

### Pattern 2: Best-Effort Deletion with Error Collection
**What:** Continue deleting files even if some fail, collect errors for user report
**When to use:** Uninstall operations where partial deletion is better than failing completely
**Example:**
```python
# Source: https://docs.python.org/3/library/shutil.html
import shutil
from pathlib import Path

failed_paths = []

def on_error(func, path, exc_info):
    """Error handler collects failures without stopping deletion."""
    failed_paths.append((path, exc_info[1]))

shutil.rmtree(data_dir, onerror=on_error)

if failed_paths:
    # Report partial failure to user
    show_partial_failure_dialog(failed_paths)
```

### Pattern 3: Platform-Specific Binary Cleanup
**What:** Use platform detection to generate appropriate cleanup script
**When to use:** Deleting running executable (impossible while running)
**Example:**
```python
# Source: PyInstaller runtime detection pattern
import sys
import subprocess
from pathlib import Path

if getattr(sys, 'frozen', False):
    exe_path = Path(sys.executable)

    if sys.platform == 'darwin':
        # macOS: AppleScript to move to Trash after quit
        create_macos_cleanup_script(exe_path)
    elif sys.platform == 'win32':
        # Windows: Batch file that waits then deletes
        create_windows_cleanup_script(exe_path)
    else:
        # Linux: Shell script with delay
        create_linux_cleanup_script(exe_path)
```

### Pattern 4: ZIP Backup with User-Selected Location
**What:** Create ZIP of profile+config with native file picker for save location
**When to use:** Before destructive operations where user might want data later
**Example:**
```python
# Sources:
# - https://docs.python.org/3/library/zipfile.html
# - https://docs.python.org/3/library/dialog.html
import zipfile
from tkinter import filedialog
from pathlib import Path

def create_backup(data_dir: Path):
    # Native file picker for save location
    save_path = filedialog.asksaveasfilename(
        title="Save Backup",
        defaultextension=".zip",
        filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
        initialfile="job-radar-backup.zip"
    )

    if not save_path:
        return None  # User cancelled

    # Create ZIP with profile and config
    with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        profile_path = data_dir / "profile.json"
        config_path = data_dir / "config.json"

        if profile_path.exists():
            zf.write(profile_path, arcname="profile.json")
        if config_path.exists():
            zf.write(config_path, arcname="config.json")

    return save_path
```

### Pattern 5: Modal Dialog with Checkbox Confirmation
**What:** Checkbox must be checked before destructive button activates
**When to use:** Final confirmation step for irreversible operations
**Example:**
```python
# Source: Existing pattern in main_window.py _show_error_dialog
import customtkinter as ctk

class FinalConfirmationDialog(ctk.CTkToplevel):
    def __init__(self, parent, paths_to_delete):
        super().__init__(parent)
        self.title("Confirm Uninstall")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()

        self.result = False

        # List of paths with descriptions
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        for path, desc in paths_to_delete:
            label = ctk.CTkLabel(scroll, text=f"{path} - {desc}")
            label.pack(anchor="w", pady=2)

        # Checkbox to enable confirmation
        self.confirm_var = ctk.BooleanVar(value=False)
        checkbox = ctk.CTkCheckBox(
            self,
            text="I understand this cannot be undone",
            variable=self.confirm_var,
            command=self._update_button_state
        )
        checkbox.pack(pady=(10, 5))

        # Uninstall button (disabled until checkbox checked)
        self.uninstall_btn = ctk.CTkButton(
            self,
            text="Uninstall",
            state="disabled",
            fg_color="red",
            hover_color="darkred",
            command=self._on_confirm
        )
        self.uninstall_btn.pack(pady=5)

        # Cancel button
        cancel_btn = ctk.CTkButton(
            self,
            text="Cancel",
            command=self._on_cancel
        )
        cancel_btn.pack(pady=5)

    def _update_button_state(self):
        if self.confirm_var.get():
            self.uninstall_btn.configure(state="normal")
        else:
            self.uninstall_btn.configure(state="disabled")

    def _on_confirm(self):
        self.result = True
        self.destroy()

    def _on_cancel(self):
        self.result = False
        self.destroy()
```

### Anti-Patterns to Avoid
- **Silent deletion failures:** Always report what couldn't be deleted so user can manually clean up
- **Blocking the GUI thread:** Use threading or after() for potentially slow deletion operations
- **Deleting executable first:** Data deletion must happen before app quits; binary deletion happens after
- **Hardcoded paths:** Always use get_data_dir() and platform detection for cross-platform support

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Recursive directory deletion | Custom os.walk loop | shutil.rmtree | Handles permissions, symlinks, locked files |
| ZIP file creation | Manual file copying | zipfile module | Handles compression, directory structure, edge cases |
| File picker dialogs | Custom CTk dialog | tkinter.filedialog | Platform-native appearance, handles edge cases |
| Platform detection | Parsing uname output | sys.platform | Reliable, works in frozen apps |
| Modal dialogs | Custom focus management | CTkToplevel + transient/grab_set | Existing pattern in codebase |
| Atomic file writes | Direct overwrite | tempfile + Path.replace | Prevents corruption on error (already used for .env) |

**Key insight:** The Python standard library already handles the complexity of cross-platform file operations. The only area requiring custom code is platform-specific cleanup scripts for binary deletion, which cannot use standard libraries because the app will have already quit.

## Common Pitfalls

### Pitfall 1: Deleting Running Executable
**What goes wrong:** Operating systems prevent deletion of running executables (Windows locks file, macOS keeps .app in use)
**Why it happens:** File handle is held open by the OS while process runs
**How to avoid:** Two-stage cleanup—delete data while running, spawn cleanup script for binary deletion after quit
**Warning signs:** PermissionError on sys.executable deletion, "file in use" errors on Windows

### Pitfall 2: Ignoring Deletion Errors
**What goes wrong:** Silent failures leave data behind, user thinks uninstall completed
**Why it happens:** Using ignore_errors=True without tracking what failed
**How to avoid:** Use custom error handler to collect failures, report to user with specific paths
**Warning signs:** Users reporting "uninstalled but files still there"

### Pitfall 3: Backup Including Large Temp Data
**What goes wrong:** Backup ZIP becomes huge from cache/rate limit databases
**Why it happens:** Including entire data directory instead of just user data
**How to avoid:** Explicitly backup only profile.json and config.json (user's actual configuration)
**Warning signs:** Backup taking long time, large ZIP files

### Pitfall 4: Modal Dialog Not Actually Modal
**What goes wrong:** User can click elsewhere while confirmation dialog is open
**Why it happens:** Forgetting transient() or grab_set() calls
**How to avoid:** Use established pattern: dialog.transient(parent) + dialog.grab_set()
**Warning signs:** Clicking parent window while dialog is open works

### Pitfall 5: Cleanup Script Still Running After App Quits
**What goes wrong:** User sees lingering terminal windows or processes
**Why it happens:** Not using background/detached mode for cleanup scripts
**How to avoid:** Use platform-specific background execution (& on Unix, START /B on Windows)
**Warning signs:** Terminal windows remaining after app quit

### Pitfall 6: Rate Limit Database Locks
**What goes wrong:** SQLite database files can't be deleted while connections open
**Why it happens:** rate_limits.py keeps connections in _connections dict
**How to avoid:** Call rate_limits._cleanup_connections() before deletion, or rely on atexit handler
**Warning signs:** PermissionError on .rate_limits/*.db files

### Pitfall 7: Cross-Platform Path Separators
**What goes wrong:** Hardcoded / or \ in paths breaks on different OS
**Why it happens:** Not using pathlib.Path for path construction
**How to avoid:** Use Path objects throughout, let pathlib handle separators
**Warning signs:** Paths work on dev machine but fail on different OS

## Code Examples

Verified patterns from official sources:

### File Deletion with Error Handling
```python
# Source: https://docs.python.org/3/library/shutil.html
import shutil
from pathlib import Path

def delete_data_with_errors() -> list[tuple[str, Exception]]:
    """Delete data directory, return list of failures."""
    data_dir = get_data_dir()
    failed = []

    def on_error(func, path, exc_info):
        failed.append((path, exc_info[1]))

    if data_dir.exists():
        shutil.rmtree(data_dir, onerror=on_error)

    return failed
```

### Creating Backup ZIP
```python
# Source: https://docs.python.org/3/library/zipfile.html
import zipfile
from pathlib import Path

def create_backup_zip(save_path: str, data_dir: Path) -> None:
    """Create ZIP backup of user data (profile + config only)."""
    with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_name in ['profile.json', 'config.json']:
            file_path = data_dir / file_name
            if file_path.exists():
                zf.write(file_path, arcname=file_name)
```

### Platform-Specific Binary Path Detection
```python
# Source: https://pyinstaller.org/en/stable/runtime-information.html
import sys
from pathlib import Path

def get_binary_path() -> Path | None:
    """Get path to executable binary if running frozen, else None."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys.executable)
    return None
```

### macOS Cleanup Script Generation
```python
def create_macos_cleanup_script(exe_path: Path) -> Path:
    """Create AppleScript to move app to Trash after delay."""
    script_content = f'''
    delay 2
    do shell script "osascript -e 'tell application \\"Finder\\" to delete POSIX file \\"{exe_path}\\"'"
    '''

    script_path = Path.home() / ".job-radar-cleanup.scpt"
    script_path.write_text(script_content)

    # Execute in background
    import subprocess
    subprocess.Popen(['osascript', str(script_path)],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL,
                     start_new_session=True)

    return script_path
```

### Windows Cleanup Script Generation
```python
def create_windows_cleanup_script(exe_path: Path) -> Path:
    """Create batch file to delete exe after delay."""
    script_content = f'''
    @echo off
    timeout /t 3 /nobreak > nul
    del /f /q "{exe_path}"
    del "%~f0"
    '''

    script_path = Path.home() / "job-radar-cleanup.bat"
    script_path.write_text(script_content)

    # Execute in background
    import subprocess
    subprocess.Popen(['cmd', '/c', 'start', '/b', str(script_path)],
                     creationflags=subprocess.CREATE_NO_WINDOW)

    return script_path
```

### Linux Cleanup Script Generation
```python
def create_linux_cleanup_script(exe_path: Path) -> Path:
    """Create shell script to delete binary after delay."""
    script_content = f'''#!/bin/bash
    sleep 3
    rm -f "{exe_path}"
    rm -f "$0"
    '''

    script_path = Path.home() / ".job-radar-cleanup.sh"
    script_path.write_text(script_content)
    script_path.chmod(0o755)

    # Execute in background
    import subprocess
    subprocess.Popen(['/bin/bash', str(script_path)],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL,
                     start_new_session=True)

    return script_path
```

### Progress Dialog During Deletion
```python
import customtkinter as ctk

class DeletionProgressDialog(ctk.CTkToplevel):
    """Modal progress dialog shown during deletion."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Uninstalling...")
        self.geometry("400x150")
        self.transient(parent)
        self.grab_set()

        # Prevent closing
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.label = ctk.CTkLabel(
            self,
            text="Deleting application data...",
            font=ctk.CTkFont(size=14)
        )
        self.label.pack(pady=30)

        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.pack(pady=10)
        self.progress.start()

    def update_status(self, message: str):
        """Update status message."""
        self.label.configure(text=message)
        self.update()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual file paths | platformdirs | Job Radar v1.0+ | Cross-platform user data location |
| os.path | pathlib | Python 3.4+ | Cleaner path operations |
| onerror parameter | onexc parameter (shutil.rmtree) | Python 3.12 | Better error handling API |
| Manual modal focus | CTkToplevel pattern | CustomTkinter established | Consistent modal dialogs |
| send2trash for Windows | Native batch script | Windows 10+ | More control over deletion timing |

**Deprecated/outdated:**
- **os.path for path manipulation:** Use pathlib.Path for modern path operations
- **Manual directory traversal:** Use shutil.rmtree instead of os.walk + os.remove
- **Blocking sleep in main thread:** Use after() or threading for delays

## Open Questions

1. **Should we use send2trash for binary deletion on macOS?**
   - What we know: send2trash can move .app bundles to Trash, cleaner than manual deletion
   - What's unclear: Whether it works reliably on running .app bundles (may still fail)
   - Recommendation: Test with PyInstaller .app bundle; if it works, use it; otherwise fall back to manual instructions

2. **How to handle .env file deletion?**
   - What we know: .env lives in CWD, not data directory; may contain API keys user wants to keep
   - What's unclear: Whether uninstall should touch .env or leave it (it's technically not app data)
   - Recommendation: Leave .env alone—it's user configuration for their development environment, not app-specific data

3. **Should we delete the log file (~/job-radar-error.log)?**
   - What we know: Error log lives in home directory, separate from app data
   - What's unclear: Whether users expect uninstall to remove logs
   - Recommendation: Include in deletion since it's app-specific data, show in path preview dialog

4. **What if user has custom config.json path via --config flag?**
   - What we know: Config can be loaded from custom paths, but GUI doesn't use this feature
   - What's unclear: Whether GUI should detect/warn about configs outside data directory
   - Recommendation: Ignore—GUI only uses default path, custom configs are CLI-only feature

## Sources

### Primary (HIGH confidence)
- [Python shutil documentation](https://docs.python.org/3/library/shutil.html) - rmtree error handling, file operations
- [Python zipfile documentation](https://docs.python.org/3/library/zipfile.html) - ZIP archive creation patterns
- [Python tkinter.filedialog documentation](https://docs.python.org/3/library/dialog.html) - Native file picker dialogs
- [PyInstaller runtime information](https://pyinstaller.org/en/stable/runtime-information.html) - Frozen app detection, sys.executable behavior
- Existing codebase: /Users/coryebert/Job-Radar/job_radar/gui/main_window.py - Modal dialog pattern (lines 744-774, 1376-1407)
- Existing codebase: /Users/coryebert/Job-Radar/job_radar/paths.py - Platform-specific data directory resolution
- Existing codebase: /Users/coryebert/Job-Radar/job_radar/rate_limits.py - SQLite connection cleanup pattern (lines 133-174)

### Secondary (MEDIUM confidence)
- [Send2Trash PyPI](https://pypi.org/project/Send2Trash/) - Cross-platform trash/recycle bin library
- [Send2Trash GitHub](https://github.com/arsenetar/send2trash) - macOS FSMoveObjectToTrashSync implementation
- [Delete directory recursively guide](https://note.nkmk.me/en/python-os-remove-rmdir-removedirs-shutil-rmtree/) - shutil.rmtree patterns
- [Python ZIP file backups guide](https://coderslegacy.com/python/problem-solving/how-to-create-zip-file-backups-in-python/) - Practical backup patterns
- [tkinter asksaveasfilename guide](https://likegeeks.com/tkinter-filedialog-asksaveasfilename/) - File picker best practices

### Tertiary (LOW confidence)
- [Self-deleting Python executables Gist](https://gist.github.com/0xdade/272afa7fe0446acbe0303b03b2ef34ba) - Patterns for PyInstaller self-deletion (approach may be outdated)
- Various StackOverflow/forum discussions on Windows executable self-deletion (marked for validation)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified in official documentation, existing codebase uses them
- Architecture: HIGH - Patterns verified in PyInstaller docs and existing GUI code
- Pitfalls: HIGH - Based on documented shutil behavior, PyInstaller limitations, OS file locking

**Research date:** 2026-02-14
**Valid until:** ~60 days (stable domain—file operations and GUI patterns don't change rapidly)

**Key dependencies identified:**
- platformdirs (already installed) - User data directory resolution
- customtkinter (already installed) - Modal dialog UI components
- PyInstaller (already in use) - Frozen app detection and binary path resolution
- Standard library modules (shutil, zipfile, tkinter, sys, pathlib, subprocess) - Core functionality

**Platform-specific considerations:**
- macOS: .app bundles are directories, can use send2trash or AppleScript for Trash
- Windows: Executable file locking prevents deletion while running, batch script required
- Linux: Standard rm works after delay, shell script with start_new_session=True

**Integration points with existing codebase:**
- Settings tab in main_window.py: Add "Uninstall Job Radar" button
- get_data_dir() in paths.py: Already provides cross-platform data directory path
- Modal dialog pattern: Matches _show_error_dialog and _show_info_dialog patterns
- rate_limits._cleanup_connections(): Must be called before deleting .rate_limits/
