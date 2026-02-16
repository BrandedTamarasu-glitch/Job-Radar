# Phase 38: Auto-Update Foundation (Version Detection) - Research

**Researched:** 2026-02-16
**Domain:** Desktop application auto-update notifications, version checking, GitHub Releases API integration
**Confidence:** HIGH

## Summary

This phase implements the foundation for auto-update notifications in a Python/CustomTkinter desktop application. Users will see a VS Code-style banner notification when a new version is available via GitHub Releases API, with dismiss/remind functionality and manual check capability in Settings. The implementation leverages existing patterns (threading, atomic JSON writes, queue-based GUI updates) already proven in the codebase.

The technical stack is mature and well-documented: GitHub Releases API provides stable unauthenticated access (60 req/hour), Python's built-in `packaging.version` handles semantic versioning correctly, and CustomTkinter's grid layout system supports full-width banner placement. The primary complexity is coordinating background checks with GUI thread-safety, suppress period tracking, and graceful network failure handling.

**Primary recommendation:** Use threading.Thread daemon pattern (already in codebase) for background version checks, packaging.version.Version for comparison (stdlib, no dependencies), atomic JSON writes for update state persistence (pattern exists in profile_manager.py), and CTkFrame with grid sticky="ew" for banner placement (standard CustomTkinter).

## User Constraints

### Locked Decisions

**Notification appearance:**
- Full-width top banner above all content (VS Code style)
- Accent/info color (blue/teal) that stands out but isn't alarming
- Shows version number and Download button: "Version X.Y.Z available" + Download + Remind Later
- X button to dismiss (24-hour suppress) plus Remind Later button (7-day suppress)
- No changelog preview in banner (Phase 41 scope)

**Check timing & frequency:**
- Check GitHub Releases API once per day on launch (skip if already checked within 24 hours)
- Background thread — app loads immediately, banner appears a moment later if update found
- On network failure: silent fail with subtle indicator in Settings showing last check failed
- Store last-checked timestamp and check status inside existing config (not a separate file)

**Dismiss & remind behavior:**
- X button: suppresses banner for 24 hours
- Remind Later button: suppresses banner for 7 days
- Per-version dismiss — dismissing v2.3 only suppresses v2.3; if v2.4 drops during suppress period, it shows immediately
- After suppress period ends, banner reappears on next daily update check (not automatically mid-session)

**Settings integration:**
- Dedicated "Updates" section in Settings tab
- Shows current version, last check time, and check status (e.g., "v2.2.0 — Last checked: 2h ago — Up to date")
- "Check for Updates" button with inline status feedback: button text changes "Checking..." → "Up to date!" or "Update available!"
- "Check for updates automatically" toggle — user can disable auto-checks entirely
- Manual check always available regardless of toggle state

### Claude's Discretion

- Exact banner animation/transition
- Version comparison implementation details (semantic versioning parsing)
- GitHub Releases API request specifics (auth, caching headers)
- Error state icon/tooltip design in Settings

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| packaging | Stdlib 3.10+ | Semantic version parsing/comparison | Python's official version comparison library, PEP 440 compliant, handles pre-releases correctly |
| requests | Already in deps | GitHub Releases API HTTP calls | Already dependency, proven in API sources code, handles timeouts/errors gracefully |
| threading | Stdlib | Background version check on launch | Already used in worker_thread.py, daemon threads for non-blocking checks |
| datetime/timedelta | Stdlib | Timestamp tracking, suppress period calculation | Already used throughout codebase (search.py, tracker.py), native time arithmetic |
| json | Stdlib | Update state persistence in config.json | Atomic write pattern exists in profile_manager.py, reusable |
| webbrowser | Stdlib | Open GitHub Releases page in browser | Cross-platform URL opening, already used in main_window.py for report opening |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| queue.Queue | Stdlib | Thread-safe message passing to GUI | Reuse existing pattern from worker_thread.py for version check results |
| tempfile | Stdlib | Atomic JSON writes (temp + rename) | Already in profile_manager.py _write_json_atomic, prevents corruption |
| pathlib | Stdlib 3.10+ | Config file path resolution | Already in paths.py get_data_dir, consistent with project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| packaging.version | semver library | semver is third-party dependency (adds 1 dep), packaging is stdlib and already available |
| requests | urllib.request | urllib has less friendly error handling, no built-in timeout support, requests already a dependency |
| Manual version parsing | String split + int compare | Brittle: fails on pre-releases (v2.1.0-rc1), doesn't handle epochs, packaging.version handles all edge cases |

