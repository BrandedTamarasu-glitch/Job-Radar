# Phase 35: Additional API Sources (SerpAPI, Jobicy) - Research

**Researched:** 2026-02-14
**Domain:** Job API integration, rate limiting, quota tracking UI
**Confidence:** HIGH

## Summary

This phase adds two new job API integrations following the established pattern from JSearch/USAJobs/Adzuna/Authentic Jobs implementations. SerpAPI provides access to Google Jobs results via their aggregator service, while Jobicy offers remote-focused job listings through a public API. Both APIs have clear documentation and well-defined response structures that map cleanly to the existing JobResult dataclass.

The main technical challenge is implementing real-time quota tracking display in the GUI Settings tab. The existing pyrate-limiter infrastructure tracks usage in SQLite but doesn't expose remaining counts directly. Research shows the best approach is to query the SQLite bucket tables directly to calculate usage against configured limits, with simple text display ("15/100 today") avoiding complex UI components.

**Primary recommendation:** Implement both APIs using the exact pattern from existing sources (api_config → rate_limits → sources.py fetcher → mapper function), add quota display by querying SQLite buckets directly, and include test buttons in GUI Settings tab for immediate validation.

## Standard Stack

The established libraries/tools for this domain are already in the codebase:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | latest | HTTP client for API calls | Universal Python HTTP library, used by all existing API fetchers |
| pyrate-limiter | latest | Rate limiting with SQLite persistence | Already integrated, provides persistent quota tracking across restarts |
| python-dotenv | latest | .env credential management | Already used for API key storage, proven pattern |
| beautifulsoup4 | latest | HTML description parsing | Needed for Jobicy HTML job descriptions |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlite3 | built-in | Query rate limit buckets for quota display | Direct SQL queries to .rate_limits/*.db for usage counts |
| customtkinter | latest | GUI quota display widgets | Already used for Settings tab, consistent UI |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pyrate-limiter SQLite queries | In-memory counter tracking | SQLite queries proven reliable, no reason to diverge from existing pattern |
| Simple text display | Progress bars for quota | Context decision: "simple count without progress bars" per CONTEXT.md |

**Installation:**
No new dependencies required - all libraries already in pyproject.toml.

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── api_config.py         # Add SERPAPI_API_KEY, JOBICY validation
├── rate_limits.py        # Add serpapi/jobicy rate configs to RATE_LIMITS dict
├── sources.py            # Add fetch_serpapi(), fetch_jobicy(), map_*_to_job_result()
├── api_setup.py          # Add SerpAPI/Jobicy sections to setup_apis() wizard
└── gui/
    └── main_window.py    # Add quota display labels, SerpAPI/Jobicy API sections
```

### Pattern 1: API Fetcher Implementation
**What:** Follow JSearch/USAJobs pattern for consistency
**When to use:** For both SerpAPI and Jobicy integrations
**Example:**
```python
# Source: Existing codebase pattern from sources.py:959-1016

def fetch_serpapi(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from SerpAPI Google Jobs API."""
    results = []

    # Check credentials
    api_key = get_api_key("SERPAPI_API_KEY", "SerpAPI")
    if not api_key:
        return results

    # Check rate limit
    if not check_rate_limit("serpapi", verbose=verbose):
        return results

    # Build API URL
    params = {
        "engine": "google_jobs",
        "q": query,
        "api_key": api_key,
    }
    if location:
        params["location"] = location

    url = "https://serpapi.com/search?" + urllib.parse.urlencode(params)

    # Fetch with retry
    try:
        body = fetch_with_retry(url, headers=HEADERS, use_cache=True)
        if body is None:
            log.debug("[SerpAPI] Fetch failed for '%s'", query)
            return results

        data = _json.loads(body)
        items = data.get("jobs_results", [])

        for item in items:
            job = map_serpapi_to_job_result(item)
            if job:
                results.append(job)

    except _json.JSONDecodeError as e:
        log.debug("[SerpAPI] JSON parse error: %s", e)
    except Exception as e:
        error_str = str(e).lower()
        if "401" in error_str or "403" in error_str or "unauthorized" in error_str:
            log.error("[SerpAPI] Authentication failed - run 'job-radar --setup-apis' to reconfigure")
        else:
            log.debug("[SerpAPI] Request failed: %s", e)

    log.info("[SerpAPI] Found %d results for '%s'", len(results), query)
    return results
```

### Pattern 2: Response Mapping with Validation
**What:** Map API response to JobResult with required field validation
**When to use:** For both map_serpapi_to_job_result() and map_jobicy_to_job_result()
**Example:**
```python
# Source: Existing codebase pattern from sources.py:744-812

def map_serpapi_to_job_result(item: dict) -> JobResult | None:
    """Map SerpAPI response item to JobResult.

    Validates required fields (title, company, url) and returns None if any are missing.
    """
    # Extract and validate required fields
    title = item.get("title", "").strip()
    company = item.get("company_name", "").strip()
    url = item.get("apply_options", [{}])[0].get("link", "").strip()

    if not title or not company or not url:
        log.debug("[SerpAPI] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                 bool(title), bool(company), bool(url))
        return None

    # Location normalization
    location_raw = item.get("location", "")
    location = parse_location_to_city_state(location_raw)

    # Detect work-from-home flag
    extensions = item.get("detected_extensions", {})
    arrangement = "remote" if extensions.get("work_from_home") else _parse_arrangement(f"{title} {item.get('description', '')}")

    # Description cleaning
    description_raw = item.get("description", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    # Employment type
    emp_type = extensions.get("schedule_type", "")

    # Salary (SerpAPI doesn't typically include salary)
    salary = "Not specified"

    # Date posted
    date_posted = extensions.get("posted_at", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="serpapi",
        employment_type=emp_type,
        parse_confidence="high",
    )
```

### Pattern 3: Rate Limiter Configuration
**What:** Add source to RATE_LIMITS dict with conservative defaults
**When to use:** For both SerpAPI and Jobicy in rate_limits.py
**Example:**
```python
# Source: Existing codebase pattern from rate_limits.py:42-105

def _load_rate_limits() -> dict:
    """Load rate limits from config file with fallback to defaults."""
    # Hardcoded defaults (conservative)
    defaults = {
        "adzuna": [Rate(100, Duration.MINUTE), Rate(1000, Duration.HOUR)],
        "authentic_jobs": [Rate(60, Duration.MINUTE)],
        "jsearch": [Rate(100, Duration.MINUTE)],
        "usajobs": [Rate(60, Duration.MINUTE)],
        "serpapi": [Rate(50, Duration.MINUTE)],  # Conservative for free tier
        "jobicy": [Rate(1, Duration.HOUR)],      # Per docs: "once per hour"
    }
    # ... merge with config overrides ...
```

### Pattern 4: Quota Display via SQLite Query
**What:** Query pyrate-limiter SQLite buckets directly to calculate usage
**When to use:** For real-time quota display in GUI Settings tab
**Example:**
```python
# Source: Research into pyrate-limiter internals + existing codebase pattern

def get_quota_usage(source: str) -> tuple[int, int, str] | None:
    """Get current quota usage for a source.

    Returns (used, limit, period) tuple or None if not available.
    """
    from .rate_limits import BACKEND_API_MAP, RATE_LIMITS, _connections

    backend_api = BACKEND_API_MAP.get(source, source)

    # Get rate configuration
    rates = RATE_LIMITS.get(backend_api)
    if not rates:
        return None

    # Get SQLite connection
    conn = _connections.get(backend_api)
    if not conn:
        return None

    # Query bucket table for current window usage
    # pyrate-limiter stores items with timestamps in rate_limits table
    # Count items within current rate period
    shortest_rate = min(rates, key=lambda r: r.interval)
    limit = shortest_rate.limit
    interval_seconds = shortest_rate.interval

    # Calculate current window start time
    now = time.time()
    window_start = now - interval_seconds

    try:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM rate_limits WHERE item_id = ? AND created_at >= ?",
            (source, window_start)
        )
        used = cursor.fetchone()[0]

        # Format period string
        if interval_seconds == 60:
            period = "minute"
        elif interval_seconds == 3600:
            period = "hour"
        elif interval_seconds == 86400:
            period = "day"
        else:
            period = f"{interval_seconds}s"

        return (used, limit, period)
    except Exception as e:
        log.debug(f"Could not get quota for {source}: {e}")
        return None
```

### Pattern 5: GUI Quota Display
**What:** Add simple text labels showing "X/Y period" next to API key fields
**When to use:** In _add_api_section() for SerpAPI, Jobicy, and existing APIs
**Example:**
```python
# Source: Context decision + existing GUI patterns from main_window.py

# Add quota display label after Test button
quota_label = ctk.CTkLabel(
    test_frame,
    text="",  # Will be updated dynamically
    font=ctk.CTkFont(size=10),
    text_color="gray"
)
quota_label.pack(side="left", padx=(10, 0))

# Store reference for dynamic updates
self._quota_labels[backend_api] = quota_label

# Update quota display function (called after each search)
def update_quota_display(self):
    """Update quota usage displays for all configured APIs."""
    for backend_api, label in self._quota_labels.items():
        quota_info = get_quota_usage(backend_api)
        if quota_info:
            used, limit, period = quota_info
            percentage = (used / limit) * 100

            # Color based on usage (yellow/orange at >80%)
            if percentage >= 80:
                label.configure(text_color="orange")
            else:
                label.configure(text_color="gray")

            label.configure(text=f"{used}/{limit} this {period}")
        else:
            label.configure(text="")
```

### Anti-Patterns to Avoid
- **Don't create separate rate limiter instances per source:** Sources sharing the same backend API (like JSearch) must share rate limiters to prevent quota violations
- **Don't skip required field validation:** Empty title/company/url cause scoring errors - validate and skip invalid jobs early
- **Don't forget to add sources to build_search_queries():** New sources won't be queried unless explicitly added to the query builder
- **Don't add to JSEARCH_KNOWN_SOURCES:** This set is for JSearch's job_publisher field only, not for new APIs

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rate limit quota tracking | Custom counter with timestamps | pyrate-limiter SQLite bucket queries | Already persistent, thread-safe, handles clock skew |
| API credential validation | Custom regex patterns | Inline test requests during setup | Validates actual API functionality, not just format |
| HTML description parsing | Manual tag stripping with regex | BeautifulSoup strip_html_and_normalize() | Handles malformed HTML, decodes entities correctly |
| Location normalization | Custom state mapping per API | Shared parse_location_to_city_state() | Consistent format across all sources, handles edge cases |

**Key insight:** The existing Job Radar codebase has battle-tested patterns for every part of this phase. The biggest risk is deviating from established patterns, not missing libraries.

## Common Pitfalls

### Pitfall 1: Quota Display Race Conditions
**What goes wrong:** SQLite queries for quota display can conflict with pyrate-limiter's background leak() threads
**Why it happens:** pyrate-limiter runs background threads that periodically clean old items from buckets
**How to avoid:** Use read-only queries with timeout, don't modify bucket tables directly
**Warning signs:** "Database is locked" errors, inconsistent quota counts

### Pitfall 2: SerpAPI Free Tier Limits
**What goes wrong:** SerpAPI free tier is 100 searches/month total (very limited)
**Why it happens:** Documentation emphasizes per-second limits but monthly cap is in fine print
**How to avoid:** Set conservative rate limit (50/min to stay well under monthly), warn users in setup wizard about monthly cap
**Warning signs:** Unexpected 429 errors mid-month, quota exhaustion notifications

### Pitfall 3: Jobicy HTML Description Handling
**What goes wrong:** Jobicy returns HTML in jobDescription field, not plain text
**Why it happens:** Their API preserves formatting from original posts
**How to avoid:** Use strip_html_and_normalize() utility (already handles this)
**Warning signs:** HTML tags appearing in search results, scoring errors on description field

### Pitfall 4: Source Name Consistency
**What goes wrong:** Mismatched source names between rate_limits.py, BACKEND_API_MAP, and fetch functions
**Why it happens:** Different naming conventions (serpapi vs SerpAPI vs serpapi_google_jobs)
**How to avoid:** Use lowercase identifier consistently everywhere ("serpapi", "jobicy"), display names in _SOURCE_DISPLAY_NAMES
**Warning signs:** Rate limiter creating multiple databases, quota display showing "unknown"

### Pitfall 5: Jobicy Geographic Filtering
**What goes wrong:** Jobicy's "geo" filter uses custom values, not standard city/state
**Why it happens:** Their API uses predefined region codes ("usa", "europe", "anywhere")
**How to avoid:** Map user's location input to Jobicy geo values, or skip geo filter and filter client-side
**Warning signs:** Empty results for valid location searches, errors on location parameter

## Code Examples

Verified patterns from official sources:

### SerpAPI Request Structure
```python
# Source: https://serpapi.com/google-jobs-api (official docs)

import requests
import json

params = {
    "engine": "google_jobs",
    "q": "software engineer",
    "location": "San Francisco, CA",
    "api_key": "your_api_key_here"
}

response = requests.get("https://serpapi.com/search", params=params)
data = response.json()

# Response structure:
# {
#   "search_metadata": {...},
#   "search_parameters": {...},
#   "jobs_results": [
#     {
#       "title": "Job Title",
#       "company_name": "Company",
#       "location": "City, State",
#       "via": "Job Board",
#       "description": "Full description...",
#       "detected_extensions": {
#         "posted_at": "2 days ago",
#         "schedule_type": "Full-time",
#         "work_from_home": true
#       },
#       "apply_options": [{"title": "Apply", "link": "https://..."}],
#       "job_id": "base64_encoded_id"
#     }
#   ]
# }
```

### Jobicy Request Structure
```python
# Source: https://github.com/Jobicy/remote-jobs-api (official docs)

import requests

params = {
    "count": 20,
    "geo": "usa",
    "industry": "marketing",
    "tag": "python"
}

response = requests.get("https://jobicy.com/api/v2/remote-jobs", params=params)
jobs = response.json()

# Response structure (array of jobs):
# [
#   {
#     "id": "12345",
#     "url": "https://jobicy.com/jobs/...",
#     "jobTitle": "Senior Python Developer",
#     "companyName": "Tech Corp",
#     "companyLogo": "https://...",
#     "jobIndustry": "Marketing",
#     "jobType": "full-time",
#     "jobGeo": "USA",
#     "jobLevel": "Senior",
#     "jobExcerpt": "Exciting opportunity...",
#     "jobDescription": "<p>Full HTML description...</p>",
#     "pubDate": "2026-02-13 10:30:00",
#     "annualSalaryMin": "120000",
#     "annualSalaryMax": "180000",
#     "salaryCurrency": "USD"
#   }
# ]
```

### SQLite Quota Query Pattern
```python
# Source: pyrate-limiter internals + research

import sqlite3
import time
from pathlib import Path

def get_current_usage(backend_api: str, interval_seconds: int) -> int:
    """Query pyrate-limiter SQLite bucket for current window usage."""
    db_path = Path.cwd() / ".rate_limits" / f"{backend_api}.db"

    if not db_path.exists():
        return 0

    conn = sqlite3.connect(str(db_path), timeout=1.0)
    now = time.time()
    window_start = now - interval_seconds

    try:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM rate_limits WHERE created_at >= ?",
            (window_start,)
        )
        count = cursor.fetchone()[0]
        return count
    finally:
        conn.close()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual quota tracking with counters | SQLite-backed pyrate-limiter | Phase 31 | Persistent, survives restarts, handles clock skew |
| API keys in config.json | .env file with python-dotenv | v1.x → v2.0 | Standard practice, keeps secrets out of version control |
| Hardcoded rate limits | Config-overridable with defaults | Phase 31 | Users can customize limits without code changes |
| "JSearch" source attribution | Original publisher (LinkedIn/Indeed/Glassdoor) | Phase 32 | Accurate source labels in results |
| Simple progress bar | Per-source job count display | Phase 32 | Users see which sources are productive |

**Deprecated/outdated:**
- Global rate limiters shared across all sources: Replaced with per-backend-API limiters to prevent cross-contamination
- In-memory rate tracking: Replaced with SQLite persistence for reliability across restarts

## Open Questions

1. **SerpAPI Free Tier Monthly Cap**
   - What we know: 100 searches/month free tier documented
   - What's unclear: Whether cached searches count against quota (docs say "identical queries within 1 hour are free")
   - Recommendation: Assume cached searches don't count, but set conservative 50/min limit to stay well under monthly cap. Add warning in setup wizard about monthly limit.

2. **Jobicy Rate Limit Enforcement**
   - What we know: Docs say "once per hour", may restrict excessive access
   - What's unclear: Whether restriction is hard block (429) or soft throttle, how it's tracked (IP? No auth)
   - Recommendation: Implement 1 req/hour limit defensively, add retry with exponential backoff for 429 responses

3. **Quota Display Update Timing**
   - What we know: Context says "real-time after each search"
   - What's unclear: Whether to update during search (per source) or only at completion
   - Recommendation: Update after each source completes (in source_complete callback) for immediate feedback without UI flicker

4. **SerpAPI vs Jobicy Search Order**
   - What we know: Context says "SerpAPI and Jobicy come after other APIs"
   - What's unclear: Whether they go in aggregator phase (like JSearch) or API phase
   - Recommendation: Place in aggregator phase (phase 3) since SerpAPI aggregates Google Jobs results. Jobicy is a native source but limited quota justifies running last.

## Sources

### Primary (HIGH confidence)
- [SerpAPI Google Jobs API Documentation](https://serpapi.com/google-jobs-api) - API endpoint, parameters, response structure
- [Jobicy Remote Jobs API GitHub](https://github.com/Jobicy/remote-jobs-api) - API endpoint, rate limits, response structure
- pyrate-limiter codebase (/Users/coryebert/Job-Radar/job_radar/rate_limits.py) - SQLite bucket implementation
- Job Radar sources.py (/Users/coryebert/Job-Radar/job_radar/sources.py) - Existing API patterns

### Secondary (MEDIUM confidence)
- [pyrate-limiter PyPI Documentation](https://pypi.org/project/pyrate-limiter/) - Rate definition and bucket tracking
- [API Rate Limiting Best Practices](https://medium.com/neural-engineer/implementing-effective-api-rate-limiting-in-python-6147fdd7d516) - Quota management patterns
- [API Quota Display Patterns](https://developers.google.com/display-video/api/guides/best-practices/quota) - UI best practices for quota visibility

### Tertiary (LOW confidence)
- None - all findings verified with official documentation or existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use, no new dependencies
- Architecture: HIGH - Existing patterns proven in 4 API sources (JSearch, USAJobs, Adzuna, Authentic Jobs)
- Pitfalls: MEDIUM - SerpAPI monthly cap and Jobicy HTML handling based on documentation, not field testing

**Research date:** 2026-02-14
**Valid until:** 30 days (APIs and libraries are stable, rate limits may change)
