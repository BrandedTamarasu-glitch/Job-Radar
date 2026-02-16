# Phase 39: Auto-Update Download - Research

**Researched:** 2026-02-16
**Domain:** HTTP streaming downloads with threading, progress visualization, and file integrity verification
**Confidence:** HIGH

## Summary

Phase 39 implements background installer downloads from GitHub Releases with real-time progress feedback, cancellation support, and SHA256 integrity verification. The standard Python approach uses `requests` library with `stream=True` for chunk-based downloading, `threading.Event` for cooperative cancellation, `queue.Queue` for thread-safe GUI updates, and `hashlib.sha256()` for file verification. The codebase already has established patterns for threading with CustomTkinter through `worker_thread.py`, which provides the template for implementing download workers.

The key technical challenge is transforming the UpdateBanner widget between three states (notification → progress → completion) while maintaining thread-safe GUI updates. CustomTkinter's `CTkProgressBar` and `after()` method enable this pattern.

**Primary recommendation:** Follow existing `SearchWorker` pattern from `worker_thread.py` — create `DownloadWorker` with queue-based messaging, use `threading.Event` for cancellation, and implement state transformation in `UpdateBanner` with grid_remove/grid methods.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Download trigger & flow:**
- Confirmation dialog before download starts: "Download v{version}? ~{size}MB"
- After confirmation, banner transforms to show progress inline (replaces notification buttons with progress bar)
- Download runs in background thread — user can use app normally, navigate tabs, while banner shows progress
- On completion, banner shows "Download complete!" with "Install Now" button (wired in Phase 40)

**Progress visualization:**
- Progress bar displayed inline in the transformed banner (replaces Download/Remind Later/X buttons)
- Shows: progress bar + percentage + downloaded/total size (e.g., "45% (12 MB / 25 MB)")
- Progress bar uses same blue/teal accent color as the notification banner — cohesive look
- Cancel button displayed alongside progress bar on the right side

**Cancel & failure behavior:**
- Cancel button in banner during download — clicking cancels immediately
- On cancel: suppress banner until next program start (not 24h/7d suppress — just session dismiss)
- Partial file deleted on cancel — clean slate
- On download failure: banner shows "Download failed" with Retry and Dismiss buttons
- Retry restarts download from scratch (no resume/range requests) — simpler, always works
- Retry limit: Claude's discretion on auto-retry behavior

**File management:**
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

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.x | HTTP downloads with streaming | Already in project, industry standard for HTTP, built-in chunk streaming |
| hashlib | stdlib | SHA256 file verification | Python standard library, cryptographic hashing, zero dependencies |
| threading | stdlib | Background download execution | Python standard library, already used in project via `worker_thread.py` |
| queue | stdlib | Thread-safe GUI communication | Python standard library, already used for `UpdateChecker` and `SearchWorker` |
| tempfile | stdlib | Cross-platform temp directory | Python standard library, handles platform differences automatically |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| customtkinter | ~5.x | CTkProgressBar widget | Already project UI framework for progress visualization |
| packaging.version | ~23.x | Version string comparison | Already used in `UpdateChecker.is_newer_version()` |
| pathlib | stdlib | Path manipulation | Preferred over os.path in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| requests | urllib3 | Lower-level, more complex API, no benefit for this use case |
| requests | aiohttp | Async I/O unnecessary — already using threading model |
| threading.Event | asyncio cancellation | Would require rewriting entire GUI threading model |