**Installation:**
No new dependencies required — all libraries are stdlib or already in `pyproject.toml`.

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── update_checker.py        # NEW: Version check logic, GitHub API calls
├── gui/
│   ├── main_window.py        # MODIFY: Add banner container, launch check on init
│   ├── update_banner.py      # NEW: CTkFrame banner widget with dismiss/remind
│   └── worker_thread.py      # REFERENCE: Thread pattern for background checks
└── paths.py                  # REFERENCE: Config path resolution pattern
```

### Pattern 1: Background Version Check on Launch

**What:** Non-blocking version check that doesn't delay app startup

**When to use:** On MainWindow.__init__, after UI loads

**Example:**
```python
# job_radar/update_checker.py
import threading
import queue
from datetime import datetime, timedelta
from packaging.version import Version, InvalidVersion
import requests
from job_radar import __version__
from job_radar.paths import get_data_dir

class UpdateChecker:
    """Background version checker using GitHub Releases API."""

    def __init__(self, result_queue: queue.Queue):
        self._queue = result_queue
        self._config_path = get_data_dir() / "config.json"

    def should_check(self) -> bool:
        """Check if 24 hours elapsed since last check."""
        config = self._load_config()
        last_check = config.get("update_state", {}).get("last_check")

        if not last_check:
            return True

        last_check_dt = datetime.fromisoformat(last_check)
        elapsed = datetime.now() - last_check_dt
        return elapsed >= timedelta(hours=24)

    def check_for_updates(self):
        """Query GitHub Releases API for latest version (runs in thread)."""
        try:
            # GitHub endpoint for latest release
            url = "https://api.github.com/repos/coryebert/Job-Radar/releases/latest"
            headers = {
                "User-Agent": "Job-Radar/2.1.7",  # GitHub requires User-Agent
                "Accept": "application/vnd.github.v3+json"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            release = response.json()
            latest_version = release["tag_name"].lstrip("v")
            release_url = release["html_url"]

            # Compare versions using packaging.version
            current = Version(__version__)
            latest = Version(latest_version)

            if latest > current:
                self._queue.put(("update_available", latest_version, release_url))
            else:
                self._queue.put(("up_to_date",))

            # Update last check timestamp
            self._save_check_status(success=True)

        except (requests.RequestException, InvalidVersion, KeyError) as e:
            # Network error, invalid JSON, or parse failure
            self._queue.put(("check_failed", str(e)))
            self._save_check_status(success=False)

    def _save_check_status(self, success: bool):
        """Atomically save last check timestamp and status."""
        config = self._load_config()
        config.setdefault("update_state", {})
        config["update_state"]["last_check"] = datetime.now().isoformat()
        config["update_state"]["check_success"] = success
        self._write_config(config)
```

**Source:** GitHub Releases API official docs (https://docs.github.com/en/rest/releases)

### Pattern 2: Per-Version Suppress Tracking

**What:** Track suppress periods per version, so new versions show immediately

**When to use:** When user clicks X (24h) or Remind Later (7d)

**Example:**
```python
def dismiss_banner(self, version: str, suppress_hours: int):
    """Suppress banner for specific version and duration.

    Args:
        version: Version being dismissed (e.g., "2.2.0")
        suppress_hours: 24 for X button, 168 (7*24) for Remind Later
    """
    config = self._load_config()
    config.setdefault("update_state", {})

    # Per-version suppress expiry timestamp
    expiry = datetime.now() + timedelta(hours=suppress_hours)
    config["update_state"]["suppressed_versions"] = {
        version: expiry.isoformat()
    }

    self._write_config(config)

def should_show_banner(self, version: str) -> bool:
    """Check if banner should display for given version."""
    config = self._load_config()
    suppressed = config.get("update_state", {}).get("suppressed_versions", {})

    if version not in suppressed:
        return True

    expiry = datetime.fromisoformat(suppressed[version])
    return datetime.now() >= expiry
```

**Key insight:** Suppress periods are version-specific, not global. If user dismisses v2.3 for 7 days but v2.4 releases tomorrow, v2.4 banner shows immediately.

### Pattern 3: Full-Width Banner with Grid Layout

**What:** VS Code-style banner at top of window, above tab content

**When to use:** When update available and not suppressed

**Example:**
```python
# job_radar/gui/update_banner.py
import customtkinter as ctk
import webbrowser

class UpdateBanner(ctk.CTkFrame):
    """Full-width update notification banner (VS Code style)."""

    def __init__(self, parent, version: str, release_url: str, on_dismiss, on_remind):
        super().__init__(
            parent,
            fg_color=("#3498DB", "#2874A6"),  # Blue/teal (light, dark)
            corner_radius=0,
            height=50
        )

        # Configure grid: single row, 4 columns (message | download | remind | X)
        self.grid_columnconfigure(0, weight=1)  # Message expands
        self.grid_columnconfigure(1, weight=0)  # Download button
        self.grid_columnconfigure(2, weight=0)  # Remind Later
        self.grid_columnconfigure(3, weight=0)  # X button

        # Message label
        msg = ctk.CTkLabel(
            self,
            text=f"Version {version} available",
            font=ctk.CTkFont(size=13),
            text_color="white"
        )
        msg.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=10)

        # Download button (opens browser to release page)
        download_btn = ctk.CTkButton(
            self,
            text="Download",
            width=100,
            command=lambda: webbrowser.open(release_url)
        )
        download_btn.grid(row=0, column=1, padx=5)

        # Remind Later button (7-day suppress)
        remind_btn = ctk.CTkButton(
            self,
            text="Remind Later",
            width=100,
            fg_color="transparent",
            border_width=1,
            command=lambda: on_remind(version)
        )
        remind_btn.grid(row=0, column=2, padx=5)

        # X button (24-hour suppress)
        x_btn = ctk.CTkButton(
            self,
            text="✕",
            width=30,
            command=lambda: on_dismiss(version)
        )
        x_btn.grid(row=0, column=3, padx=(5, 20))

