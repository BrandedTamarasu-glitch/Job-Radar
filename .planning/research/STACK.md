# Stack Research

**Domain:** Job aggregation desktop application - v2.1.0 source expansion
**Researched:** 2026-02-13
**Confidence:** HIGH

## Recommended Stack Additions

### Job Aggregator APIs

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `serpapi` | 0.1.5+ | Google Jobs access via SerpAPI | Official Python SDK for SerpAPI with dedicated Google Jobs engine support. Returns structured JSON with 40+ data points per job. Integrates with existing `requests` + `python-dotenv` pattern for API keys. |
| `requests` (existing) | Current | JSearch API integration | RapidAPI-hosted JSearch requires standard HTTP headers (`X-RapidAPI-Key`, `X-RapidAPI-Host`). No dedicated SDK needed - existing `requests` library handles this with custom headers. |

**Implementation notes:**
- **SerpAPI**: Use `client.search({'engine': 'google_jobs', 'q': query})` pattern. Fits existing API abstraction in `job_radar/sources.py`.
- **JSearch**: Direct `requests.get()` with RapidAPI headers. Available on RapidAPI with generous free tier for testing.

### Free Job Board APIs

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `requests` (existing) | Current | All three job boards | USAJobs, Jobicy, and ZipRecruiter are HTTP REST APIs. Existing `requests` + `BeautifulSoup4` stack covers all needs. |
| Standard library `urllib.parse` | Built-in | Query parameter encoding | For USAJobs search filters and Jobicy tag parameters. |

**API-specific requirements:**
- **USAJobs**: Requires `Authorization-Key` header + email in `User-Agent`. Free API key from developer.usajobs.gov. Rate limits documented but not strict for reasonable use.
- **Jobicy**: Public RSS/JSON API at `jobicy.com/api/v2/remote-jobs`. No auth required. Limit checks to 1/hour to avoid access restrictions. Supports `count`, `geo`, `industry`, `tag` query params.
- **ZipRecruiter**: No official public API confirmed. Third-party scraping services exist (ScrapingBee, Apify) but require paid subscriptions. **Recommendation: Defer ZipRecruiter or use manual URL source pattern like Indeed/LinkedIn.**

### User-Configurable Scoring

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Standard library `json` | Built-in | Config schema extension | Existing `config.py` uses `json.load()`. Extend schema with `scoring_weights` key for 6-component weights. No new dependencies. |
| Existing profile schema | v4+ | Store user preferences | Add `scoring_weights: {skill_match: 0.25, ...}` to profile JSON. Falls back to hardcoded defaults in `scoring.py` if not present. |

**Implementation notes:**
- Scoring weights currently hardcoded in `scoring.py:47-54` (0.25, 0.15, 0.15, 0.15, 0.10, 0.20).
- Extend profile schema with optional `scoring_weights` object.
- Update `score_job()` to accept weights parameter with defaults.
- GUI: Add scoring preferences panel in profile editor using existing CustomTkinter widgets.

### GUI Uninstall Functionality

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Standard library `subprocess` | Built-in | Platform-native uninstall | Cross-platform solution. Calls platform-specific tools without new dependencies. |
| Standard library `platform` | Built-in | OS detection | Determines which uninstall method to use (Windows/macOS/Linux). |
| Standard library `shutil` | Built-in | Directory removal | For cleaning user data directories after uninstall. |

**Platform-specific approaches:**
- **Windows**: `subprocess.run(['powershell', 'Get-AppxPackage', ...])` for Windows Store apps, or registry-based uninstaller lookup for traditional apps. Self-contained apps: delete program directory.
- **macOS**: Self-contained .app bundles - delete `/Applications/JobRadar.app` + user data in `~/Library/Application Support/JobRadar`.
- **Linux**: PyInstaller onedir - delete installation directory + `~/.local/share/job-radar` data directory.

**Critical consideration**: GUI uninstall button removes the app that runs it. Must launch external cleanup script that waits for app exit before deletion. Use `subprocess.Popen()` to spawn detached cleanup process.

### Platform-Native Packaging

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `dmgbuild` | 1.6.7+ | macOS DMG creation | Official, actively maintained (Jan 2026 release). Requires Python 3.10+. Creates professional disk images without deprecated APIs. macOS-only (wrapper around macOS tools). |
| `pynsist` | 2.8+ | Windows NSIS installer | Creates NSIS installers that bundle Python runtime. Python 3.5+ support confirmed. Better alternative to manual PyInstaller + NSIS combination. |

