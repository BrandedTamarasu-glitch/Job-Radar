# Phase 40: Auto-Update Installation - Research

**Researched:** 2026-02-16
**Domain:** Platform-specific installer launching, subprocess management, GUI confirmation flows
**Confidence:** HIGH

## Summary

Phase 40 implements the "Install Now" button functionality that launches platform-specific installers (DMG on macOS, NSIS .exe on Windows, tar.gz instructions on Linux) after download completes. The implementation requires platform-specific subprocess handling, graceful app shutdown sequencing, and robust error handling for edge cases like missing files or launch failures.

The core challenge is coordinating three distinct concerns: (1) platform-specific installer launching using subprocess, (2) proper app exit sequencing to avoid file-in-use conflicts, and (3) error handling for multiple failure modes (SHA256 mismatch, missing files, permission issues). Python's subprocess module provides the foundation, with platform detection already established in the codebase via `sys.platform` checks.

**Primary recommendation:** Use Python's built-in subprocess module with platform-specific command patterns (hdiutil + open for macOS, direct .exe launch for Windows, xdg-open for Linux), implement a two-stage shutdown sequence (brief status message → app.after delay → destroy), and leverage existing CustomTkinter dialog patterns for confirmation/error UI.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Install Now behavior:**
- App auto-closes before launching installer — no conflicts with files in use
- Brief confirmation dialog before closing: "Ready to install v{version}? The app will restart."
- After spawning installer, show brief "Installer launched. Closing app..." status message, then exit
- Downloaded installer file kept until next app start (delete on next launch) — ensures installer had time to read the file

**Platform-specific experience:**
- Platform-specific messages explaining what's about to happen (not generic)
  - macOS: "Opening installer DMG..."
  - Windows: "Launching installer..."
  - Linux: different flow (see Linux handling)
- macOS DMG: mount DMG and open the volume in Finder so user sees drag-to-Applications window
- Windows NSIS: just launch the exe — let Windows show the UAC prompt naturally
- Quarantine handling on macOS: Claude's discretion on whether to strip xattr

**Failure & edge cases:**
- SHA256 mismatch: show Retry button AND "Download manually" link to GitHub releases page
- Missing installer file (temp cleaned up): "Installer file not found. Download again?" — user clicks to re-download
- Installer launch failure (permissions): error message with file path AND retry button — "Couldn't launch installer. File saved at: [path]"
- Trust download-time SHA256 verification — no re-verify before launch

**Linux handling:**
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

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| subprocess | stdlib | Platform-specific process launching | Built-in, cross-platform, robust process control with Popen/run |
| pathlib.Path | stdlib | File path manipulation | Modern Python standard, already used throughout codebase |
| sys | stdlib | Platform detection via sys.platform | Standard approach for OS detection |
| customtkinter | 5.x | Dialog UI (CTkToplevel) | Already integrated, consistent with existing dialogs |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyperclip | 1.x | Clipboard operations | Optional - for Linux "Copy" button in extraction dialog |
| tempfile | stdlib | Temp directory path | Already used for installer download path |
| time.sleep | stdlib | Brief delays | Only if app.after proves insufficient for status message timing |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| subprocess | os.system | os.system less secure, no process control, deprecated |
| subprocess.run | subprocess.Popen | run() is simpler for fire-and-forget, Popen gives more control |
| pyperclip | tkinter clipboard | tkinter clipboard is simpler, no dependency, sufficient for single-text copy |

**Installation:**
```bash
# pyperclip is OPTIONAL - only needed if choosing it over tkinter clipboard
pip install pyperclip  # Linux only, for Copy button
```

**Note:** Pyperclip requires xclip or xsel on Linux, but tkinter's clipboard methods work without additional dependencies. Recommend using tkinter clipboard to avoid external dependency.

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── update_checker.py          # Add launch_installer() method
├── gui/
│   ├── update_banner.py       # Wire Install Now button → MainWindow callback
│   ├── main_window.py         # Implement _on_install_now() → launch + exit
│   └── installer_dialogs.py   # NEW: Install confirmation + Linux instructions dialogs
tests/
└── test_installer_launch.py   # NEW: Platform-specific launch tests
```

### Pattern 1: Platform-Specific Installer Launch

**What:** Use subprocess with platform-specific command patterns, proper process detachment
**When to use:** When spawning installer and immediately exiting parent app

**macOS DMG Pattern:**
```python
# Source: hdiutil man page + macOS subprocess best practices
import subprocess
import sys
from pathlib import Path