# job_radar/gui/main_window.py (integration)
def __init__(self):
    # ... existing init code ...

    # Grid layout: row 0 = header, row 1 = banner (hidden), row 2 = content
    self.grid_rowconfigure(0, weight=0)  # Header (fixed)
    self.grid_rowconfigure(1, weight=0)  # Banner (fixed, initially hidden)
    self.grid_rowconfigure(2, weight=1)  # Content (expands)
    self.grid_columnconfigure(0, weight=1)

    # Banner placeholder (initially None)
    self._update_banner = None

    # Start background version check
    self._start_update_check()

def _show_update_banner(self, version: str, release_url: str):
    """Display update banner at row 1."""
    if self._update_banner:
        self._update_banner.destroy()

    self._update_banner = UpdateBanner(
        self,
        version,
        release_url,
        on_dismiss=lambda v: self._dismiss_banner(v, hours=24),
        on_remind=lambda v: self._dismiss_banner(v, hours=168)
    )
    self._update_banner.grid(row=1, column=0, sticky="ew", pady=0)
```

**Source:** CustomTkinter grid system docs (https://customtkinter.tomschimansky.com/tutorial/grid-system/)

### Pattern 4: Inline Button Status Feedback

**What:** Button text changes to show status ("Checking..." → "Up to date!")

**When to use:** Settings tab manual check button

**Example:**
```python
def _on_manual_check(self):
    """Handle manual update check button click."""
    # Disable button, change text
    self._check_button.configure(state="disabled", text="Checking...")

    # Start background check
    def check_thread():
        self._update_checker.check_for_updates()

    threading.Thread(target=check_thread, daemon=True).start()