**Installation:**
```bash
# All dependencies already in project (requests, customtkinter)
# No new packages required
```

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── gui/
│   ├── update_banner.py          # Extend with state transformation
│   ├── worker_thread.py          # Add DownloadWorker class
│   └── main_window.py            # Wire download confirmation dialog
├── update_checker.py             # Extend with GitHub API assets
└── paths.py                      # Already has get_data_dir()
```

### Pattern 1: DownloadWorker with Queue Communication
**What:** Background thread downloads file in chunks, sends progress messages via queue
**When to use:** All background downloads in CustomTkinter GUI
**Example:**
```python
# Source: Existing pattern from job_radar/gui/worker_thread.py (lines 152-332)
class DownloadWorker:
    def __init__(self, result_queue: queue.Queue, stop_event: threading.Event,
                 asset_url: str, asset_digest: str, dest_path: str):
        self._queue = result_queue
        self._stop_event = stop_event
        self._asset_url = asset_url
        self._asset_digest = asset_digest  # "sha256:abc123..."
        self._dest_path = dest_path

    def run(self):
        """Download file with progress updates (runs in worker thread)."""
        try:
            # Stream download with progress
            response = requests.get(self._asset_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(self._dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._stop_event.is_set():
                        self._queue.put(("download_cancelled",))
                        return

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Send progress every 100KB to avoid GUI flooding
                        if downloaded % (100 * 1024) < 8192:
                            self._queue.put(("download_progress", downloaded, total_size))

            # Verify SHA256
            computed_hash = self._compute_sha256(self._dest_path)
            expected_hash = self._asset_digest.replace("sha256:", "")

            if computed_hash != expected_hash:
                self._queue.put(("download_failed", "Hash verification failed"))
                return

            self._queue.put(("download_complete", self._dest_path))

        except Exception as e:
            self._queue.put(("download_failed", str(e)))

    def _compute_sha256(self, filepath: str) -> str:
        """Compute SHA256 hash of file in chunks."""
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(4096):
                h.update(chunk)
        return h.hexdigest()

    def cancel(self):
        """Request cancellation of download."""
        self._stop_event.set()
```

### Pattern 2: UpdateBanner State Transformation
**What:** Transform banner widget between notification/progress/complete states using grid_remove/grid
**When to use:** UI widgets that need to switch between distinct layouts without recreation
**Example:**
```python
# Source: CustomTkinter patterns + existing UpdateBanner structure
class UpdateBanner(ctk.CTkFrame):
    def __init__(self, parent, version, release_url, on_dismiss, on_remind, on_download):
        super().__init__(parent, fg_color=("#3498DB", "#2874A6"), corner_radius=0)
        self.version = version
        self.on_download = on_download

        # Create ALL widgets upfront, show/hide with grid/grid_remove
        self._create_notification_widgets()
        self._create_progress_widgets()
        self._create_complete_widgets()

        # Start in notification state
        self.show_notification()

    def show_notification(self):
        """Show: message + Download + Remind Later + X buttons."""
        self._hide_all()
        self.message_label.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=10)
        self.download_btn.grid(row=0, column=1, padx=(0, 10), pady=10)
        self.remind_btn.grid(row=0, column=2, padx=(0, 10), pady=10)
        self.x_btn.grid(row=0, column=3, padx=(0, 20), pady=10)

    def show_progress(self):
        """Show: message + progress bar + percentage + cancel button."""
        self._hide_all()
        self.progress_message.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=10)
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
        self.progress_label.grid(row=0, column=2, padx=(0, 10), pady=10)
        self.cancel_btn.grid(row=0, column=3, padx=(0, 20), pady=10)

    def update_progress(self, downloaded: int, total: int):
        """Update progress bar and label (called from queue polling)."""
        progress = downloaded / total if total > 0 else 0
        self.progress_bar.set(progress)

        downloaded_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        pct = int(progress * 100)
        self.progress_label.configure(text=f"{pct}% ({downloaded_mb:.1f} MB / {total_mb:.1f} MB)")
```

### Pattern 3: Queue Polling with after()
**What:** Main thread polls queue at regular intervals (100ms) to receive worker messages
**When to use:** All GUI updates from background threads (standard Tkinter/CustomTkinter pattern)
**Example:**
```python
# Source: Existing pattern from job_radar/gui/main_window.py (lines 100-101, expanded)
def _check_queue(self):
    """Poll queue for messages from worker threads."""
    try:
        while True:
            msg = self._queue.get_nowait()

            if msg[0] == "download_progress":
                _, downloaded, total = msg
                if self._update_banner:
                    self._update_banner.update_progress(downloaded, total)

            elif msg[0] == "download_complete":
                _, dest_path = msg
                if self._update_banner:
                    self._update_banner.show_complete(dest_path)

            elif msg[0] == "download_failed":
                _, error = msg
                if self._update_banner:
                    self._update_banner.show_failure(error)

            elif msg[0] == "download_cancelled":
                if self._update_banner:
                    self._update_banner.destroy()
                    self._update_banner = None

    except queue.Empty:
        pass

    # Re-schedule polling (100ms interval)
    self.after(100, self._check_queue)