**Why NOT cx_Freeze for MSI:**
- cx_Freeze supports MSI generation, but project already uses PyInstaller successfully.
- PyInstaller + pynsist workflow is simpler: PyInstaller builds executable, pynsist wraps in NSIS installer.
- cx_Freeze would require rewriting build process and re-testing packaging on all platforms.
- Startup time differences (1.8s vs 2.1s) are negligible for desktop app with GUI launch.

**Existing PyInstaller integration:**
- Already configured: `job-radar.spec`, CustomTkinter asset bundling, macOS .app bundle creation.
- Keep PyInstaller as build step; add installer packaging as post-build step.

## Installation

```bash
# Job aggregator APIs
pip install serpapi>=0.1.5

# Platform-native packaging (dev dependencies)
pip install dmgbuild>=1.6.7  # macOS only
pip install pynsist>=2.8     # Windows installer creation

# Note: No new runtime dependencies for job boards, scoring config, or uninstall.
# All use existing requests + standard library.
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `serpapi` for Google Jobs | Direct scraping of Google Jobs HTML | Never - violates Google ToS and fragile to DOM changes. API is reliable and legal. |
| `requests` for JSearch | RapidAPI SDK (if exists) | If RapidAPI releases official Python SDK, migrate for convenience. Currently `requests` is adequate. |
| `requests` for USAJobs | `usajobs` PyPI package (v0.1.0) | Exists but last updated years ago, limited functionality. Direct API calls more maintainable. |
| Profile JSON for scoring config | Separate config file | If scoring preferences needed independently of profiles. Current approach keeps profile self-contained. |
| `pynsist` for Windows | Manual PyInstaller + NSIS | If custom installer branding/logic needed beyond pynsist capabilities. pynsist handles 95% of use cases. |
| `dmgbuild` for macOS | `create-dmg` shell script | If Python dependency is problematic for build environment. `create-dmg` requires only macOS, no Python. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `cx_Freeze` | Requires rewriting entire build pipeline. PyInstaller already validated with 452 tests. Marginal startup time improvements don't justify migration risk. | Keep `PyInstaller` + add `pynsist`/`dmgbuild` post-build |
| ZipRecruiter official API | No confirmed public API. Third-party scrapers require paid subscriptions ($50+/mo). Cost-benefit doesn't justify for single source. | Manual URL source (existing pattern) or defer to future milestone |
| Custom uninstall registry manipulation | Brittle, Windows-only, risk of registry corruption. Modern Windows uses PowerShell cmdlets for clean uninstall. | `subprocess` + platform-specific standard tools |
| Embedding scoring weights in GUI config.json | Violates single-source-of-truth principle. Scoring is profile-specific, not app-wide. Different profiles may have different priorities. | Profile JSON schema extension |
| RapidAPI SDK/wrapper libraries | Adds dependency for minimal benefit. RapidAPI uses standard HTTP headers that `requests` handles natively. SDK would abstract away header control. | Direct `requests.get()` with custom headers |

## Stack Patterns by Variant

**If using paid API tiers (SerpAPI/JSearch beyond free limits):**
- Add `pyrate-limiter` configs for each API's rate limits (already in dependencies)
- Store API keys in `python-dotenv` .env file (existing pattern from `api_config.py`)
- Implement cost tracking for paid queries (log to JSON, warn at threshold)

**If targeting enterprise deployment:**
- Add Windows MSI via WiX Toolset (not pynsist) for Group Policy installation
- macOS: Use `productbuild` for signed .pkg installers instead of DMG
- Because: Enterprise IT requires signed installers with silent install flags

**If offline packaging required:**
- Use `pip download` to vendor all dependencies in repo
- Modify `pynsist` config to use local wheels instead of PyPI
- Because: Air-gapped networks cannot access PyPI during installation

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `serpapi@0.1.5` | Python 3.7+ | Tested with existing `requests` library, no conflicts |
| `dmgbuild@1.6.7` | Python 3.10-3.15 | Matches project's `requires-python = ">=3.10"` |
| `pynsist@2.8` | Python 3.5+ | Supports Python 3.10 (project minimum) but note Python 3.10 EOL is Oct 2026 |
| `PyInstaller@6.18.0` | Python 3.8-3.14 | Current project uses PyInstaller with Python 3.10+ |

**Critical compatibility note**: Python 3.10 reaches end-of-life October 2026. Project should plan migration to Python 3.11+ by Q4 2026 before security patch support ends.

## Integration Points

### Existing Architecture Alignment

**API Sources Pattern** (`job_radar/sources.py`):
```python
# Current: Dice, HN Hiring, RemoteOK, etc.
# Add: SerpAPI Google Jobs, JSearch, USAJobs, Jobicy
# Each returns List[JobResult] - no interface changes needed
```

**Rate Limiting** (`job_radar/rate_limits.py`):
```python
# Already uses pyrate-limiter
# Add limits for new APIs:
# - SerpAPI: 50 requests/month (free tier)
# - JSearch: Check RapidAPI plan limits
# - USAJobs: Documented in developer portal
# - Jobicy: Max 1 request/hour (recommended)
```

**API Key Management** (`job_radar/api_config.py`, `job_radar/api_setup.py`):
```python
# Existing: Supports optional API sources with setup wizard
# Add: SERPAPI_KEY, RAPIDAPI_KEY, USAJOBS_API_KEY, USAJOBS_EMAIL
# .env pattern already established
```

**Scoring Engine** (`job_radar/scoring.py`):
```python
# Current: Hardcoded weights at line 47-54
# Change: Accept optional weights dict parameter
# Fallback: Default weights if profile.scoring_weights not present
# Maintains backward compatibility with existing profiles
```

**Profile Schema** (`job_radar/profile_manager.py`):
```python
# Current: v4 schema with dealbreakers, preferences, skills
# Add: Optional scoring_weights object
# Example: {"scoring_weights": {"skill_match": 0.30, "response": 0.15, ...}}
# Validator: Sum of weights must equal 1.0
```

**GUI Architecture** (`job_radar/gui/main_window.py`):
```python
# Add: Uninstall button in Settings/Help menu
# Behavior: Calls platform-specific cleanup script
# macOS: Instruct user to drag .app to Trash + confirm data deletion
# Windows: Launch PowerShell uninstaller or delete program dir
# Linux: Remove install dir + data dir with sudo prompt
```

**Packaging Workflow** (`.github/workflows/release.yml`):
```yaml
# Current: PyInstaller → tar.gz/zip archives
# macOS addition: PyInstaller → dmgbuild → .dmg file
# Windows addition: PyInstaller → pynsist → .exe installer
# Linux: Keep tar.gz (standard for Linux distribution)
```

## Sources

### Job Aggregator APIs
- [SerpAPI Python SDK - PyPI](https://pypi.org/project/serpapi/) — Official package, version info, Google Jobs engine docs
- [JSearch API on RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) — API capabilities, free tier availability
- [RapidAPI Python Integration](https://docs.rapidapi.com/docs/additional-request-headers) — Header requirements for requests library

### Free Job Boards
- [USAJobs Developer Portal](https://developer.usajobs.gov/) — Official API docs, authentication requirements
- [Jobicy Remote Jobs API](https://github.com/Jobicy/remote-jobs-api) — Public API documentation, usage guidelines
- [ZipRecruiter APIs on RapidAPI](https://rapidapi.com/collection/ziprecruiter-api) — Third-party options (no confirmed official API)

### Platform-Native Packaging
- [dmgbuild PyPI](https://pypi.org/project/dmgbuild/) — Version 1.6.7, Python 3.10+ requirement, macOS-only
- [pynsist PyPI and docs](https://pynsist.readthedocs.io/) — Version 2.8, Python 3.5+ support
- [PyInstaller vs cx_Freeze 2026 comparison](https://ahmedsyntax.com/2026-comparison-pyinstaller-vs-cx-freeze-vs-nui/) — Performance benchmarks, feature comparison
- [cx_Freeze MSI creation guide](https://www.alexandrumarin.com/create-a-python-executable-and-msi-installer-using-cx_freeze/) — Alternative approach (not recommended for this project)

### Uninstall Functionality
- [Python cross-platform uninstall guide](https://thelinuxcode.com/how-to-uninstall-software-using-python-windows-macos-linux/) — Subprocess patterns, platform detection

### Package Versions
- [Python 3.10 EOL schedule](https://devguide.python.org/versions/) — October 2026 end-of-life
- [PyInstaller 6.18.0](https://pypi.org/project/pyinstaller/) — Released January 2026, Python 3.8-3.14 support

---
*Stack research for: Job Radar v2.1.0 source expansion*
*Researched: 2026-02-13*
*Confidence: HIGH for packaging tools (official docs verified), MEDIUM for JSearch/ZipRecruiter (WebSearch only), HIGH for USAJobs/Jobicy (official docs verified)*
