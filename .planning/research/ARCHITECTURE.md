# Architecture Patterns

**Domain:** Desktop job search application (auto-update + hiring.cafe integration)
**Researched:** 2026-02-15

## Recommended Architecture

This milestone adds two new capabilities to the existing Job Radar desktop application:
1. **Auto-update system** for version checking and installer download
2. **hiring.cafe integration** as a new job source

### Integration Points with Existing Architecture

```
job_radar/
├── __main__.py              [EXISTING] Entry point (CLI/GUI routing)
├── __init__.py              [EXISTING] Version string (__version__ = "2.1.7")
├── gui/
│   ├── main_window.py       [MODIFY] Add update banner + Settings button
│   └── worker_thread.py     [EXISTING] Thread pattern for downloads
├── sources.py               [MODIFY] Add hiring.cafe source
├── rate_limits.py           [MODIFY] Add hiring.cafe rate limit
├── config.py                [EXISTING] Config loading (no changes)
└── updater.py               [NEW] Version check + download logic
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **updater.py** | Version check, manifest fetch, installer download | GitHub API, main_window.py |
| **UpdateBanner** (GUI widget) | Display update notification + Download button | updater.py, main_window.py |
| **DownloadWorker** | Background installer download with progress | updater.py, main_window.py (via queue) |
| **hiring.cafe source** | Fetch jobs from hiring.cafe API | sources.py (SOURCES list), rate_limits.py |

---

## Auto-Update Integration

### Pattern: GitHub Releases with Version Manifest

**Why GitHub Releases:**
- Job Radar already uses GitHub releases for distribution (README.md confirms)
- No server hosting costs
- Built-in asset CDN
- Existing release process in place

**Architecture:**
```
1. Version Check (on GUI startup):
   - Compare __version__ to latest GitHub release
   - Use GitHub API: GET /repos/owner/repo/releases/latest
   - Parse tag_name (e.g., "v2.1.8") → semver comparison

2. Update UI (if new version available):
   - Banner widget in main_window.py (row 0.5, between header and tabs)
   - "Update available: v2.1.8 → Download" button
   - Dismissible (session-only, no persistent state)

3. Download Flow:
   - User clicks "Download" → DownloadWorker thread starts
   - Fetch installer asset from GitHub release
   - Progress callback updates banner (% complete)
   - Save to temp directory (tempfile.NamedTemporaryFile)

4. Installer Launch (platform-specific):
   - Windows: subprocess.Popen([installer_path], shell=False)
   - macOS: subprocess.Popen(["open", dmg_path])
   - Linux: Show "Extract and run" message (no auto-open)
   - Exit app after launching installer
```

### Data Flow

```
┌─────────────────┐
│ MainWindow      │
│ __init__()      │
└────────┬────────┘
         │ Check on startup
         ▼
┌─────────────────┐      ┌──────────────────┐
│ updater.py      │─────>│ GitHub API       │
│ check_version() │<─────│ releases/latest  │
└────────┬────────┘      └──────────────────┘
         │ Returns: {"has_update": bool, "version": str, "download_url": str}
         ▼
┌─────────────────┐
│ UpdateBanner    │ (if has_update)
│ [v2.1.8 ready]  │
│ [Download btn]  │
└────────┬────────┘
         │ User clicks Download
         ▼
┌─────────────────┐      ┌──────────────────┐
│ DownloadWorker  │─────>│ GitHub CDN       │
│ (thread)        │<─────│ (installer file) │
└────────┬────────┘      └──────────────────┘
         │ Progress messages via queue
         ▼
┌─────────────────┐
│ UpdateBanner    │
│ [Downloading... │
│  52% ▓▓▓▓░░░]   │
└────────┬────────┘
         │ Complete
         ▼
┌─────────────────┐
│ subprocess      │
│ open(installer) │
│ app.quit()      │
└─────────────────┘
```

### New Components Needed

#### updater.py (new module)

```python
"""Auto-update functionality for Job Radar desktop app."""