```

### Pattern 4: Platform Detection for Asset Selection
**What:** Use `sys.platform` to select correct installer asset from GitHub release
**When to use:** Cross-platform applications downloading platform-specific binaries
**Example:**
```python
# Source: Python official docs - platform detection
import sys

def get_platform_asset_pattern() -> str:
    """Return regex pattern for matching platform-specific installer asset."""
    if sys.platform == "darwin":
        return r"\.dmg$"
    elif sys.platform == "win32":
        return r"\.exe$"
    elif sys.platform.startswith("linux"):
        return r"\.tar\.gz$"
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")

def select_installer_asset(assets: list[dict]) -> dict | None:
    """Select platform-appropriate installer from GitHub release assets.

    Args:
        assets: List of asset dicts from GitHub API with 'name', 'browser_download_url', 'digest'

    Returns:
        Asset dict or None if no match found
    """
    import re
    pattern = get_platform_asset_pattern()

    for asset in assets:
        if re.search(pattern, asset['name'], re.IGNORECASE):
            return asset

    return None
```

### Pattern 5: Temp File with Cleanup
**What:** Use `tempfile.gettempdir()` for cross-platform temp directory, manual file creation with try/finally cleanup
**When to use:** Temporary files that need a guaranteed name (for external process launch)
**Example:**
```python
# Source: Python tempfile docs + project needs
import tempfile
from pathlib import Path

def create_installer_path(version: str) -> Path:
    """Create temp path for installer download.

    Returns path like: /tmp/Job-Radar-v2.3.0-installer.dmg
    """
    temp_dir = Path(tempfile.gettempdir())

    if sys.platform == "darwin":
        filename = f"Job-Radar-v{version}-installer.dmg"
    elif sys.platform == "win32":
        filename = f"Job-Radar-Setup-v{version}.exe"
    else:
        filename = f"job-radar-v{version}-installer.tar.gz"

    return temp_dir / filename

def cleanup_installer(filepath: Path):
    """Delete installer file, ignoring errors if already deleted."""
    try:
        filepath.unlink(missing_ok=True)
    except Exception:
        pass  # Best effort cleanup
```

### Anti-Patterns to Avoid

- **Updating GUI from worker thread directly:** CustomTkinter is NOT thread-safe. Always use queue + after() polling
- **Using NamedTemporaryFile with delete=True:** File disappears before Phase 40 can launch it — use manual file creation
- **Resuming partial downloads with Range requests:** Adds complexity, GitHub Assets API may not support it reliably — restart from scratch on retry
- **Blocking main thread during download:** Use daemon thread, never `thread.join()` in GUI code
- **Progress update spam:** Sending every 8KB chunk floods queue — send updates every 100KB or 100ms minimum

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP downloads | Custom socket code, urllib manual chunk handling | `requests.get(stream=True)` with `iter_content()` | Handles redirects, compression, encoding, timeouts, errors automatically |
| SHA256 hashing | Manual hash implementation | `hashlib.sha256()` with chunked file reading | FIPS-compliant, battle-tested, handles large files efficiently |
| Cross-platform temp directory | Hardcoded paths like `/tmp` or `C:\Temp` | `tempfile.gettempdir()` | Handles env vars (TMPDIR, TEMP, TMP), platform defaults, permissions |
| Thread cancellation | Thread termination, forceful killing | `threading.Event` with cooperative checks | Python has no safe thread.kill() — cooperative cancellation is the only reliable pattern |
| Platform detection | Parsing `platform.system()` strings | `sys.platform` comparison | More reliable, simpler API, returns canonical values |

**Key insight:** Python's stdlib already handles the hard parts (HTTP, crypto, threads, temp files). Don't reimplement — compose stdlib primitives following established patterns.

## Common Pitfalls

### Pitfall 1: CTkProgressBar Expects 0.0-1.0, Not 0-100
**What goes wrong:** Setting progress to percentage (e.g., `progress_bar.set(45)`) crashes or shows empty bar
**Why it happens:** CTkProgressBar uses 0.0-1.0 range like Tkinter's ttk.Progressbar
**How to avoid:** Always divide: `progress_bar.set(downloaded / total)`
**Warning signs:** Progress bar appears empty despite download proceeding

### Pitfall 2: Partial File Left on Cancel Without Cleanup
**What goes wrong:** User cancels download, retries, gets corrupted file (appends to partial)
**Why it happens:** File handle closed but file not deleted on cancellation
**How to avoid:** Delete partial file in cancel handler:
```python
try:
    if self._stop_event.is_set():
        Path(self._dest_path).unlink(missing_ok=True)
        self._queue.put(("download_cancelled",))
        return
