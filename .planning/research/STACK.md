# Stack Research: Auto-Update & hiring.cafe Integration

**Domain:** Desktop application auto-update infrastructure + unofficial job board API integration
**Researched:** 2026-02-15
**Confidence:** HIGH

## Executive Summary

This research identifies minimal, zero-bloat additions to Job Radar's existing Python stack for v2.2.0. **No new external dependencies required for auto-update**—Python stdlib (urllib, subprocess, platform) + existing requests library handle everything. **No new dependencies for hiring.cafe**—existing requests + BeautifulSoup stack already sufficient. Only additions: `packaging` for robust version comparison and optionally `tqdm` for download progress UX.

## Recommended Stack Additions

### Core Technologies (New)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| packaging | 26.0 | Semantic version comparison | PEP 440-compliant version parsing; 3x faster than alternatives; Python stdlib-adjacent (PyPA official); handles edge cases like epochs and pre-releases that naive string comparison misses |

### Supporting Libraries (Optional)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tqdm | 4.67.3 | Download progress visualization | GUI download progress indicator; 60ns overhead per iteration; integrates with urllib.request via reporthook; optional—can ship without if download UX doesn't need progress bars |

### Existing Stack (Reused)

| Technology | Already in pyproject.toml | Purpose for New Features |
|------------|---------------------------|--------------------------|
| requests | ✓ (no version pin) | GitHub Releases API calls for version checking; hiring.cafe POST requests with JSON payload |
| platformdirs | ✓ (≥4.0) | Not needed for v2.2.0, but available if update manifest needs local cache |
| pyrate-limiter | ✓ (no version pin) | Rate limiting for hiring.cafe API (reuse existing SQLiteBucket infrastructure) |
| beautifulsoup4 | ✓ (no version pin) | Fallback if hiring.cafe changes API to server-rendered HTML |
| customtkinter | ✓ (no version pin) | Update notification dialog in GUI; reuse CTkToplevel or native messagebox |

### Python Standard Library (Zero Dependencies)

| Module | Purpose | Why Not External Library |
|--------|---------|--------------------------|
| urllib.request | Download installers (DMG/NSIS/tar.gz) from GitHub Releases | Stdlib; no requests needed for simple GET with progress hook |
| subprocess | Open downloaded installer with OS default (macOS `open`, Windows `start`, Linux `xdg-open`) | Cross-platform file opening; no extra deps |
| platform | Detect OS (Darwin/Windows/Linux) to select correct installer asset | Stdlib; more reliable than sys.platform for version detection |
| json | Parse GitHub Releases API responses | Stdlib; requests.json() already uses this |
| threading | Background version check without blocking GUI | Already used in Job Radar (SearchWorker); reuse pattern |

## Installation

```bash
# Minimal: just version comparison (REQUIRED)
pip install "packaging>=26.0"

# Optional: add download progress bars (NICE-TO-HAVE)
pip install "tqdm>=4.67.3"

# No other changes needed—existing stack handles everything
```

**pyproject.toml update:**
```toml
dependencies = [
    "requests",
    "beautifulsoup4",
    "platformdirs>=4.0",
    "pyfiglet",
    "colorama",
    "certifi",
    "questionary",
    "python-dotenv",
    "pyrate-limiter",
    "rapidfuzz",
    "pdfplumber>=0.11.9",
    "python-dateutil>=2.9.0",
    "tabulate>=0.9.0",
    "customtkinter",
    "packaging>=26.0"  # NEW: semantic version comparison for auto-update
]

[project.optional-dependencies]
dev = ["pytest>=9.0", "pytest-mock"]
build = ["pyinstaller", "pillow"]
gui = ["tqdm>=4.67.3"]  # NEW: optional download progress bars for GUI
```

## Auto-Update: Technical Specification

### Version Checking Flow