def launch_macos_dmg(dmg_path: Path) -> None:
    """Mount DMG and open volume in Finder."""
    # Mount DMG using hdiutil
    result = subprocess.run(
        ["hdiutil", "attach", str(dmg_path)],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        raise RuntimeError(f"DMG mount failed: {result.stderr}")

    # Parse mount point from hdiutil output
    # Output format: "/dev/diskX ... /Volumes/VolumeName"
    lines = result.stdout.strip().split('\n')
    mount_point = None
    for line in lines:
        if '/Volumes/' in line:
            parts = line.split('\t')
            mount_point = parts[-1].strip()
            break

    if not mount_point:
        raise RuntimeError("Could not determine mount point")

    # Open mounted volume in Finder
    subprocess.Popen(["open", mount_point])
```

**Windows NSIS Pattern:**
```python
# Source: Windows subprocess docs
import subprocess
from pathlib import Path

def launch_windows_installer(exe_path: Path) -> None:
    """Launch NSIS installer exe."""
    # Simple launch - Windows handles UAC prompt automatically
    subprocess.Popen([str(exe_path)], creationflags=subprocess.DETACHED_PROCESS)
```

**Linux Instructions Pattern:**
```python
# Source: xdg-open docs + Linux best practices
import subprocess
from pathlib import Path

def open_linux_folder(file_path: Path) -> None:
    """Open containing folder in default file manager."""
    folder = file_path.parent
    subprocess.Popen(["xdg-open", str(folder)])
```

### Pattern 2: Graceful App Exit After Launch

**What:** Two-stage shutdown with visual feedback
**When to use:** When closing app after spawning long-running external process

```python
# Source: CustomTkinter after() best practices
def _on_install_confirmed(self):
    """Launch installer and exit app after brief status message."""
    # Stage 1: Show status message
    self._show_install_status("Installer launched. Closing app...")

    # Stage 2: Launch installer (non-blocking)
    try:
        self._launch_installer(self._installer_path)
    except Exception as e:
        self._show_error(f"Failed to launch installer: {e}")
        return

    # Stage 3: Schedule app exit after brief delay (1-2 seconds)
    self.after(1500, self.destroy)  # 1.5 second delay
```

### Pattern 3: Confirmation Dialog with Cancel Option

**What:** Modal dialog inheriting from CTkToplevel, centered on parent
**When to use:** Pre-action confirmation that allows user to back out

```python
# Source: Existing DownloadConfirmDialog pattern in update_banner.py
class InstallConfirmDialog(ctk.CTkToplevel):
    """Confirm install action before closing app."""

    def __init__(self, parent, version: str, on_confirm: callable):
        super().__init__(parent)
        self.title("Install Update")
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()  # Modal

        # Message
        message = ctk.CTkLabel(
            self,
            text=f"Ready to install v{version}?\nThe app will close.",
            font=CTkFont(size=14)
        )
        message.pack(pady=(30, 20))

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        cancel_btn = ctk.CTkButton(
            button_frame, text="Cancel", width=120,
            command=self.destroy
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        install_btn = ctk.CTkButton(
            button_frame, text="Install Now", width=120,
            command=lambda: (on_confirm(), self.destroy())
        )
        install_btn.pack(side="left")

        # Center on parent
        self.after(10, self._center_on_parent)
```

### Pattern 4: Linux Instructions Dialog with Copy Button

**What:** Dialog showing extraction commands with clipboard copy functionality
**When to use:** Linux platform where auto-install is not possible

```python
# Source: tkinter clipboard docs (avoid pyperclip dependency)
class LinuxInstallInstructionsDialog(ctk.CTkToplevel):
    """Show tar.gz extraction instructions with copy button."""

    def __init__(self, parent, tar_path: Path):
        super().__init__(parent)
        self.title("Installation Instructions")
        self.geometry("550x300")

        # Instructions text
        command = f"tar -xzf {tar_path.name} && sudo mv job-radar /usr/local/bin/"

        instructions = ctk.CTkTextbox(self, height=150, width=500)
        instructions.insert("1.0", f"1. Extract the archive:\n{command}\n\n")
        instructions.insert("end", "2. Move the binary to your PATH\n")
        instructions.insert("end", "3. Run: job-radar-gui")
        instructions.configure(state="disabled")
        instructions.pack(pady=20, padx=20)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        # Copy command button
        copy_btn = ctk.CTkButton(
            btn_frame, text="Copy Command", width=130,
            command=lambda: self._copy_to_clipboard(command)
        )
        copy_btn.pack(side="left", padx=5)

        # Open folder button
        folder_btn = ctk.CTkButton(
            btn_frame, text="Open Folder", width=130,
            command=lambda: self._open_folder(tar_path)
        )
        folder_btn.pack(side="left", padx=5)

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard using tkinter."""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()  # Required for clipboard to persist

    def _open_folder(self, file_path: Path):
        """Open containing folder in file manager."""
        subprocess.Popen(["xdg-open", str(file_path.parent)])
```

### Anti-Patterns to Avoid

- **Using os.system() for process launching:** No security, no error handling, deprecated
- **Blocking subprocess.run() without timeout:** Can freeze GUI if process hangs
- **sys.exit() instead of destroy():** Bypasses cleanup, can leave resources open
- **Re-verifying SHA256 before launch:** Wastes time, already verified at download
- **Generic error messages:** "Failed to install" tells user nothing — include file path
- **Immediate app.destroy() after Popen:** No visual feedback, jarring UX

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DMG mounting | Custom DMG parser | hdiutil command | Complex binary format, edge cases (encryption, compression) |
| Process detachment | Manual fork/exec | subprocess.Popen with flags | Platform-specific complexity, Windows vs Unix differences |
| Clipboard operations | Custom clipboard API | tkinter clipboard methods | Already available, no dependency, works cross-platform |
| Modal dialogs | Custom window management | CTkToplevel with transient/grab_set | Proper parent tracking, focus management, already proven |
| Temp file cleanup | Custom deletion tracking | Cleanup on startup pattern | Safer than atexit (installer may still be reading file) |

**Key insight:** Installer launching is deceptively complex due to platform differences (UAC elevation, quarantine attributes, volume mounting). Use stdlib subprocess with platform-specific command patterns rather than trying to abstract away differences.

## Common Pitfalls

### Pitfall 1: App Exits Before Installer Reads File

**What goes wrong:** App deletes installer file immediately after launching it, installer fails to read
**Why it happens:** Race condition between Popen return and actual file access by installer process
**How to avoid:** Keep installer file until NEXT app startup, delete in init code
**Warning signs:** Installer reports "file not found" even though launch succeeded

```python
# WRONG - immediate deletion
subprocess.Popen(["installer.exe"])
os.remove("installer.exe")  # Too soon!

# RIGHT - delete on next launch
def __init__(self):
    self._cleanup_old_installers()  # Delete from PREVIOUS session
    # ... rest of init

def _cleanup_old_installers(self):
    """Delete installer files from previous session."""
    temp_dir = Path(tempfile.gettempdir())
    for pattern in ["Job-Radar-v*-installer.*", "Job-Radar-Setup-v*.exe"]:
        for old_file in temp_dir.glob(pattern):
            try:
                old_file.unlink()
            except OSError:
                pass  # File may be in use, ignore
```

### Pitfall 2: DMG Mount Point Not Found

**What goes wrong:** hdiutil attach succeeds but code can't find mount point to open in Finder
**Why it happens:** hdiutil output format varies, parsing fails on unexpected format
**How to avoid:** Parse hdiutil output defensively, check for /Volumes/ path explicitly
**Warning signs:** DMG mounts but Finder doesn't open, user doesn't see drag-to-install window

```python
# Parse hdiutil output looking for mount point
# Output: "/dev/disk4 ... Apple_HFS /Volumes/Job-Radar"
lines = result.stdout.strip().split('\n')
mount_point = None
for line in lines:
    if '/Volumes/' in line:
        # Split on tab, take last field
        parts = line.split('\t')
        mount_point = parts[-1].strip()
        break

if not mount_point:
    # Fallback: try to construct expected volume name
    volume_name = dmg_path.stem  # e.g., "Job-Radar-v2.2.0"
    mount_point = f"/Volumes/{volume_name}"
    if not Path(mount_point).exists():
        raise RuntimeError("Could not determine mount point")
```

### Pitfall 3: Windows UAC Blocks Silent Install

**What goes wrong:** Installer launches but UAC prompt appears behind app window, user confused
**Why it happens:** UAC prompt doesn't always steal focus
**How to avoid:** This is expected behavior — user instructions should mention UAC prompt
**Warning signs:** User reports "nothing happened" when installer actually launched

**Note:** This is NOT a pitfall to fix with code. NSIS installers require admin elevation, UAC prompt is correct behavior. Document in confirmation dialog: "Windows may show a security prompt."

### Pitfall 4: Linux xdg-open Not Installed

**What goes wrong:** xdg-open command fails, folder doesn't open
**Why it happens:** Minimal Linux installations may not include xdg-utils
**How to avoid:** Catch subprocess error, show file path in error message
**Warning signs:** "xdg-open: command not found" in stderr

```python
try:
    subprocess.Popen(["xdg-open", str(folder_path)])
except FileNotFoundError:
    # xdg-open not installed - show path instead
    self._show_info(f"File saved to: {folder_path}")
except Exception as e:
    self._show_error(f"Could not open folder: {e}\nFile saved to: {folder_path}")
```

### Pitfall 5: macOS Quarantine Blocks DMG

**What goes wrong:** macOS Gatekeeper shows "unverified developer" warning, user can't open DMG
**Why it happens:** com.apple.quarantine extended attribute set on downloaded file
**How to avoid:** Decision point — strip xattr after download OR rely on notarization (Phase 39 requirement UPDATE-09)
**Warning signs:** User reports "can't open DMG, security warning"

**Recommendation:** Since UPDATE-09 requires notarization, LEAVE quarantine attribute intact. Notarized DMGs pass Gatekeeper checks even with quarantine. Stripping xattr reduces security without benefit.

```python
# OPTIONAL: Strip quarantine if NOT relying on notarization
# Only implement if UPDATE-09 notarization is deferred
import subprocess

def strip_quarantine(file_path: Path):
    """Remove macOS quarantine attribute."""
    try:
        subprocess.run(
            ["xattr", "-d", "com.apple.quarantine", str(file_path)],
            check=True,
            timeout=5
        )
    except subprocess.CalledProcessError:
        # Attribute may not exist, ignore
        pass
```

## Code Examples

Verified patterns from stdlib docs and existing codebase:

### Platform Detection (Already Established)

```python
# Source: job_radar/update_checker.py (lines 41-48)
import sys

def get_platform():
    """Get current platform identifier."""
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    elif sys.platform.startswith("linux"):
        return "linux"
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")
```

### Subprocess with Timeout and Error Handling

```python
# Source: Python subprocess docs
import subprocess
from pathlib import Path

def launch_installer(installer_path: Path, platform: str):
    """Launch platform-specific installer."""
    try:
        if platform == "macos":
            # Mount DMG and open in Finder
            result = subprocess.run(
                ["hdiutil", "attach", str(installer_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            result.check_returncode()

            # Parse and open mount point
            mount_point = _parse_mount_point(result.stdout)
            subprocess.Popen(["open", mount_point])

        elif platform == "windows":
            # Launch exe with detached process
            subprocess.Popen(
                [str(installer_path)],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )

        elif platform == "linux":
            # Linux shows instructions dialog instead
            # This function not called on Linux
            raise RuntimeError("Linux uses instructions dialog, not direct launch")

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Installer launch timed out after 30 seconds")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Installer launch failed: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError(f"Installer file not found: {installer_path}")
```

### CustomTkinter Modal Dialog (Existing Pattern)

```python
# Source: job_radar/gui/uninstall_dialog.py (lines 15-52)
import customtkinter as ctk

class ConfirmDialog(ctk.CTkToplevel):
    """Modal confirmation dialog."""

    def __init__(self, parent, message: str, on_confirm: callable):
        super().__init__(parent)
        self.title("Confirm")
        self.geometry("400x150")

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        # Content
        label = ctk.CTkLabel(self, text=message, wraplength=350)
        label.pack(pady=30)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        cancel = ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy)
        cancel.pack(side="left", padx=5)

        confirm = ctk.CTkButton(
            btn_frame, text="Confirm",
            command=lambda: (on_confirm(), self.destroy())
        )
        confirm.pack(side="left", padx=5)
```

### Tkinter Clipboard (No External Dependency)

```python
# Source: tkinter clipboard API
def copy_to_clipboard(widget, text: str):
    """Copy text to clipboard using tkinter."""
    widget.clipboard_clear()
    widget.clipboard_append(text)
    widget.update()  # Required for clipboard to persist after window closes
```

### App.after() for Delayed Shutdown

```python
# Source: tkinter after() method docs
def shutdown_after_message(self, message: str, delay_ms: int = 1500):
    """Show status message, then exit after delay."""
    # Update status label
    self.status_label.configure(text=message)

    # Schedule destroy after delay
    self.after(delay_ms, self.destroy)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| os.system() for process launch | subprocess module | Python 2.6+ | Better error handling, security, cross-platform |
| subprocess.call() | subprocess.run() | Python 3.5 | Simpler API, better defaults |
| Manual dialog centering | parent.winfo_x/y calculations | Tkinter 8.5+ | Reliable centering on multi-monitor setups |
| pyperclip for clipboard | tkinter clipboard methods | Built-in since Tk 8.0 | No external dependency |
| Immediate file deletion | Cleanup on next startup | Async best practice | Avoids race conditions |

**Deprecated/outdated:**
- **os.system()**: Deprecated in favor of subprocess (security, error handling)
- **subprocess.call()**: Replaced by subprocess.run() in Python 3.5+
- **Stripping quarantine on notarized apps**: Unnecessary since macOS 10.15+ trusts notarization

## Open Questions

1. **Should we strip macOS quarantine attribute?**
   - What we know: UPDATE-09 requires notarization, which satisfies Gatekeeper
   - What's unclear: Does notarization guarantee no quarantine warnings?
   - Recommendation: Leave quarantine intact (trust notarization), add xattr stripping as fallback if user reports issues in testing

2. **Exact delay timing for status message before exit?**
   - What we know: Need enough time for user to read "Installer launched. Closing app..."
   - What's unclear: Optimal milliseconds for readability vs responsiveness
   - Recommendation: Start with 1500ms (1.5 seconds), adjust based on user feedback

3. **Linux tar extraction command format?**
   - What we know: Need tar -xzf for .tar.gz, should suggest /usr/local/bin for system-wide install
   - What's unclear: Should we show sudo mv or suggest user-local path (~/.local/bin)?
   - Recommendation: Show both options in instructions, default to system-wide with sudo

4. **Error recovery for failed DMG mount?**
   - What we know: hdiutil can fail due to disk space, corruption, quarantine issues
   - What's unclear: Should we retry once, or immediately show manual download link?
   - Recommendation: No retry for mount failures (unlikely to succeed), show error + manual link

## Sources

### Primary (HIGH confidence)

- [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html) - Official subprocess API reference
- [CustomTkinter CTkToplevel documentation](https://customtkinter.tomschimansky.com/documentation/windows/toplevel/) - Modal dialog patterns
- [macOS hdiutil man page](https://ss64.com/mac/hdiutil.html) - DMG mounting commands
- Existing codebase patterns:
  - `job_radar/update_checker.py` - Platform detection, installer paths
  - `job_radar/gui/update_banner.py` - Dialog patterns, confirmation flows
  - `job_radar/gui/uninstall_dialog.py` - CTkToplevel modal dialog implementation
  - `job_radar/gui/worker_thread.py` - DownloadWorker pattern with SHA256 verification

### Secondary (MEDIUM confidence)

- [Python subprocess Popen detach process](https://www.digitaldesignjournal.com/python-detach-subprocess-and-exit-with-examples/) - Process detachment patterns
- [macOS quarantine attribute removal](https://derflounder.wordpress.com/2012/11/20/clearing-the-quarantine-extended-attribute-from-downloaded-applications/) - xattr commands
- [Linux xdg-open documentation](https://www.geeksforgeeks.org/linux-unix/xdg-open-command-in-linux-with-examples/) - File manager opening
- [Tkinter after() method best practices](https://www.pythontutorial.net/tkinter/tkinter-after/) - GUI delay patterns
- [Tkinter destroy vs quit](https://blog.finxter.com/understanding-the-differences-between-root-destroy-and-root-quit-in-tkinter-python/) - Proper shutdown

### Tertiary (LOW confidence)

- [pyperclip documentation](https://pypi.org/project/pyperclip/) - Clipboard library (not recommended, use tkinter instead)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - subprocess, pathlib, sys are stdlib, CustomTkinter already integrated
- Architecture: HIGH - Patterns verified in existing codebase, official docs confirm subprocess APIs
- Pitfalls: MEDIUM - Based on general subprocess best practices and macOS/Windows installer knowledge, not phase-specific testing

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (30 days - stable technologies, stdlib focus)

**Platform-specific notes:**
- macOS: hdiutil commands may change in future macOS versions, but stable since 10.5+
- Windows: NSIS installers handle UAC automatically, no code changes needed
- Linux: xdg-open is standard but may not be installed on minimal systems (good error handling required)