except Exception:
    pass  # File may not exist yet
```
**Warning signs:** Second download attempt fails with hash mismatch

### Pitfall 3: GitHub Digest Field is Null for Old Releases
**What goes wrong:** Code expects `asset['digest']` but gets `None`, crashes on verification
**Why it happens:** GitHub only generates SHA256 digests for releases published after June 2025
**How to avoid:** Check for null digest, handle gracefully:
```python
if not asset.get('digest'):
    log.warning("Asset has no digest field - skipping verification")
    self._queue.put(("download_complete", self._dest_path))
    return

# Only verify if digest exists
expected_hash = asset['digest'].replace("sha256:", "")
```
**Warning signs:** Download works locally (new test releases) but fails in production (old releases)

### Pitfall 4: Flooding Queue with Progress Updates
**What goes wrong:** Sending progress message for every 8KB chunk (1000+ messages for 10MB file) makes GUI sluggish
**Why it happens:** Chunk size is small (8KB recommended for I/O), but GUI can't process 1000 updates/sec
**How to avoid:** Throttle updates to every 100KB or use modulo check:
```python
if downloaded % (100 * 1024) < chunk_size:  # Every 100KB
    self._queue.put(("download_progress", downloaded, total))
```
**Warning signs:** Progress bar updates appear jerky, GUI becomes unresponsive during download

### Pitfall 5: Widget State Confusion (Notification vs Progress)
**What goes wrong:** Download button still visible during progress, or progress bar shows after completion
**Why it happens:** Forgetting to hide old widgets when transitioning states
**How to avoid:** Implement `_hide_all()` helper that calls `grid_remove()` on ALL state-specific widgets
```python
def _hide_all(self):
    """Remove all state-specific widgets from grid."""
    for widget in [self.download_btn, self.remind_btn, self.x_btn,
                   self.progress_bar, self.progress_label, self.cancel_btn,
                   self.install_btn, self.retry_btn]:
        widget.grid_remove()
```
**Warning signs:** Overlapping buttons, layout corruption during state transitions

### Pitfall 6: Thread Still Running After Cancel
**What goes wrong:** User cancels, banner disappears, but thread continues downloading (wasted bandwidth)
**Why it happens:** Not checking `stop_event` frequently enough in download loop
**How to avoid:** Check `stop_event.is_set()` before AND after each chunk write
```python
for chunk in response.iter_content(chunk_size=8192):
    if self._stop_event.is_set():
        # Clean up partial file before returning
        Path(self._dest_path).unlink(missing_ok=True)
        self._queue.put(("download_cancelled",))
        return

    if chunk:
        f.write(chunk)
```
**Warning signs:** Download continues after banner dismissed (check network monitor)

## Code Examples

Verified patterns from official sources and existing codebase:

### SHA256 File Verification (Chunked)
```python
# Source: https://docs.python.org/3/library/hashlib.html
import hashlib