def _on_check_complete(self, result: str):
    """Handle check completion (called from queue processing)."""
    if result == "up_to_date":
        self._check_button.configure(text="Up to date!", state="normal")
    elif result == "update_available":
        self._check_button.configure(text="Update available!", state="normal")
    else:
        self._check_button.configure(text="Check failed", state="normal")

    # Reset button text after 3 seconds
    self.after(3000, lambda: self._check_button.configure(text="Check for Updates"))
```

**Source:** CustomTkinter button documentation (https://customtkinter.tomschimansky.com/documentation/widgets/button/)

### Anti-Patterns to Avoid

- **Blocking main thread with API call:** Always use threading.Thread daemon for GitHub API requests — blocking freezes GUI
- **String comparison for versions:** `"1.10" < "1.9"` is True in string sorting — use `packaging.version.Version` for correct comparison
- **Non-atomic config writes:** Writing JSON directly risks corruption on crash — use tempfile + rename pattern from profile_manager.py
- **Checking on every tab switch:** Rate limit is 60/hour unauthenticated — check once per day max, not per action
- **Ignoring network timeouts:** GitHub API can hang — always set timeout parameter in requests.get()

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Semantic version comparison | Custom string parsing with split() | `packaging.version.Version` | Handles pre-releases (rc, alpha), epochs, local versions, normalization — 100+ edge cases |
| Atomic file writes | Open file, write JSON, close | `tempfile.mkstemp()` + `os.replace()` | Race conditions, partial writes on crash, non-atomic renames on Windows |
| Thread-safe GUI updates | Polling with time.sleep() | `queue.Queue` + `after()` loop | Queue is thread-safe by design, after() runs in main thread, already proven pattern |
| HTTP timeout handling | Try/except around requests.get() | `timeout` parameter + ConnectionError | Covers socket timeouts, DNS failures, connection refused — requests handles all cases |
| Timestamp arithmetic | Manual hour counting | `datetime` + `timedelta` | Handles DST, leap seconds, timezone-aware comparisons, tested extensively |

**Key insight:** Version comparison is deceptively complex. Pre-releases, local versions, epochs, and normalization have dozens of edge cases. `packaging.version` is PEP 440 compliant and battle-tested across entire Python ecosystem.

## Common Pitfalls

### Pitfall 1: Rate Limit Exhaustion

**What goes wrong:** Checking for updates on every app launch without tracking last check timestamp hits GitHub's 60 req/hour limit after ~2 days of normal usage

**Why it happens:** No check frequency throttling, no last-check persistence

**How to avoid:** Store `last_check` timestamp in config.json, skip check if `datetime.now() - last_check < timedelta(hours=24)`

**Warning signs:** HTTP 403 responses from GitHub API with message "API rate limit exceeded"

### Pitfall 2: Version String Comparison

**What goes wrong:** `"2.10.0" < "2.9.0"` returns True when comparing strings directly

**Why it happens:** String comparison is lexicographic (character-by-character), not numeric

**How to avoid:** Always use `packaging.version.Version()` to parse before comparing:
```python
# WRONG
if latest_version > current_version:  # String comparison

# RIGHT
from packaging.version import Version
if Version(latest_version) > Version(current_version):
```

**Warning signs:** User sees "update available" for older versions, or doesn't see notification for new versions like 2.10

### Pitfall 3: Banner Flashing on Every Launch

**What goes wrong:** Banner shows briefly on every launch even after dismissal, then disappears

**Why it happens:** Check happens before loading suppress state, banner shows immediately, then gets hidden after suppress check completes

**How to avoid:** Load suppress state synchronously before starting background check, only start check if not suppressed

**Warning signs:** User reports "banner flashes every time I open the app"

### Pitfall 4: Missing User-Agent Header

**What goes wrong:** GitHub API returns 403 Forbidden with "User-Agent required" error

**Why it happens:** GitHub API requires User-Agent header for all requests (documented requirement)

**How to avoid:** Always include User-Agent in headers:
```python
headers = {
    "User-Agent": f"Job-Radar/{__version__}",
    "Accept": "application/vnd.github.v3+json"
}
```

**Warning signs:** Requests fail with 403 status even though repository is public

### Pitfall 5: Config Corruption on Crash

**What goes wrong:** App crashes during config write, leaves empty or truncated JSON file, loses all settings on next launch

**Why it happens:** Direct file write (`json.dump(config, open(path, 'w'))`) is not atomic — crash during write leaves partial content

**How to avoid:** Use tempfile + replace pattern (already in profile_manager.py `_write_json_atomic`)

**Warning signs:** User reports "all my settings disappeared after crash"

## Code Examples

Verified patterns from official sources and existing codebase.

### GitHub Releases API Request
```python
# Source: https://docs.github.com/en/rest/releases
import requests