**Endpoint:** `GET https://api.github.com/repos/coryebert/Job-Radar/releases/latest`
**Library:** `requests` (already in stack)
**Authentication:** None required (public repo)
**Rate limit:** 60 req/hour unauthenticated; uses ETag caching (doesn't count against limit)

**Response structure:**
```json
{
  "tag_name": "v2.2.0",
  "name": "Job Radar v2.2.0",
  "assets": [
    {
      "name": "Job-Radar-2.2.0.dmg",
      "browser_download_url": "https://github.com/.../Job-Radar-2.2.0.dmg",
      "content_type": "application/x-apple-diskimage",
      "size": 45678901
    },
    {
      "name": "Job-Radar-2.2.0-setup.exe",
      "browser_download_url": "https://github.com/.../Job-Radar-2.2.0-setup.exe",
      "content_type": "application/x-msdownload",
      "size": 34567890
    },
    {
      "name": "job-radar-2.2.0-linux.tar.gz",
      "browser_download_url": "https://github.com/.../job-radar-2.2.0-linux.tar.gz",
      "content_type": "application/gzip",
      "size": 23456789
    }
  ]
}
```

**Version comparison:**
```python
from packaging.version import Version

current = Version("2.1.7")  # from pyproject.toml or __version__
latest_tag = "v2.2.0"  # from API response
latest = Version(latest_tag.lstrip("v"))  # strip 'v' prefix

if latest > current:
    # Update available
```

**Why packaging.version?**
- Handles PEP 440 version schemes (2.1.0rc1, 2.1.0.post1, 1!2.0.0 with epochs)
- 3x faster than semver library (26.0 performance improvements)
- No regex footguns from naive string splitting
- PyPA official implementation

### Installer Download Flow

**Method 1: urllib with progress (recommended for GUI)**
```python
import urllib.request
from tqdm import tqdm

def download_with_progress(url, dest):
    with tqdm(unit='B', unit_scale=True, unit_divisor=1024, miniters=1) as t:
        urllib.request.urlretrieve(
            url,
            dest,
            reporthook=lambda b, bsize, tsize: t.update(bsize)
        )
```

**Method 2: requests streaming (if urllib insufficient)**
```python
import requests
from tqdm import tqdm

response = requests.get(url, stream=True)
total = int(response.headers.get('content-length', 0))
with open(dest, 'wb') as f, tqdm(total=total, unit='B', unit_scale=True) as bar:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
        bar.update(len(chunk))
```

**Asset selection logic:**
```python
import platform

system = platform.system()  # 'Darwin', 'Windows', 'Linux'
arch = platform.machine()   # 'x86_64', 'arm64', etc.

asset_patterns = {
    'Darwin': '.dmg',
    'Windows': '.exe',
    'Linux': '.tar.gz'
}

matching_asset = next(
    a for a in assets
    if asset_patterns[system] in a['name']
)
```

### Installer Launch Flow

**Cross-platform opener:**
```python
import subprocess
import platform

def open_installer(filepath):
    system = platform.system()

    if system == 'Darwin':
        subprocess.Popen(['open', filepath])
    elif system == 'Windows':
        subprocess.Popen(['start', filepath], shell=True)
    else:  # Linux
        subprocess.Popen(['xdg-open', filepath])
```

**Why subprocess, not os.startfile()?**
- `os.startfile()` is Windows-only (AttributeError on macOS/Linux)
- subprocess with platform detection is cross-platform standard
- Non-blocking (user can continue using app while installer opens)

### GUI Integration Points

**Update notification options:**

1. **Native tkinter.messagebox** (zero deps, already in Python):
   ```python
   from tkinter import messagebox

   result = messagebox.askyesno(
       "Update Available",
       f"Job Radar {latest_version} is available (you have {current_version}).\n\nDownload now?"
   )
   ```

2. **CustomTkinter dialog** (reuse existing CTkToplevel pattern):
   ```python
   from customtkinter import CTkToplevel, CTkLabel, CTkButton

   # Custom dialog with theme consistency
   ```

3. **CTkMessagebox extension** (if willing to add dependency):
   - PyPI: ctkmessagebox2 (tkinter.messagebox clone for CustomTkinter)
   - Adds dependency; not recommended unless strong UX need

**Recommendation:** Use native `tkinter.messagebox` for v2.2.0. Zero deps, battle-tested, accessible.

### Timing and UX

**When to check:**
- On GUI startup (non-blocking background thread)
- Max once per day (cache last check timestamp)
- Respect user preference (opt-out setting)

**User flow:**
1. App launches
2. Background thread: Check GitHub Releases API
3. If update available: Show dialog with version details
4. User clicks "Download"
5. Download installer to temp dir with progress bar
6. Open installer automatically
7. User completes installation wizard
8. App does NOT auto-restart (user controls when)

**Why user-initiated install, not silent?**
- macOS Gatekeeper requires user approval for unsigned DMG
- Windows SmartScreen requires user approval for unsigned exe
- Linux package managers expect user control
- Security best practice: no silent privilege escalation

## hiring.cafe: Technical Specification

### API Endpoints

**Discovered from reverse engineering:**
Source: [umur957/hiring-cafe-job-scraper](https://github.com/umur957/hiring-cafe-job-scraper) and [jinijinjaney/hiringcafe-job-scraper](https://github.com/jinijinjaney/hiringcafe-job-scraper)

**Count endpoint (optional—for pagination planning):**
```
POST https://hiring.cafe/api/search-jobs/get-total-count
Content-Type: application/json

{
  "searchState": { ... }
}
```

**Jobs endpoint (primary):**
```
POST https://hiring.cafe/api/search-jobs
Content-Type: application/json

{
  "size": 1000,  // max 1000 jobs per request
  "page": 0,     // zero-indexed pagination
  "searchState": {
    "locations": [
      {
        "id": "ChIJCzYy5IS16lQRQrfeQ5K5Oxw",
        "description": "United States"
      }
    ],
    "workplaceTypes": ["Remote", "Hybrid", "Onsite"],
    "commitmentTypes": ["Full Time", "Part Time", "Contract", "Internship"],
    "searchQuery": "",
    "dateFetchedPastNDays": 61,
    "sortBy": "default"
  }
}
```

**Required headers (mimic browser):**
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Origin': 'https://hiring.cafe',
    'Referer': 'https://hiring.cafe/'
}
```

**Response format:**
```json
{
  "results": [
    {
      "v5_processed_job_data": {
        "title": "Senior Software Engineer",
        "description": "...",
        "job_information": {
          "seniority_level": ["Senior"],
          "commitment_type": "Full Time",
          "workplace_type": "Remote",
          "compensation": {
            "min": 120000,
            "max": 180000,
            "currency": "USD"
          }
        }
      },
      "v5_processed_company_data": {
        "name": "Company Name",
        "location": {
          "city": "San Francisco",
          "state": "CA",
          "country": "United States"
        }
      }
    }
  ]
}
```

### Implementation Strategy

**No new dependencies needed:**
```python
import requests  # already in stack
from pyrate_limiter import Duration, Limiter, SQLiteBucket  # already in stack

# Rate limiting (reuse existing infrastructure)
limiter = Limiter(
    SQLiteBucket('hiringcafe', 'rate_limits.db'),
    Duration.MINUTE * 1
)

@limiter.ratelimit('hiringcafe', max_rate=10)  # conservative: 10 req/min
def fetch_hiringcafe_jobs(search_query='', location='United States', days=14):
    url = 'https://hiring.cafe/api/search-jobs'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Origin': 'https://hiring.cafe',
        'Referer': 'https://hiring.cafe/'
    }

    payload = {
        'size': 1000,  # max per request
        'page': 0,
        'searchState': {
            'locations': [{'description': location}],
            'workplaceTypes': ['Remote', 'Hybrid', 'Onsite'],
            'commitmentTypes': ['Full Time'],
            'searchQuery': search_query,
            'dateFetchedPastNDays': days,
            'sortBy': 'default'
        }
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data.get('results', [])
```

**Data extraction patterns:**
```python
def extract_job_details(job):
    processed = job.get('v5_processed_job_data', {})
    company = job.get('v5_processed_company_data', {})
    job_info = processed.get('job_information', {})

    return {
        'title': processed.get('title', ''),
        'company': company.get('name', ''),
        'location': format_location(company.get('location', {})),
        'workplace_type': job_info.get('workplace_type', 'Unknown'),
        'salary_min': job_info.get('compensation', {}).get('min'),
        'salary_max': job_info.get('compensation', {}).get('max'),
        'currency': job_info.get('compensation', {}).get('currency', 'USD'),
        'description': processed.get('description', ''),
        'seniority': job_info.get('seniority_level', []),
        'commitment': job_info.get('commitment_type', 'Full Time')
    }
```

**Pagination (if needed):**
```python
all_jobs = []
page = 0

while True:
    payload['page'] = page
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    results = data.get('results', [])

    if not results:
        break

    all_jobs.extend(results)
    page += 1

    if len(results) < 1000:  # Last page
        break
```

### Rate Limiting Strategy

**Conservative approach:**
- Start with 10 requests/minute (600 jobs/min at 1000/request)
- Monitor for HTTP 429 (Too Many Requests) responses
- Exponential backoff on rate limit errors
- Reuse existing `pyrate-limiter` SQLite infrastructure

**Integration with existing sources:**
```python
# job_radar/sources/hiringcafe.py
RATE_LIMIT_CONFIG = {
    'bucket': 'hiringcafe',
    'max_rate': 10,
    'duration': Duration.MINUTE * 1
}
```

### Salary Extraction

**Already present in API response:**
```python
compensation = job_info.get('compensation', {})

if compensation:
    min_salary = compensation.get('min')
    max_salary = compensation.get('max')
    currency = compensation.get('currency', 'USD')

    if min_salary and max_salary:
        salary_range = f"${min_salary:,} - ${max_salary:,} {currency}"
    elif min_salary:
        salary_range = f"${min_salary:,}+ {currency}"
    else:
        salary_range = None
```

**No extraction complexity**—hiring.cafe already normalizes salary data in their API.

### Location Filtering

**Strategy 1: Server-side (recommended—reduces bandwidth):**
```python
payload['searchState']['locations'] = [
    {'description': 'San Francisco, CA, United States'},
    {'description': 'Remote'}
]
```

**Strategy 2: Client-side filtering:**
```python
def filter_by_location(jobs, allowed_locations):
    return [
        job for job in jobs
        if matches_location_criteria(
            job['v5_processed_company_data'].get('location', {}),
            allowed_locations
        )
    ]
```

**Recommendation:** Use server-side filtering via `searchState.locations` to reduce API payload size and respect rate limits.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| packaging.version | semver library | Never—semver doesn't handle PEP 440 (Python-specific versioning), and packaging is 3x faster |
| packaging.version | String splitting + int comparison | Never—breaks on 2.1.0rc1, 2.1.0.post1, 1!2.0.0 edge cases |
| urllib.request | requests library | Use requests if need retry logic, session cookies, or auth; overkill for simple GET |
| tqdm | Custom progress bar | Use custom only if avoiding dependencies; tqdm has 60ns overhead (negligible) |
| tkinter.messagebox | CTkMessagebox extension | Use CTkMessagebox if need advanced styling (icons, custom buttons); adds dependency |
| subprocess + platform | os.startfile() | Never—os.startfile() is Windows-only; subprocess works cross-platform |
| GitHub Releases API | Self-hosted update manifest | Use self-hosted if not using GitHub; adds infrastructure complexity |
| hiring.cafe POST API | Scraping HTML | Use scraping only if API breaks; fragile to DOM changes |
| pyrate-limiter SQLite | In-memory rate limiting | Use in-memory only for single-run CLI; loses state across restarts |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| PyUpdater | Archived/unmaintained since 2020; PyInstaller-specific; over-engineered for simple use case | stdlib urllib + subprocess + packaging.version |
| Esky | Python 2 only; incompatible with PyInstaller and modern Python; dead project | stdlib urllib + subprocess + packaging.version |
| tufup | Overkill for simple "download installer" workflow; designed for delta updates and complex security; adds complexity | stdlib urllib + subprocess (simple GET + open file) |
| os.startfile() | Windows-only; raises AttributeError on macOS/Linux | subprocess.Popen with platform detection |
| semver library | Doesn't handle PEP 440; slower than packaging.version; solves wrong problem (npm-style semver, not Python) | packaging.version (Python-native, faster, correct) |
| String version comparison | Breaks on "2.10.0" > "2.9.0" (lexicographic fails); no pre-release support | packaging.version |
| requests for installer download | Overkill when urllib.request + reporthook handles progress; extra dependency usage | urllib.request (stdlib, simpler) |
| BeautifulSoup for hiring.cafe | Unnecessary—API returns clean JSON; scraping is fragile fallback only | requests.post() with JSON payload |
| Custom rate limiter | Reinventing wheel; Job Radar already has pyrate-limiter + SQLite | pyrate-limiter (already in stack) |
| CTkMessagebox library | Adds dependency for marginal UX benefit; tkinter.messagebox is accessible and theme-agnostic | tkinter.messagebox (stdlib, zero deps) |

## Stack Patterns by Variant

**If user needs offline installer (no download):**
- Skip GitHub Releases API entirely
- Provide manual download link in settings
- Version check still runs, notification says "Download from website"

**If hiring.cafe API changes to HTML rendering:**
- Fallback to BeautifulSoup scraping (already in stack)
- Target job cards with CSS selectors
- Extract title, company, location, salary from DOM
- More fragile than API, but zero new dependencies

**If need silent updates (enterprise deployment):**
- DO NOT implement in v2.2.0 (security anti-pattern for unsigned binaries)
- Wait for code signing infrastructure (macOS Developer ID, Windows Authenticode)
- Even then, prefer user-initiated for transparency

**If rate limits too aggressive:**
- Add exponential backoff: 1s, 2s, 4s, 8s delays
- Reduce max_rate from 10/min to 5/min
- Cache hiring.cafe results (reuse existing cache.py infrastructure)
- Respect HTTP 429 Retry-After header

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| packaging 26.0 | Python >=3.8 | Job Radar requires Python >=3.10, so fully compatible |
| tqdm 4.67.3 | Python >=3.7 | Job Radar requires Python >=3.10, so fully compatible |
| requests (existing) | urllib.request | Can use either; urllib for simple GET, requests for API with JSON |
| pyrate-limiter (existing) | hiring.cafe API | Reuse existing SQLiteBucket('hiringcafe', 'rate_limits.db') |
| customtkinter (existing) | tkinter.messagebox | messagebox is stdlib; works alongside CustomTkinter |

**PyInstaller bundling notes:**
- packaging has no hidden imports (pure Python)
- tqdm has no hidden imports (pure Python)
- urllib is stdlib (auto-bundled)
- subprocess is stdlib (auto-bundled)
- platform is stdlib (auto-bundled)

**No PyInstaller spec changes needed.**

## Integration Checklist

**Auto-update:**
- [ ] Add `packaging>=26.0` to pyproject.toml dependencies
- [ ] Add `tqdm>=4.67.3` to optional gui dependencies (or skip if no progress bars)
- [ ] Create `job_radar/updater.py` module
- [ ] Implement `check_for_updates()` using requests + packaging.version
- [ ] Implement `download_installer()` using urllib.request + tqdm reporthook
- [ ] Implement `open_installer()` using subprocess + platform.system()
- [ ] Add background thread in GUI startup (reuse SearchWorker pattern)
- [ ] Add update notification dialog (tkinter.messagebox or CTkToplevel)
- [ ] Add user preference for "Check for updates" (default: enabled)
- [ ] Add timestamp caching (max once per day)
- [ ] Write tests for version comparison edge cases

**hiring.cafe:**
- [ ] Create `job_radar/sources/hiringcafe.py` module
- [ ] Implement `fetch_jobs()` using requests.post() with JSON payload
- [ ] Add rate limiting using existing pyrate-limiter SQLiteBucket
- [ ] Add headers to mimic browser (User-Agent, Referer, Origin)
- [ ] Implement pagination loop (max 1000 per page)
- [ ] Extract salary from compensation object (already normalized)
- [ ] Add location filtering via searchState.locations
- [ ] Add workplace type filtering (Remote/Hybrid/Onsite)
- [ ] Map to Job Radar internal job schema
- [ ] Add error handling for API changes (fallback to HTML scraping if needed)
- [ ] Write tests for JSON parsing and pagination

## Sources

### Auto-Update Research

**Framework comparisons:**
- [GitHub - cloudmatrix/esky](https://github.com/cloudmatrix/esky) — Dead project, Python 2 only
- [PyUpdater](http://www.pyupdater.org/) — Archived, no longer maintained
- [GitHub - dennisvang/tufup](https://github.com/dennisvang/tufup) — Modern alternative, but overkill for simple use case

**GitHub Releases API:**
- [GitHub REST API - Releases](https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28) — Official documentation (HIGH confidence)
- [github-release-downloader · PyPI](https://pypi.org/project/github-release-downloader/) — Example library (not needed, but validates approach)

**Version comparison:**
- [packaging · PyPI](https://pypi.org/project/packaging/) — Official PyPA library (HIGH confidence)
- [Versioning - Python Packaging User Guide](https://packaging.python.org/en/latest/discussions/versioning/) — Best practices (HIGH confidence)
- [PEP 440 – Version Identification](https://peps.python.org/pep-0440/) — Specification (HIGH confidence)

**File downloads:**
- [tqdm · PyPI](https://pypi.org/project/tqdm/) — Official documentation (HIGH confidence)
- [GitHub - tqdm/tqdm](https://github.com/tqdm/tqdm) — Source code and examples (HIGH confidence)
- [Python requests download file with tqdm progress bar](https://gist.github.com/yanqd0/c13ed29e29432e3cf3e7c38467f42f51) — Community pattern (MEDIUM confidence)

**Cross-platform file opening:**
- [Python: Use subprocess to open file with default program](https://gist.github.com/ytturi/0c23ad5ab89154d24c340c2b1cc3432b) — Community pattern (MEDIUM confidence)
- [Is There a Cross-Platform Equivalent to os.startfile()?](https://www.pythontutorials.net/blog/is-there-an-platform-independent-equivalent-of-os-startfile/) — Tutorial (MEDIUM confidence)

### hiring.cafe Research

**Reverse engineering:**
- [GitHub - umur957/hiring-cafe-job-scraper](https://github.com/umur957/hiring-cafe-job-scraper) — API endpoint discovery (HIGH confidence—verified source code)
- [GitHub - jinijinjaney/hiringcafe-job-scraper](https://github.com/jinijinjaney/hiringcafe-job-scraper) — Additional validation (HIGH confidence—verified source code)
- [Scaling HiringCafe from 0 to 1M+ users](https://blog.hiring.cafe/p/scaling-hiringcafe-from-0-to-1m-users) — Architecture context (MEDIUM confidence)

**Rate limiting:**
- Existing Job Radar codebase — pyrate-limiter + SQLiteBucket pattern (HIGH confidence—already validated in production)

### GUI Integration

**CustomTkinter dialogs:**
- [GitHub - Akascape/CTkMessagebox](https://github.com/Akascape/CTkMessagebox) — Extension library (MEDIUM confidence—optional dependency)
- [tkinter.messagebox — Python 3.14.3 documentation](https://docs.python.org/3/library/tkinter.messagebox.html) — Stdlib reference (HIGH confidence)

---

*Stack research for: Job Radar v2.2.0 Auto-Update & hiring.cafe Integration*
*Researched: 2026-02-15*
*Confidence: HIGH — All recommendations verified against official documentation or reverse-engineered source code*