def compute_sha256(filepath: str) -> str:
    """Compute SHA256 hash of file in 4KB chunks.

    Args:
        filepath: Path to file to hash

    Returns:
        Lowercase hexadecimal digest string
    """
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        # Read 4KB chunks (>2047 bytes for GIL release)
        while chunk := f.read(4096):
            h.update(chunk)
    return h.hexdigest()
```

### GitHub Release Assets API Call
```python
# Source: https://docs.github.com/en/rest/releases/assets + existing update_checker.py
import requests

def fetch_release_assets(repo_owner: str, repo_name: str, tag: str) -> list[dict]:
    """Fetch assets for a specific release tag.

    Args:
        repo_owner: GitHub username (e.g., "BrandedTamarasu-glitch")
        repo_name: Repository name (e.g., "Job-Radar")
        tag: Release tag (e.g., "v2.3.0")

    Returns:
        List of asset dicts with keys: name, browser_download_url, digest, size
    """
    # Get release by tag
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{tag}"
    response = requests.get(url, headers={"User-Agent": f"{repo_name}/auto-update"}, timeout=10)
    response.raise_for_status()

    release = response.json()
    assets = release.get('assets', [])

    # Extract relevant fields
    return [
        {
            'name': asset['name'],
            'browser_download_url': asset['browser_download_url'],
            'digest': asset.get('digest'),  # May be None for old releases
            'size': asset['size']
        }
        for asset in assets
    ]
```

### Confirmation Dialog with Size Display
```python
# Source: CustomTkinter patterns
import customtkinter as ctk

class DownloadConfirmDialog(ctk.CTkToplevel):
    """Confirmation dialog before starting download."""

    def __init__(self, parent, version: str, size_bytes: int, on_confirm: callable):
        super().__init__(parent)

        self.title("Download Installer")
        self.geometry("400x150")
        self.resizable(False, False)

        # Center on parent
        self.transient(parent)
        self.grab_set()

        self.on_confirm = on_confirm
        self.confirmed = False

        # Message
        size_mb = size_bytes / (1024 * 1024)
        message = ctk.CTkLabel(
            self,
            text=f"Download v{version}? ~{size_mb:.1f}MB",
            font=ctk.CTkFont(size=14)
        )
        message.pack(pady=(30, 20))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            command=self.destroy
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="Download",
            width=100,
            command=self._on_confirm
        )
        confirm_btn.pack(side="left")

    def _on_confirm(self):
        """Handle confirm button click."""
        self.confirmed = True
        self.destroy()
        self.on_confirm()
```

### Worker Thread Creation Pattern
```python
# Source: job_radar/gui/worker_thread.py (lines 314-332)
def create_download_worker(
    result_queue: queue.Queue,
    asset_url: str,
    asset_digest: str,
    dest_path: str
) -> tuple:
    """Create download worker with thread.

    Args:
        result_queue: Queue for worker to send messages to GUI
        asset_url: GitHub asset browser_download_url
        asset_digest: Expected SHA256 digest ("sha256:abc123...")
        dest_path: Destination path for downloaded file

    Returns:
        Tuple of (worker, thread). Caller must call thread.start().
    """
    stop_event = threading.Event()
    worker = DownloadWorker(result_queue, stop_event, asset_url, asset_digest, dest_path)
    thread = threading.Thread(target=worker.run, daemon=True)
    return worker, thread
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `urllib.urlretrieve()` | `requests.get(stream=True)` | ~2015 | Better error handling, timeout support, modern API |
| Manual thread termination | `threading.Event` cooperative cancellation | Python 2.x era | Only safe way to stop threads in Python |
| Tkinter-only GUI | CustomTkinter | 2021+ | Modern look, dark mode, better widgets (CTkProgressBar) |
| MD5 checksums | SHA256 digests | ~2010 security shift | MD5 cryptographically broken, SHA256 industry standard |
| GitHub API v2 | GitHub REST API v3 | 2014 | Structured JSON, asset metadata including digests |

**Deprecated/outdated:**
- `urllib.urlretrieve()`: Still works but lacks streaming, progress, modern error handling — use `requests`
- Manual `Content-Length` parsing: `requests` provides it in `response.headers` dict automatically
- GitHub API v2 XML format: Replaced by v3 JSON in 2014
- `Thread.terminate()`: Never existed in Python — use Event-based cancellation