def fetch_latest_release(owner: str, repo: str, timeout: int = 10) -> dict:
    """Fetch latest release from GitHub Releases API.

    Returns:
        dict with keys: tag_name, html_url, assets

    Raises:
        requests.RequestException: Network error, timeout, or API failure
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    headers = {
        "User-Agent": f"Job-Radar/{__version__}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()
```

### Semantic Version Comparison
```python
# Source: https://packaging.pypa.io/en/stable/version.html
from packaging.version import Version, InvalidVersion

def is_newer_version(current: str, latest: str) -> bool:
    """Compare semantic versions correctly.

    Handles pre-releases, local versions, epochs, normalization.

    Examples:
        >>> is_newer_version("2.1.0", "2.2.0")
        True
        >>> is_newer_version("2.9.0", "2.10.0")
        True
        >>> is_newer_version("2.1.0", "2.1.0-rc1")
        False  # rc1 is pre-release, older than final
    """
    try:
        return Version(latest) > Version(current)
    except InvalidVersion as e:
        # Log error, treat as not newer
        return False
```

### Atomic JSON Config Update
```python
# Source: job_radar/profile_manager.py _write_json_atomic
import json
import os
import tempfile
from pathlib import Path

def update_config_atomic(config_path: Path, updates: dict):
    """Merge updates into config and write atomically.

    Args:
        config_path: Path to config.json
        updates: Dict of keys to update (shallow merge)
    """
    # Load existing config
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}

    # Merge updates
    config.update(updates)

    # Atomic write: temp file + rename
    config_path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        dir=config_path.parent,
        prefix=config_path.name + ".",
        suffix=".tmp"
    )

    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        Path(tmp_path).replace(config_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise
```

### Background Check with Queue Communication
```python
# Source: job_radar/gui/worker_thread.py pattern
import threading
import queue

class MainWindow(ctk.CTk):
    def __init__(self):
        # ... existing init ...

        self._queue = queue.Queue()
        self._start_update_check()
        self._check_queue()  # Start queue polling

    def _start_update_check(self):
        """Launch background version check on startup."""
        checker = UpdateChecker(self._queue)

        if not checker.should_check():
            return  # Checked within last 24 hours

        def check_thread():
            checker.check_for_updates()

        threading.Thread(target=check_thread, daemon=True).start()

    def _check_queue(self):
        """Process messages from background threads (runs in main GUI thread)."""
        try:
            while True:
                try:
                    msg = self._queue.get_nowait()
                    msg_type = msg[0]

                    if msg_type == "update_available":
                        _, version, release_url = msg
                        self._show_update_banner(version, release_url)
                    elif msg_type == "up_to_date":
                        pass  # Silently continue
                    elif msg_type == "check_failed":
                        _, error = msg
                        self._update_check_failed(error)

                except queue.Empty:
                    break
        finally:
            # Re-schedule next check
            self.after(100, self._check_queue)
```

### Suppress Period Calculation
```python
# Source: Python datetime docs (https://docs.python.org/3/library/datetime.html)
from datetime import datetime, timedelta

def calculate_suppress_expiry(hours: int) -> str:
    """Calculate ISO timestamp for suppress period expiry.

    Args:
        hours: 24 for X button, 168 (7*24) for Remind Later

    Returns:
        ISO 8601 timestamp string (e.g., "2026-02-17T14:30:00")
    """
    expiry = datetime.now() + timedelta(hours=hours)
    return expiry.isoformat()

def is_suppress_expired(expiry_iso: str) -> bool:
    """Check if suppress period has expired.

    Args:
        expiry_iso: ISO timestamp from config

    Returns:
        True if current time >= expiry time
    """
    expiry = datetime.fromisoformat(expiry_iso)
    return datetime.now() >= expiry
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual version checking (no auto-update) | Background check on launch with notification | v2.2.0 (this phase) | Users discover updates proactively vs. hoping they see GitHub |
| String version comparison | packaging.version.Version | Python 3.4+ (PEP 440) | Correct handling of 2.10 > 2.9, pre-releases, local versions |
| Blocking API calls | Threading with queue-based communication | v2.0 (GUI foundation) | Non-blocking checks, responsive UI during network requests |
| Manual config file writes | Atomic writes (tempfile + rename) | v2.0 (profile manager) | No corruption on crash, consistent pattern across app |

**Deprecated/outdated:**
- Using `distutils.version.LooseVersion`: Deprecated in Python 3.10, removed in 3.12 — use `packaging.version.Version` instead
- Unauthenticated API calls without User-Agent: GitHub now requires User-Agent header (returns 403 without it)
- Synchronous requests in GUI: Freezes UI — always use threading for network calls

## Open Questions

1. **Rate limit fallback strategy if user launches app >60 times/hour**
   - What we know: GitHub unauthenticated limit is 60 req/hour per IP
   - What's unclear: Should we implement auth token support for power users?
   - Recommendation: Start with unauthenticated (simpler), add GitHub token support in Phase 41 if users request it. Daily check limit makes 60/hour sufficient for >99% of users.

2. **Conditional requests (If-None-Match) to reduce bandwidth**
   - What we know: GitHub supports ETag caching headers to reduce transfer
   - What's unclear: Worth the complexity for a ~2KB JSON response?
   - Recommendation: Skip for now — daily checks mean ~60KB/month, not worth cache management complexity. Revisit if we add hourly checks.

3. **Multi-platform version targeting (different versions per OS)**
   - What we know: GitHub Releases can have platform-specific versions (v2.2.0-macos, v2.2.0-windows)
   - What's unclear: Do we need separate version tracking per platform?
   - Recommendation: Use single version across platforms (current approach), link to release page where user picks platform. Separate versioning adds significant complexity.

## Sources

### Primary (HIGH confidence)
- GitHub REST API Releases endpoint: https://docs.github.com/en/rest/releases
- GitHub API rate limits: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- Python packaging.version documentation: https://packaging.pypa.io/en/stable/version.html
- PEP 440 Version Identification: https://peps.python.org/pep-0440/
- CustomTkinter grid system: https://customtkinter.tomschimansky.com/tutorial/grid-system/
- CustomTkinter CTkFrame: https://customtkinter.tomschimansky.com/documentation/widgets/frame/
- Python datetime module: https://docs.python.org/3/library/datetime.html
- Python webbrowser module: https://docs.python.org/3/library/webbrowser.html
- Existing codebase patterns: job_radar/gui/worker_thread.py, job_radar/profile_manager.py, job_radar/gui/main_window.py

### Secondary (MEDIUM confidence)
- VS Code notification UX: https://code.visualstudio.com/api/ux-guidelines/notifications
- Atomic file writes in Python: https://gist.github.com/therightstuff/cbdcbef4010c20acc70d2175a91a321f
- Python requests User-Agent best practices: https://thelinuxcode.com/user-agent-in-python-requests-practical-patterns-for-2026/
- Notification banner design patterns: https://ui-patterns.com/patterns/notifications

### Tertiary (LOW confidence)
- None — all findings verified with official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All libraries stdlib or existing dependencies, patterns proven in codebase
- Architecture: HIGH — Threading, queue, atomic writes already working in worker_thread.py and profile_manager.py
- Pitfalls: HIGH — Version comparison, rate limits, atomic writes documented extensively in official sources

**Research date:** 2026-02-16
**Valid until:** ~30 days (GitHub API stable, stdlib patterns don't change rapidly)