def check_version() -> dict:
    """Check GitHub for newer version.

    Returns:
        {"has_update": bool, "version": str, "download_url": str, "size_bytes": int}
    """
    # GET https://api.github.com/repos/{owner}/{repo}/releases/latest
    # Parse tag_name (strip 'v' prefix)
    # Compare to __version__ using semantic versioning
    # Find correct asset for platform (e.g., Job-Radar-Setup-v2.1.8.exe)
    pass

def download_installer(url: str, progress_callback) -> str:
    """Download installer to temp directory.

    Args:
        url: GitHub release asset URL
        progress_callback: Called with (downloaded_bytes, total_bytes)

    Returns:
        Path to downloaded installer
    """
    # Use requests.get(url, stream=True)
    # Save to tempfile.NamedTemporaryFile(delete=False, suffix='.exe'|'.dmg')
    # Call progress_callback during download
    pass

def launch_installer(installer_path: str):
    """Open installer (platform-specific)."""
    # Windows: subprocess.Popen([installer_path])
    # macOS: subprocess.Popen(["open", installer_path])
    # Linux: Show message (no auto-open)
    pass
```

#### gui/update_banner.py (new widget)

```python
"""Update notification banner for GUI."""

class UpdateBanner(ctk.CTkFrame):
    """Banner showing available update with download button."""

    def __init__(self, parent, version_info: dict):
        # Display: "Update available: v{version}"
        # Download button → starts DownloadWorker
        # Dismiss button (X) → destroy widget
        pass

    def _on_download(self):
        # Start DownloadWorker thread
        # Switch to progress display
        pass

    def _update_progress(self, downloaded: int, total: int):
        # Update progress bar
        pass
```

#### gui/download_worker.py (new thread)

```python
"""Background worker for downloading installer."""

class DownloadWorker:
    """Downloads installer in background thread with progress reporting."""

    def __init__(self, queue, url, version):
        self._queue = queue
        self._url = url
        self._version = version

    def run(self):
        # Download installer using updater.download_installer()
        # Send progress messages: ("download_progress", downloaded, total)
        # On complete: ("download_complete", installer_path)
        # On error: ("download_error", error_msg)
        pass
```

### Where to Display Update UI

**Rejected Approaches:**
- ❌ Modal dialog (blocks GUI startup)
- ❌ Settings tab button (hidden, users won't see)
- ❌ Toast notification (easy to miss, no persistent state)

**Recommended Approach:**
✅ **Banner between header and tabs** (row 0.5)

```python
# main_window.py __init__()
self.grid_rowconfigure(0, weight=0)      # Header (existing)
self.grid_rowconfigure(1, weight=0)      # Update banner (NEW)
self.grid_rowconfigure(2, weight=1)      # Tabs (existing, renumber from 1)

# After header creation
self._create_header()
self._check_for_updates()  # NEW
self._show_main_tabs()
```

**Banner behavior:**
- Appears only when update available
- Dismissible (session-only, re-checks on next startup)
- Non-blocking (user can ignore and use app normally)
- Prominent but not annoying

### Platform-Specific Considerations

| Platform | Installer Format | Download Pattern | Launch Pattern |
|----------|-----------------|------------------|----------------|
| **Windows** | `.exe` (NSIS) | Direct download | `subprocess.Popen([path])` then `app.quit()` |
| **macOS** | `.dmg` | Direct download | `subprocess.Popen(["open", path])` then `app.quit()` |
| **Linux** | `.tar.gz` | Direct download | Show "Extract to ~/Applications and run" message (no auto-launch) |

**Asset detection:**
```python
import platform

def get_installer_asset_name(version: str) -> str:
    """Get platform-specific installer asset name."""
    system = platform.system()
    if system == "Windows":
        return f"Job-Radar-Setup-v{version}.exe"
    elif system == "Darwin":
        return f"Job-Radar-v{version}-macos.dmg"
    elif system == "Linux":
        return f"job-radar-v{version}-linux.tar.gz"
    else:
        raise ValueError(f"Unsupported platform: {system}")