## Open Questions

1. **Auto-retry on transient network failure**
   - What we know: User can manually retry via button; worker detects RequestException
   - What's unclear: Should worker auto-retry once before showing failure UI?
   - Recommendation: Start with manual-only (simpler), add auto-retry in future phase if user feedback indicates need

2. **Progress update frequency optimization**
   - What we know: 8KB chunks → ~1000 messages for 10MB, needs throttling
   - What's unclear: Best balance between smoothness and performance (100KB? 100ms timer?)
   - Recommendation: Start with 100KB threshold (simple, deterministic), profile if GUI sluggish

3. **Banner animation between states**
   - What we know: grid_remove/grid enables instant transitions; could add fade/slide
   - What's unclear: Do animations improve UX or add distraction?
   - Recommendation: Start with instant transitions (VS Code style), add animation later if desired

4. **Session-only suppress mechanism**
   - What we know: Cancel dismisses until next launch (not 24h/7d)
   - What's unclear: Store in-memory flag or config.json with session ID?
   - Recommendation: In-memory flag (simplest) — just don't show banner again if `_update_banner` destroyed during session

## Sources

### Primary (HIGH confidence)
- [Python tempfile module official docs](https://docs.python.org/3/library/tempfile.html) - gettempdir(), cross-platform behavior
- [Python hashlib module official docs](https://docs.python.org/3/library/hashlib.html) - sha256(), chunked file hashing
- [Python threading module official docs](https://docs.python.org/3/library/threading.html) - Event, Queue, best practices
- [GitHub REST API: Release Assets](https://docs.github.com/en/rest/releases/assets) - Asset fields, digest format, download URLs
- Existing codebase patterns:
  - `job_radar/gui/worker_thread.py` (lines 1-332) - Queue-based threading pattern
  - `job_radar/update_checker.py` (lines 1-301) - UpdateChecker implementation
  - `job_radar/gui/update_banner.py` (lines 1-110) - Current banner implementation

### Secondary (MEDIUM confidence)
- [CustomTkinter CTkProgressBar documentation](https://customtkinter.tomschimansky.com/documentation/widgets/progressbar/) - Progress bar API
- [CustomTkinter CTkProgressBar Wiki](https://github.com/TomSchimansky/CustomTkinter/wiki/CTkProgressBar) - Usage examples
- [GitHub SHA256 checksums announcement](https://undercodenews.com/github-enhances-release-asset-integrity-with-sha256-checksums/) - Feature launch date (June 2025)
- [GitHub Releases checksums discussion](https://github.com/orgs/community/discussions/23512) - Community verification patterns
- [Python threading Event for cancellation tutorial](https://superfastpython.com/stop-a-thread-in-python/) - Cooperative cancellation patterns
- [Python platform detection guide](https://www.pythonmorsels.com/operating-system-checks/) - sys.platform vs platform.system()

### Tertiary (LOW confidence)
- [Progress bars with tqdm + requests examples](https://gist.github.com/yanqd0/c13ed29e29432e3cf3e7c38467f42f51) - Community patterns
- [Tkinter threading tutorial](https://www.pythontutorial.net/tkinter/tkinter-thread/) - General threading patterns
- [Medium article on Tkinter download progress](https://medium.com/codingmountain-blog/elevating-download-progress-visualization-with-python-a-tkinter-twist-6a5c05d0e0ca) - Community implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project or Python stdlib, verified usage patterns
- Architecture: HIGH - Existing `worker_thread.py` provides proven template, CustomTkinter patterns documented
- Pitfalls: MEDIUM-HIGH - Some from official docs (null digest, progress range), others from community experience
- GitHub API: HIGH - Official docs verified, digest field format confirmed
- Temp file handling: HIGH - Python stdlib docs, cross-platform behavior well-documented

**Research date:** 2026-02-16
**Valid until:** ~2026-03-18 (30 days - stable domain, unlikely to change)