```

### Threading Pattern (Reuse Existing)

Job Radar already has a proven threading pattern in **worker_thread.py**:
- Queue-based messaging (GUI thread polls queue)
- Cooperative cancellation (threading.Event)
- Progress callbacks

**Reuse this pattern:**
```python
# DownloadWorker follows same pattern as SearchWorker
class DownloadWorker:
    def __init__(self, queue, stop_event, url, version):
        self._queue = queue
        self._stop_event = stop_event
        # ...

    def run(self):
        # Same structure as SearchWorker.run()
        # Send progress via queue: ("download_progress", pct)
        # Check stop_event for cancellation
        pass
```

### Rate Limiting

**Not needed for GitHub API:**
- Unauthenticated requests: 60/hour (sufficient for version checks)
- Once per startup = ~5/hour typical usage
- No rate limiting infrastructure required

---

## hiring.cafe Integration

### Pattern: New Source in sources.py Registry

hiring.cafe follows the same pattern as existing sources (Dice, HN Hiring, RemoteOK, etc.).

### Research Findings

**Source:** [GitHub hiring.cafe scraper](https://github.com/umur957/hiring-cafe-job-scraper), [Apify API docs](https://apify.com/memo23/apify-hiring-cafe-scraper/api)

**Key findings:**
- hiring.cafe has an **official API** for job listings
- **Fields available:** job title, company, location, pay (salary), description, requirements, job ID, application URL, employment type, company size, coordinates
- **Data format:** JSON API (not HTML scraping)
- **Authentication:** Unknown (likely API key or public endpoint)
- **Rate limits:** Unknown (needs research during implementation)

**Comparison to existing sources:**
- Similar to **Adzuna/Authentic Jobs** (JSON API with structured data)
- NOT like **Dice/HN Hiring** (HTML scraping)

### Integration Steps

#### 1. Add fetch_hiringcafe() to sources.py

```python
def fetch_hiringcafe(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from hiring.cafe API."""
    results = []

    # Check credentials (if API key required)
    api_key = get_api_key("HIRINGCAFE_API_KEY", "hiring.cafe")
    if not api_key:
        return results  # No key = skip gracefully

    # Check rate limit
    if not check_rate_limit("hiringcafe", verbose=verbose):
        return results

    # Build API URL (pattern TBD during implementation)
    params = {
        "query": query,
        "location": location,
        # Additional params TBD
    }
    url = "https://hiring.cafe/api/jobs?" + urllib.parse.urlencode(params)

    # Fetch with retry (reuse existing cache infrastructure)
    body = fetch_with_retry(url, headers=HEADERS, use_cache=True)
    if body is None:
        log.debug("[hiring.cafe] Fetch failed for '%s'", query)
        return results

    # Parse JSON response
    data = json.loads(body)
    items = data.get("jobs", [])  # Field name TBD

    for item in items:
        job = map_hiringcafe_to_job_result(item)
        if job:
            results.append(job)

    log.info("[hiring.cafe] Found %d results for '%s'", len(results), query)
    return results
```

#### 2. Add mapper function

```python
def map_hiringcafe_to_job_result(item: dict) -> JobResult | None:
    """Map hiring.cafe API response to JobResult.

    Validates required fields (title, company, url).
    """
    title = item.get("title", "").strip()
    company = item.get("company", "").strip()
    url = item.get("apply_url", "").strip()

    if not title or not company or not url:
        log.debug("[hiring.cafe] Skipping job with missing fields")
        return None

    # Location normalization (reuse existing parse_location_to_city_state)
    location_raw = item.get("location", "")
    location = parse_location_to_city_state(location_raw)

    # Salary fields (hiring.cafe provides structured salary data)
    salary_min = item.get("salary_min")  # Field name TBD
    salary_max = item.get("salary_max")
    salary_currency = item.get("salary_currency", "USD")

    # Format salary string
    if salary_min and salary_max:
        salary = f"{salary_currency} {int(salary_min):,}-{int(salary_max):,}/yr"
    elif salary_min:
        salary = f"{salary_currency} {int(salary_min):,}+/yr"
    else:
        salary = "Not specified"

    # Description cleaning (reuse existing strip_html_and_normalize)
    description_raw = item.get("description", "")
    description = strip_html_and_normalize(description_raw)[:500]

    # Arrangement detection
    arrangement = _parse_arrangement(f"{title} {description} {location}")

    # Employment type
    emp_type = item.get("employment_type", "")

    # Date posted
    date_posted = item.get("posted_date", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="hiringcafe",
        employment_type=emp_type,
        parse_confidence="high",  # Structured API = high confidence
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
    )
```

#### 3. Add to SOURCES registry

```python
# In sources.py build_search_queries()
# Add hiring.cafe queries (pattern: top 2 target titles, like RemoteOK)
for title in titles[:2]:
    queries.append({
        "source": "hiringcafe",
        "query": title,
        "location": location,
    })
```

#### 4. Add rate limiting configuration

```python
# In rate_limits.py RATE_LIMITS
RATE_LIMITS = {
    # ... existing ...
    "hiringcafe": [Rate(60, Duration.MINUTE)],  # Conservative default (adjust after testing)
}

# In rate_limits.py BACKEND_API_MAP
BACKEND_API_MAP = {
    # ... existing ...
    "hiringcafe": "hiringcafe",  # Single source, own limiter
}
```

#### 5. Add to source display names

```python
# In sources.py _SOURCE_DISPLAY_NAMES
_SOURCE_DISPLAY_NAMES = {
    # ... existing ...
    "hiringcafe": "hiring.cafe",
}
```

#### 6. Add API key configuration (if needed)

**If hiring.cafe requires API key:**
```python
# In gui/main_window.py _build_settings_tab()
# Add hiring.cafe section (same pattern as Adzuna/Authentic Jobs)
self._add_api_section(
    scroll_frame,
    "hiring.cafe",
    [("HIRINGCAFE_API_KEY", "API Key", "hiringcafe")],
    "Sign up at: https://hiring.cafe/api"
)
```

### Salary Field Mapping

hiring.cafe provides **structured salary data** (unlike most sources that have free-text):
- `salary_min`: Minimum salary (numeric)
- `salary_max`: Maximum salary (numeric)
- `salary_currency`: Currency code (e.g., "USD")

**Integration:**
✅ JobResult already has optional salary fields:
```python
@dataclass
class JobResult:
    # ... existing fields ...
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
```

**No changes needed** — just populate these fields in the mapper.

### Data Extraction Pattern

**Confirmed:** JSON API (not HTML scraping)

**Rationale:**
- Multiple scraper tools reference "official API"
- Apify provides structured API endpoint
- Data fields are well-defined (job title, company, salary, etc.)

**Pattern:**
```python
# Same pattern as Adzuna, Authentic Jobs, JSearch, USAJobs
# 1. Build API URL with query params
# 2. Fetch with retry (use existing cache)
# 3. Parse JSON response
# 4. Map fields to JobResult
# 5. Return list[JobResult]
```

### Unknown During Research (Needs Phase-Specific Investigation)

1. **API endpoint URL** — Need to inspect hiring.cafe site or API docs
2. **Authentication method** — API key? Public endpoint? OAuth?
3. **Rate limits** — Requests per minute/hour/day
4. **Field names** — Exact JSON keys for title, company, salary, etc.
5. **Query parameters** — How to filter by location, keywords, date range?

**Mitigation:**
- Start with conservative rate limit (60/min)
- Use graceful fallback (missing API key = skip source)
- Follow existing pattern (if API key missing, log.debug + return [])

---

## Patterns to Follow

### Pattern 1: Threaded Operations with Queue Messaging

**What:** Background work (download, search) runs in daemon thread, communicates via queue.Queue

**When:** Any long-running operation that would block GUI

**Example:**
```python
# GUI thread: Start worker
queue = queue.Queue()
stop_event = threading.Event()
worker = DownloadWorker(queue, stop_event, url, version)
thread = threading.Thread(target=worker.run, daemon=True)
thread.start()

# GUI thread: Poll queue
def _check_queue(self):
    try:
        msg = self._queue.get_nowait()
        msg_type = msg[0]
        if msg_type == "download_progress":
            self._update_progress_bar(msg[1], msg[2])
        elif msg_type == "download_complete":
            self._launch_installer(msg[1])
    except queue.Empty:
        pass
    finally:
        self.after(100, self._check_queue)  # Poll every 100ms
```

**Why:** CustomTkinter widgets must only be updated from main thread. Queue enables thread-safe communication.

### Pattern 2: Source Registry with Unified Interface

**What:** All job sources implement same function signature and return list[JobResult]

**When:** Adding new job sources (like hiring.cafe)

**Example:**
```python
def fetch_hiringcafe(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    # Same signature as fetch_adzuna, fetch_remoteok, etc.
    # Returns list[JobResult] or [] on error
    pass
```

**Why:** Enables parallel fetching in fetch_all() and unified deduplication.

### Pattern 3: Graceful API Failures

**What:** Missing API keys, rate limits, and network errors return empty list (no crashes)

**When:** All external API calls

**Example:**
```python
def fetch_hiringcafe(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    # Check credentials
    api_key = get_api_key("HIRINGCAFE_API_KEY", "hiring.cafe")
    if not api_key:
        return []  # Skip gracefully, don't crash

    # Check rate limit
    if not check_rate_limit("hiringcafe", verbose=verbose):
        return []  # Rate limited, try next time

    try:
        # Fetch logic
        pass
    except Exception as e:
        log.debug("[hiring.cafe] Error: %s", e)
        return []  # Log + return empty, don't crash
```

**Why:** Job search should succeed even if some sources fail. User sees "0 jobs from X" instead of crash.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Blocking the GUI Thread

**What goes wrong:** Long-running operations (network I/O, file downloads) run in main thread → GUI freezes

**Why it happens:** Direct calls to requests.get() or file I/O from event handlers

**Consequences:**
- App appears hung (spinning wheel on macOS, "Not Responding" on Windows)
- User can't cancel operation
- Poor user experience

**Prevention:**
```python
# ❌ BAD: Direct download in button handler
def _on_download_clicked(self):
    installer = download_installer(url)  # Blocks GUI!
    launch_installer(installer)

# ✅ GOOD: Delegate to worker thread
def _on_download_clicked(self):
    worker = DownloadWorker(self._queue, url, version)
    thread = threading.Thread(target=worker.run, daemon=True)
    thread.start()
    self._show_progress_ui()
```

**Detection:** If GUI becomes unresponsive during operation, operation is blocking.

### Anti-Pattern 2: Hardcoded API Endpoints and Field Names

**What goes wrong:** API changes break integration, hard to test

**Why it happens:** Magic strings scattered throughout code

**Consequences:**
- Brittle integration (API field rename breaks everything)
- Hard to mock for testing
- Difficult to debug

**Prevention:**
```python
# ❌ BAD: Magic strings everywhere
url = "https://hiring.cafe/api/jobs?q=" + query
title = item["jobTitle"]  # Breaks if API changes to "title"

# ✅ GOOD: Constants + mapper abstraction
API_BASE_URL = "https://hiring.cafe/api/jobs"

def map_hiringcafe_to_job_result(item: dict) -> JobResult | None:
    # Centralized field mapping
    title = item.get("jobTitle") or item.get("title") or ""  # Fallback
    # ... validate ...
    return JobResult(...)
```

**Detection:** If single API field rename requires changes in multiple files, fields are hardcoded.

### Anti-Pattern 3: Silent Failures in Update Checks

**What goes wrong:** Version check fails (network error, rate limit), user never knows updates exist

**Why it happens:** Exception swallowed, no logging, no fallback UI

**Consequences:**
- Users run outdated versions with known bugs
- Security vulnerabilities not patched
- No visibility into update system health

**Prevention:**
```python
# ❌ BAD: Silent failure
def check_version():
    try:
        response = requests.get(GITHUB_API_URL)
        return parse_version(response.json())
    except:
        return None  # User never sees error

# ✅ GOOD: Log failures, show fallback UI
def check_version():
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        return parse_version(response.json())
    except requests.Timeout:
        log.warning("Version check timed out - network issue?")
        return None
    except requests.HTTPError as e:
        log.error("Version check failed: HTTP %s", e.response.status_code)
        return None
    except Exception as e:
        log.error("Version check failed: %s", e)
        return None

# In GUI: Show "Check for updates" button in Settings if auto-check fails
```

**Detection:** If update check fails and user doesn't know why, failures are silent.

---

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| **Update bandwidth** | Negligible (GitHub CDN) | Negligible (GitHub CDN) | Negligible (GitHub CDN) |
| **Version check rate** | ~50 req/hour (60/hour limit) | ~5K req/hour (requires auth) | Needs dedicated version manifest server |
| **hiring.cafe API** | Conservative rate limits OK | May need higher tier API plan | Likely blocked (too many requests) |

**For current milestone (MVP):**
- GitHub free tier sufficient (unauthenticated: 60 req/hour)
- hiring.cafe unknown limits — start conservative (60/min)
- Both will scale to 1000s of users without issue

**Future scaling:**
- Version checks: Move to authenticated GitHub API (5000/hour) or CDN manifest
- hiring.cafe: Request higher rate limits from provider

---

## Build Order Recommendations

**Phase structure suggestion:**

### Phase 1: Auto-Update Infrastructure
**Why first:** Independent of hiring.cafe, immediate value to users

1. **updater.py module** (version check + download)
2. **UpdateBanner widget** (UI component)
3. **DownloadWorker thread** (background download)
4. **Integration in main_window.py** (startup check)

**Deliverable:** Users see update notifications and can download installers

**Validation:** Mock GitHub API, test with staged release

---

### Phase 2: hiring.cafe Integration
**Why second:** Depends on research (API endpoint, auth, fields)

1. **Research:** Inspect hiring.cafe API (endpoint, auth, fields, rate limits)
2. **fetch_hiringcafe() function** (source implementation)
3. **map_hiringcafe_to_job_result()** (field mapping)
4. **Rate limiting** (add to RATE_LIMITS)
5. **Settings UI** (API key configuration, if needed)
6. **Integration in fetch_all()** (add to query list)

**Deliverable:** hiring.cafe jobs appear in search results with salary data

**Validation:** Real API call, verify deduplication works, check salary display

---

## Sources

**Auto-update research:**
- [tufup - Automated updates for Python applications](https://github.com/dennisvang/tufup)
- [PyUpdater - Auto-update library](http://www.pyupdater.org/)
- [updater4pyi - PyInstaller auto-update](https://pypi.org/project/updater4pyi/)
- [PyInstaller documentation](https://pyinstaller.org/en/stable/index.html)
- [PyInstaller version file management](https://pypi.org/project/pyinstaller_versionfile/)

**hiring.cafe research:**
- [GitHub hiring.cafe scraper](https://github.com/umur957/hiring-cafe-job-scraper)
- [Apify hiring.cafe API](https://apify.com/memo23/apify-hiring-cafe-scraper/api)
- [HiringCafe scaling blog](https://blog.hiring.cafe/p/scaling-hiringcafe-from-0-to-1m-users)

**Existing architecture:**
- Job Radar codebase (sources.py, rate_limits.py, worker_thread.py, main_window.py)
- PyInstaller spec file (job-radar.spec)
