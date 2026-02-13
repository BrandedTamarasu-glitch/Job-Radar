# Phase 32: Job Aggregator APIs (JSearch, USAJobs) - Research

**Researched:** 2026-02-13
**Domain:** External API Integration (RapidAPI, Federal Government APIs)
**Confidence:** MEDIUM-HIGH

## Summary

Phase 32 integrates two job aggregator APIs: JSearch (Google Jobs via RapidAPI) and USAJobs (federal government). JSearch aggregates LinkedIn, Indeed, Glassdoor, and company career pages, while USAJobs provides federal job listings with specialized filters (GS grade, security clearance, agencies). The phase extends existing API infrastructure (--setup-apis wizard, .env credential management, rate limiting) and deduplication engine (rapidfuzz fuzzy matching at 85% threshold).

Key technical challenges: (1) JSearch returns results with `job_publisher` field (e.g., "LinkedIn") that must be split into individual sources for progress display while sharing rate limits; (2) USAJobs requires three custom headers (`Host`, `User-Agent`, `Authorization-Key`) instead of standard API key authentication; (3) Source attribution must display original board names (not "JSearch") while deduplication prioritizes native sources over aggregator copies.

**Primary recommendation:** Build JSearch and USAJobs as standard API sources (like Adzuna/Authentic Jobs) with special handling for JSearch source splitting and USAJobs header format. Extend existing patterns for API key setup, validation, rate limiting, and deduplication.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Source Attribution Display:**
- Show original board name, not aggregator name — JSearch results appear as "LinkedIn", "Indeed", "Glassdoor" (individual sources, like native integrations)
- USAJobs results display as "USAJobs (Federal)"
- GUI per-source progress shows individual lines: "LinkedIn: 5 jobs", "Indeed: 7 jobs", "Glassdoor: 3 jobs" (even though JSearch is one API call, split results by origin for progress display)

**API Key Setup Flow:**
- Extend existing --setup-apis wizard to include JSearch and USAJobs alongside Adzuna/Authentic Jobs
- Validate API keys during setup by making a test API call — instant feedback that key works before saving
- Add API key configuration fields to the GUI (Settings section) so non-technical users never need the terminal
- When API keys aren't configured, show a suggestion: "Tip: Set up JSearch API key to search LinkedIn, Indeed, and Glassdoor" — always show, not just first run

**Dedup Behavior:**
- Use existing rapidfuzz fuzzy matching (85% similarity) — same dedup engine that works across Dice/HN/RemoteOK/WWR
- When duplicate found, original source wins over aggregator copy (Dice listing kept over JSearch copy of same job)
- Show multi-source badge on merged listings: "Found on 3 sources" — signals the job is widely posted
- Show dedup stats in both CLI progress output AND report summary (e.g., "12 duplicates removed across 4 sources")

**Search Query Mapping:**
- JSearch: Use first 4 profile titles (same pattern as Dice), each as separate query
- JSearch location: Match user's profile location_preference — remote if they prefer remote, city if they specified a city
- USAJobs: Search by titles + location (same pattern as other sources)
- USAJobs optional federal fields: Add GS grade range (min/max), preferred agencies list, and security clearance level (None/Secret/Top Secret) as optional profile fields
- Federal fields are optional — blank means no filtering on those parameters

### Claude's Discretion

- Exact JSearch API query parameter mapping (search_terms, location, date_posted, etc.)
- USAJobs API authentication header format
- How to split JSearch results into individual source buckets for progress display
- Error handling for API failures (timeout, 429, invalid key)
- Where federal profile fields appear in GUI form and CLI wizard

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core Dependencies (Already in Project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | latest | HTTP client for API calls | Standard Python HTTP library, used for all existing API sources (Adzuna, Authentic Jobs) |
| python-dotenv | latest | .env file loading for API keys | Already used for API credential management, secure and simple |
| pyrate-limiter | latest | Rate limiting with SQLite persistence | Already implemented in Phase 31, supports per-backend limiters |
| rapidfuzz | latest | Fuzzy string matching for deduplication | Already used for cross-source dedup at 85% threshold |
| questionary | latest | Interactive CLI prompts | Already used in --setup-apis wizard for Adzuna/Authentic Jobs |
| customtkinter | latest | GUI framework | Already used for profile form, search controls |

### No New Dependencies Required

All required functionality is covered by existing dependencies. JSearch and USAJobs integration follows the same patterns as Adzuna and Authentic Jobs.

**Installation:**
No changes needed — all dependencies already in pyproject.toml

## Architecture Patterns

### Pattern 1: API Source Implementation

**What:** Standard fetch function structure for external APIs

**When to use:** All API-based sources (Adzuna, Authentic Jobs, JSearch, USAJobs)

**Example from Adzuna (sources.py:684-736):**
```python
def fetch_adzuna(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from Adzuna API."""
    results = []

    # Check credentials
    app_id = get_api_key("ADZUNA_APP_ID", "Adzuna")
    app_key = get_api_key("ADZUNA_APP_KEY", "Adzuna")
    if not app_id or not app_key:
        return results

    # Check rate limit
    if not check_rate_limit("adzuna", verbose=verbose):
        return results

    # Build API URL with query params
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": "50",
    }
    if location:
        params["where"] = location

    url = "https://api.adzuna.com/v1/api/jobs/us/search/1?" + urllib.parse.urlencode(params)

    # Fetch with retry
    try:
        body = fetch_with_retry(url, headers=HEADERS, use_cache=True)
        if body is None:
            log.debug("[Adzuna] Fetch failed for '%s'", query)
            return results

        data = _json.loads(body)
        items = data.get("results", [])

        for item in items:
            job = map_adzuna_to_job_result(item)
            if job:
                results.append(job)

    except _json.JSONDecodeError as e:
        log.debug("[Adzuna] JSON parse error: %s", e)
    except Exception as e:
        # Check for auth errors
        error_str = str(e).lower()
        if "401" in error_str or "403" in error_str:
            log.error("[Adzuna] Authentication failed - run 'job-radar --setup-apis' to reconfigure")
        else:
            log.debug("[Adzuna] Request failed: %s", e)

    log.info("[Adzuna] Found %d results for '%s'", len(results), query)
    return results
```

**Apply to JSearch:**
- Use RapidAPI headers: `X-RapidAPI-Key`, `X-RapidAPI-Host`
- API endpoint: `https://jsearch.p.rapidapi.com/search`
- Parameters: `query` (search terms), `page`, `num_pages`, `date_posted`, etc.
- Parse `job_publisher` field to determine original source (LinkedIn, Indeed, Glassdoor)

**Apply to USAJobs:**
- Custom headers: `Host: data.usajobs.gov`, `User-Agent: {email}`, `Authorization-Key: {api_key}`
- API endpoint: `https://data.usajobs.gov/api/search`
- Parameters: `Keyword`, `PositionTitle`, `LocationName`, `PayGradeLow`, `PayGradeHigh`, `Organization`
- Response structure: `data.SearchResult.SearchResultItems`

### Pattern 2: API Response Mapping

**What:** Defensive mapping from API JSON to JobResult dataclass

**When to use:** Converting external API responses to internal JobResult format

**Example from Adzuna (sources.py:739-807):**
```python
def map_adzuna_to_job_result(item: dict) -> JobResult | None:
    """Map Adzuna API response item to JobResult.

    Validates required fields (title, company, url) and returns None if any are missing.
    """
    # Extract and validate required fields
    title = item.get("title", "").strip()
    company = item.get("company", {}).get("display_name", "").strip()
    url = item.get("redirect_url", "").strip()

    if not title or not company or not url:
        log.debug("[Adzuna] Skipping job with missing required fields")
        return None

    # Location normalization
    location_raw = item.get("location", {}).get("display_name", "")
    location = parse_location_to_city_state(location_raw)

    # Salary fields
    salary_min = item.get("salary_min")
    salary_max = item.get("salary_max")
    salary_currency = "USD"

    # Format salary string
    if salary_min and salary_max:
        salary = f"${salary_min:,.0f} - ${salary_max:,.0f}"
    elif salary_min:
        salary = f"${salary_min:,.0f}+"
    else:
        salary = "Not specified"

    # Description cleaning
    description_raw = item.get("description", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    # Arrangement detection
    arrangement = _parse_arrangement(f"{title} {description}")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=item.get("created", ""),
        description=description,
        url=url,
        source="adzuna",
        employment_type="",
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
    )
```

**Apply to JSearch:**
- Required fields: `job_title`, `employer_name`, `job_apply_link`
- Source attribution: Use `job_publisher` field (e.g., "LinkedIn") NOT "JSearch"
- Salary: `job_min_salary`, `job_max_salary` fields
- Location: `job_city`, `job_state`, `job_country` OR `job_is_remote`
- Date: `job_posted_at_datetime_utc`

**Apply to USAJobs:**
- Required fields: `MatchedObjectDescriptor.PositionTitle`, `MatchedObjectDescriptor.OrganizationName`, `MatchedObjectDescriptor.PositionURI`
- Source: Always "USAJobs (Federal)"
- Location: `PositionLocationDisplay` OR first item in `PositionLocation` array
- Salary: `PositionRemuneration` array (min/max salary)
- Date: `PublicationStartDate`

### Pattern 3: Rate Limit Configuration with Backend API Mapping

**What:** Share rate limiters across sources using the same backend API

**When to use:** Multiple display sources (LinkedIn, Indeed, Glassdoor) call same API (JSearch)

**Example from rate_limits.py (Phase 31):**
```python
# Map sources to backend APIs - sources sharing the same backend API share rate limiters
BACKEND_API_MAP = {
    "adzuna": "adzuna",
    "authentic_jobs": "authentic_jobs",
    # Future sources will map multiple sources to same backend:
    # "linkedin": "jsearch",
    # "indeed": "jsearch",
    # "glassdoor": "jsearch",
}

def get_rate_limiter(source: str) -> Limiter:
    """Get or create a rate limiter for the given source.

    Sources sharing the same backend API (via BACKEND_API_MAP) will share
    the same rate limiter instance to prevent hitting API limits faster
    when multiple sources use the same backend.
    """
    # Look up backend API (fallback to source name if not mapped)
    backend_api = BACKEND_API_MAP.get(source, source)

    # Check if limiter already exists for this backend API
    if backend_api in _limiters:
        return _limiters[backend_api]

    # Create limiter using backend API name
    rates = RATE_LIMITS.get(backend_api, [Rate(60, Duration.MINUTE)])
    # ... create and cache limiter using backend_api as key
```

**Apply to JSearch:**
- Add to `BACKEND_API_MAP`: `{"linkedin": "jsearch", "indeed": "jsearch", "glassdoor": "jsearch"}`
- Add to `RATE_LIMITS` in config: `{"jsearch": [{"limit": 100, "interval": 60}]}`
- All three sources share same rate limiter instance (prevents hitting JSearch API faster)
- Rate limit check uses source name ("linkedin") but limiter lookup uses backend API ("jsearch")

### Pattern 4: API Key Setup Wizard Extension

**What:** Interactive prompt sequence for collecting API credentials

**When to use:** Adding new API sources to --setup-apis command

**Example from api_setup.py:54-86 (Adzuna section):**
```python
# Section 1 - Adzuna
print("=" * 60)
print("Adzuna API")
print("=" * 60)
print("Sign up at: https://developer.adzuna.com/\n")

try:
    adzuna_app_id = questionary.text(
        "ADZUNA_APP_ID (press Enter to skip):",
        style=custom_style
    ).ask()

    if adzuna_app_id is None:  # Ctrl+C
        print("\nSetup cancelled.")
        return

    if adzuna_app_id.strip():
        adzuna_app_key = questionary.text(
            "ADZUNA_APP_KEY:",
            style=custom_style
        ).ask()

        if adzuna_app_key is None:  # Ctrl+C
            print("\nSetup cancelled.")
            return

        if adzuna_app_key.strip():
            credentials["ADZUNA_APP_ID"] = adzuna_app_id.strip()
            credentials["ADZUNA_APP_KEY"] = adzuna_app_key.strip()

except KeyboardInterrupt:
    print("\nSetup cancelled.")
    return
```

**Apply to JSearch:**
- Add section after Authentic Jobs
- Prompt for `JSEARCH_API_KEY` (single key from RapidAPI)
- Sign up URL: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
- Store in .env as `JSEARCH_API_KEY=xxx`

**Apply to USAJobs:**
- Add section after JSearch
- Prompt for `USAJOBS_API_KEY` and `USAJOBS_EMAIL` (both required)
- Sign up URL: https://developer.usajobs.gov/apirequest/
- Store in .env as `USAJOBS_API_KEY=xxx` and `USAJOBS_EMAIL=user@example.com`

### Pattern 5: API Key Validation with Test Requests

**What:** Make minimal API request during setup to verify credentials work

**When to use:** --setup-apis wizard and --test-apis command

**Example from api_setup.py:223-254 (Adzuna test):**
```python
# Test Adzuna
print("Adzuna API:")
adzuna_app_id = os.getenv("ADZUNA_APP_ID")
adzuna_app_key = os.getenv("ADZUNA_APP_KEY")

if not adzuna_app_id or not adzuna_app_key:
    print("  ✗ Not configured (skipped)\n")
    results["adzuna"] = "skipped"
else:
    try:
        url = (
            f"https://api.adzuna.com/v1/api/jobs/us/search/1"
            f"?app_id={adzuna_app_id}&app_key={adzuna_app_key}&results_per_page=1"
        )
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            print("  ✓ Pass\n")
            results["adzuna"] = "pass"
        elif response.status_code in (401, 403):
            print("  ✗ Fail: Invalid credentials\n")
            results["adzuna"] = "fail"
        else:
            print(f"  ✗ Error: HTTP {response.status_code}\n")
            results["adzuna"] = "error"

    except requests.Timeout:
        print("  ✗ Error: Request timeout\n")
        results["adzuna"] = "error"
    except requests.RequestException as e:
        print(f"  ✗ Error: Network error ({e})\n")
        results["adzuna"] = "error"
```

**Apply to JSearch:**
- Test endpoint: `https://jsearch.p.rapidapi.com/search?query=test&num_pages=1`
- Headers: `X-RapidAPI-Key: {key}`, `X-RapidAPI-Host: jsearch.p.rapidapi.com`
- Success: 200 status + valid JSON response
- Auth failure: 401/403 status

**Apply to USAJobs:**
- Test endpoint: `https://data.usajobs.gov/api/search?Keyword=test&ResultsPerPage=1`
- Headers: `Host: data.usajobs.gov`, `User-Agent: {email}`, `Authorization-Key: {key}`
- Success: 200 status + valid JSON response
- Auth failure: 401/403 status

### Anti-Patterns to Avoid

**Don't hardcode source names in deduplication:**
- ❌ `if job.source == "JSearch": skip_dedup()`
- ✅ Use `job_publisher` field to set source name before deduplication runs

**Don't create separate rate limiters per display source:**
- ❌ `get_rate_limiter("linkedin")`, `get_rate_limiter("indeed")` → 3 limiters for same API
- ✅ Use `BACKEND_API_MAP` to share limiter: `"linkedin": "jsearch"` → 1 limiter

**Don't validate API keys on every request:**
- ❌ Check key format/length in fetch function
- ✅ Validate once during setup with test request, trust thereafter

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| String similarity comparison | Custom Levenshtein/edit distance | rapidfuzz (already used) | Optimized C++ implementation, handles edge cases (empty strings, unicode), provides multiple algorithms (token_sort_ratio for word order variance) |
| Rate limiting with persistence | In-memory counters + manual SQLite writes | pyrate-limiter (already used) | Background leak thread, multiple rate windows (60/min AND 1000/hour), atomic SQLite operations, cleanup on exit |
| HTTP retries with exponential backoff | Manual retry loops | fetch_with_retry helper (already exists) | Handles 429, 503, network errors; configurable retries; caching support |
| API key validation | Regex checks on key format | Test API request during setup | Only the API knows valid format; test request catches typos, expired keys, wrong permissions |
| Source attribution tracking | Manual dict/set of seen sources | Extend JobResult with multi-source support | Structured data model, type-safe, supports future features (show all sources job appeared on) |

**Key insight:** Phase 31 and existing API sources (Adzuna, Authentic Jobs) already solved these problems. JSearch and USAJobs should follow established patterns rather than inventing new approaches.

## Common Pitfalls

### Pitfall 1: RapidAPI Header Case Sensitivity

**What goes wrong:** API returns 401 even with valid key because headers use wrong case (`x-rapidapi-key` instead of `X-RapidAPI-Key`)

**Why it happens:** HTTP headers are case-insensitive per spec, but RapidAPI proxy enforces exact case for security headers

**How to avoid:** Use exact casing from RapidAPI documentation: `X-RapidAPI-Key`, `X-RapidAPI-Host`

**Warning signs:** 401 errors in test but key works in RapidAPI playground; curl works but Python fails

**Source:** [RapidAPI Additional Request Headers](https://docs.rapidapi.com/docs/additional-request-headers)

### Pitfall 2: USAJobs Requires User-Agent with Email

**What goes wrong:** USAJobs API returns 403 or blocks requests because User-Agent header is missing or doesn't contain email

**Why it happens:** USAJobs API documentation explicitly requires `User-Agent` header containing the email address used when requesting the API key

**How to avoid:** Store email in .env (`USAJOBS_EMAIL`) and include in every request: `headers["User-Agent"] = email`

**Warning signs:** Requests work from browser/Postman but fail from Python; API returns vague 403 without details

**Source:** [USAJobs Authentication Guide](https://developer.usajobs.gov/guides/authentication)

### Pitfall 3: JSearch job_publisher Values Vary

**What goes wrong:** Source attribution fails because `job_publisher` contains unexpected values ("Monster", "ZipRecruiter", "CareerBuilder") not in LinkedIn/Indeed/Glassdoor set

**Why it happens:** JSearch aggregates from Google Jobs which includes many sources; response varies by query/location

**How to avoid:**
- Whitelist known sources: `JSEARCH_SOURCES = {"LinkedIn", "Indeed", "Glassdoor"}`
- Map unknowns to generic: `source = pub if pub in JSEARCH_SOURCES else "JSearch (Other)"`
- Log unknowns for future expansion

**Warning signs:** Progress display shows unexpected source names; jobs from unknown sources get lost

### Pitfall 4: Dedup Priority Requires Source Ordering

**What goes wrong:** JSearch copy wins over native Dice listing because dedup keeps first occurrence and JSearch runs first

**Why it happens:** Phase description says "original source wins over aggregator copy" but current dedup (deduplication.py:77) keeps first occurrence based on processing order

**How to avoid:** Either:
1. **Process native sources first** (Dice, HN Hiring) then aggregators (JSearch, USAJobs) — maintains current "first wins" logic
2. **Add source priority to dedup** — check source type during match, prefer native over aggregator

**Warning signs:** Report shows JSearch URLs for jobs that appear on native sources; users click links and land on LinkedIn instead of direct application

**Implementation note:** Existing code already separates scrapers and APIs (sources.py:1202-1207). Run scrapers first → APIs second → aggregators last.

### Pitfall 5: USAJobs Nested JSON Response Structure

**What goes wrong:** Parsing fails because response structure is `data.SearchResult.SearchResultItems` not flat `results` array like other APIs

**Why it happens:** USAJobs uses government API design patterns (verbose nesting, XML-style field names)

**How to avoid:** Defensive access with fallbacks:
```python
items = data.get("SearchResult", {}).get("SearchResultItems", [])
for item in items:
    descriptor = item.get("MatchedObjectDescriptor", {})
    title = descriptor.get("PositionTitle", "Unknown")
```

**Warning signs:** KeyError or empty results despite 200 response; test data works but real data fails

**Source:** [USAJobs Search Jobs Tutorial](https://developer.usajobs.gov/tutorials/search-jobs)

### Pitfall 6: RapidFuzz Threshold Too High for Real-World Data

**What goes wrong:** Legitimate duplicates aren't caught because 85% threshold is too strict for job titles with minor variations ("Sr. Software Engineer" vs "Senior Software Engineer")

**Why it happens:** User constraint mandates 85% threshold, but real job postings have inconsistent formatting

**How to avoid:**
- Use `token_sort_ratio` (already done) which ignores word order and handles "Sr." vs "Senior"
- Test with real data from multiple sources before finalizing
- Consider separate title threshold (80%) and company threshold (85%) if user approves change

**Warning signs:** Manual review finds obvious duplicates in report; same job URL appears multiple times

**Note:** User constraint locks 85% threshold — flag this in verification if testing shows issues

**Source:** [RapidFuzz Documentation](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html)

## Code Examples

Verified patterns from official sources and existing codebase:

### JSearch API Request (RapidAPI)

```python
# Source: RapidAPI Python example pattern
import requests
import json

def fetch_jsearch(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from JSearch API (Google Jobs aggregator)."""
    results = []

    # Check credentials
    api_key = get_api_key("JSEARCH_API_KEY", "JSearch")
    if not api_key:
        return results

    # Check rate limit (uses "jsearch" backend API key shared across linkedin/indeed/glassdoor)
    if not check_rate_limit("jsearch", verbose=verbose):
        return results

    # Build request
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {
        "query": query,
        "page": "1",
        "num_pages": "1",
        "date_posted": "week",  # week, month, 3days, all
    }
    if location:
        params["location"] = location

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            items = data.get("data", [])

            for item in items:
                job = map_jsearch_to_job_result(item)
                if job:
                    results.append(job)
        elif response.status_code in (401, 403):
            log.error("[JSearch] Authentication failed - run 'job-radar --setup-apis' to reconfigure")
        else:
            log.debug("[JSearch] Request failed: HTTP %d", response.status_code)

    except requests.RequestException as e:
        log.debug("[JSearch] Request failed: %s", e)

    log.info("[JSearch] Found %d results for '%s'", len(results), query)
    return results


def map_jsearch_to_job_result(item: dict) -> JobResult | None:
    """Map JSearch API response to JobResult.

    Uses job_publisher field for source attribution (LinkedIn, Indeed, Glassdoor).
    """
    # Required fields
    title = item.get("job_title", "").strip()
    company = item.get("employer_name", "").strip()
    url = item.get("job_apply_link", "").strip()

    if not title or not company or not url:
        return None

    # Source attribution: use original publisher, not "JSearch"
    publisher = item.get("job_publisher", "JSearch")
    KNOWN_SOURCES = {"LinkedIn", "Indeed", "Glassdoor"}
    source = publisher if publisher in KNOWN_SOURCES else "JSearch (Other)"

    # Location
    city = item.get("job_city", "")
    state = item.get("job_state", "")
    is_remote = item.get("job_is_remote", False)

    if is_remote:
        location = "Remote"
    elif city and state:
        location = f"{city}, {state}"
    else:
        location = item.get("job_country", "Unknown")

    # Salary
    salary_min = item.get("job_min_salary")
    salary_max = item.get("job_max_salary")
    if salary_min and salary_max:
        salary = f"${salary_min:,.0f} - ${salary_max:,.0f}"
    elif salary_min:
        salary = f"${salary_min:,.0f}+"
    else:
        salary = "Not specified"

    # Description
    description = item.get("job_description", "")
    description = strip_html_and_normalize(description)
    if len(description) > 500:
        description = description[:497] + "..."

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=_parse_arrangement(f"{title} {description} {location}"),
        salary=salary,
        date_posted=item.get("job_posted_at_datetime_utc", "")[:10],
        description=description,
        url=url,
        source=source,  # Use original publisher for attribution
        employment_type=item.get("job_employment_type", ""),
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="USD",
    )
```

### USAJobs API Request

```python
# Source: USAJobs API authentication guide (developer.usajobs.gov)
import requests
import json

def fetch_usajobs(query: str, location: str = "", profile: dict = None, verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from USAJobs federal government API."""
    results = []

    # Check credentials
    api_key = get_api_key("USAJOBS_API_KEY", "USAJobs")
    email = get_api_key("USAJOBS_EMAIL", "USAJobs")
    if not api_key or not email:
        return results

    # Check rate limit
    if not check_rate_limit("usajobs", verbose=verbose):
        return results

    # Build request with required headers
    url = "https://data.usajobs.gov/api/search"
    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": email,  # REQUIRED: must contain email from API request
        "Authorization-Key": api_key
    }

    params = {
        "Keyword": query,
        "ResultsPerPage": "50",
    }

    # Location filter
    if location:
        params["LocationName"] = location

    # Optional federal filters from profile
    if profile:
        gs_min = profile.get("gs_grade_min")
        gs_max = profile.get("gs_grade_max")
        if gs_min:
            params["PayGradeLow"] = f"{gs_min:02d}"  # Format: "07"
        if gs_max:
            params["PayGradeHigh"] = f"{gs_max:02d}"

        agencies = profile.get("preferred_agencies", [])
        if agencies:
            # Semicolon-delimited agency codes
            params["Organization"] = ";".join(agencies)

        # Security clearance - not available as direct API parameter
        # Would need to filter results post-fetch

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # USAJobs uses nested structure
            search_result = data.get("SearchResult", {})
            items = search_result.get("SearchResultItems", [])

            for item in items:
                job = map_usajobs_to_job_result(item)
                if job:
                    results.append(job)
        elif response.status_code in (401, 403):
            log.error("[USAJobs] Authentication failed - run 'job-radar --setup-apis' to reconfigure")
        else:
            log.debug("[USAJobs] Request failed: HTTP %d", response.status_code)

    except requests.RequestException as e:
        log.debug("[USAJobs] Request failed: %s", e)

    log.info("[USAJobs] Found %d results for '%s'", len(results), query)
    return results


def map_usajobs_to_job_result(item: dict) -> JobResult | None:
    """Map USAJobs API response to JobResult."""
    # USAJobs uses nested MatchedObjectDescriptor
    descriptor = item.get("MatchedObjectDescriptor", {})

    # Required fields
    title = descriptor.get("PositionTitle", "").strip()
    company = descriptor.get("OrganizationName", "").strip()
    url = descriptor.get("PositionURI", "").strip()

    if not title or not company or not url:
        return None

    # Location
    location = descriptor.get("PositionLocationDisplay", "")
    if not location:
        # Fallback to first item in PositionLocation array
        locations = descriptor.get("PositionLocation", [])
        if locations:
            loc_obj = locations[0]
            city = loc_obj.get("LocationName", "")
            state = loc_obj.get("CountrySubDivisionCode", "")
            location = f"{city}, {state}" if city and state else city or "Unknown"

    # Salary (PositionRemuneration array)
    salary = "Not specified"
    salary_min = None
    salary_max = None
    remuneration = descriptor.get("PositionRemuneration", [])
    if remuneration:
        rem = remuneration[0]
        min_range = rem.get("MinimumRange")
        max_range = rem.get("MaximumRange")
        if min_range and max_range:
            salary = f"${float(min_range):,.0f} - ${float(max_range):,.0f}"
            salary_min = float(min_range)
            salary_max = float(max_range)

    # Description
    description = descriptor.get("UserArea", {}).get("Details", {}).get("JobSummary", "")
    description = strip_html_and_normalize(description)
    if len(description) > 500:
        description = description[:497] + "..."

    # Date posted
    date_posted = descriptor.get("PublicationStartDate", "")
    if date_posted:
        date_posted = date_posted[:10]  # Extract YYYY-MM-DD

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company + " (Federal)", _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=_parse_arrangement(f"{title} {description}"),
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="USAJobs",
        employment_type=descriptor.get("PositionSchedule", [{}])[0].get("Name", ""),
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="USD",
    )
```

### Rate Limiter Configuration

```python
# Source: Existing rate_limits.py (Phase 31)

# Add to BACKEND_API_MAP in rate_limits.py
BACKEND_API_MAP = {
    "adzuna": "adzuna",
    "authentic_jobs": "authentic_jobs",
    # JSearch aggregator - share limiter across display sources
    "linkedin": "jsearch",
    "indeed": "jsearch",
    "glassdoor": "jsearch",
    # USAJobs - single source
    "usajobs": "usajobs",
}

# Add to config.json for rate limit overrides
{
  "rate_limits": {
    "jsearch": [
      {"limit": 100, "interval": 60},    # 100 requests/minute
      {"limit": 500, "interval": 3600}   # 500 requests/hour
    ],
    "usajobs": [
      {"limit": 60, "interval": 60}      # 60 requests/minute (conservative)
    ]
  }
}
```

### Profile Schema Extension for Federal Fields

```python
# Add to profile.json schema (optional fields)
{
  "name": "Jane Doe",
  "target_titles": ["Software Engineer", "DevOps Engineer"],
  "target_market": "Washington, DC",

  # Optional federal job filters (USAJobs only)
  "gs_grade_min": 12,           # GS grade range 01-15
  "gs_grade_max": 14,
  "preferred_agencies": [       # Agency subelement codes (semicolon-delimited in API)
    "TREAS",                    # Department of Treasury
    "DD"                        # Department of Defense
  ],
  "security_clearance": "Secret"  # None, Secret, Top Secret
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual API key entry in .env file | Interactive --setup-apis wizard with validation | Phase 30-31 (v1.1.0+) | Non-technical users can configure APIs without editing text files |
| Single global rate limit | Per-source rate limits with backend API mapping | Phase 31 (v1.1.3) | Multiple sources can share same API (JSearch) without hitting limits faster |
| Exact duplicate matching by URL | Fuzzy deduplication with 85% threshold | Phase 30 (v1.1.0) | Catches near-duplicates across sources with minor formatting differences |
| Scraper-only sources | Mixed scrapers + APIs with graceful degradation | Phase 30-31 | API sources provide structured data, fall back to scrapers when keys missing |
| Fixed .env path (~/.job-radar/) | Platform-appropriate data directory with legacy fallback | Phase 28-29 | Windows/macOS users get native paths, Linux users unaffected |

**Deprecated/outdated:**
- **pyrate-limiter v3**: Upgraded to v4 in Phase 31 — new API requires explicit cleanup (atexit handler to prevent segfaults)
- **Hardcoded source names in progress callbacks**: Phase 31 added `_SOURCE_DISPLAY_NAMES` mapping for flexible display names

**Current best practices (2026):**
- Use RapidAPI for commercial job aggregators (JSearch, SerpAPI) — handles authentication, rate limiting, uptime
- Use government APIs directly (USAJobs) — no middleman, official data source, free with registration
- Validate API keys on setup, not every request — reduces latency, clearer error messages
- Share rate limiters across sources using same backend — prevents accidental limit violations

## Open Questions

1. **JSearch source filtering vs. cost**
   - What we know: JSearch aggregates many sources beyond LinkedIn/Indeed/Glassdoor
   - What's unclear: Does filtering to specific publishers (via API params) reduce cost or does JSearch charge per request regardless?
   - Recommendation: Start with broad search, filter results client-side, monitor API usage; add publisher filter if cost becomes issue

2. **USAJobs security clearance filtering**
   - What we know: USAJobs API doesn't expose security clearance as query parameter (verified in API reference)
   - What's unclear: Is clearance data available in response? Can we filter post-fetch?
   - Recommendation: Add profile field for user preference, implement post-fetch filtering if clearance data exists in response; otherwise document limitation

3. **Multi-source badge implementation**
   - What we know: User wants "Found on 3 sources" badge when job appears on multiple boards
   - What's unclear: Where does badge appear (report only? GUI? both?), how to track source list during dedup
   - Recommendation: Extend JobResult with `sources: list[str]` field, populate during dedup when match found, display in report summary section

4. **JSearch pagination and result limits**
   - What we know: JSearch supports pagination via `page` and `num_pages` parameters
   - What's unclear: How many results per page? Should we fetch multiple pages per query?
   - Recommendation: Start with 1 page per query (matches Adzuna pattern), monitor result counts, add pagination if users report insufficient results

5. **GUI settings tab design**
   - What we know: User wants GUI fields for API key configuration (no terminal needed)
   - What's unclear: Should settings be in main tabs or separate dialog? How to trigger validation?
   - Recommendation: Add "Settings" tab to main_window.py tabview, include API key fields with "Test Connection" buttons per source

## Sources

### Primary (HIGH confidence)

- [USAJobs API Authentication Guide](https://developer.usajobs.gov/guides/authentication) - Header format, required fields
- [USAJobs API Search Reference](https://developer.usajobs.gov/API-Reference/GET-api-Search) - Query parameters (PayGradeLow/High, Organization, LocationName)
- [RapidAPI Additional Request Headers](https://docs.rapidapi.com/docs/additional-request-headers) - X-RapidAPI-Key and X-RapidAPI-Host format
- Job-Radar codebase (sources.py, api_setup.py, rate_limits.py, deduplication.py) - Verified existing patterns

### Secondary (MEDIUM confidence)

- [JSearch API on RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) - API overview, endpoint structure
- [OpenWeb Ninja JSearch Docs](https://www.openwebninja.com/api/jsearch) - Response format, field descriptions
- [RapidFuzz GitHub](https://github.com/rapidfuzz/RapidFuzz) - Similarity algorithms, threshold best practices
- [RapidFuzz Documentation](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html) - token_sort_ratio usage, score_cutoff parameter

### Tertiary (LOW confidence - needs verification)

- Medium article on JSearch API - Example response structure showing `job_publisher` and `employer_name` fields
- GitHub find-jobs repository - Referenced JSearch usage but source code not examined
- Apyflux JSearch integration article - Response field descriptions (needs direct API testing to verify)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All dependencies already in project, verified working
- Architecture: HIGH - Patterns established in Phase 30-31, direct code examples from codebase
- JSearch specifics: MEDIUM - Response structure verified via web sources, but exact parameter formats need direct API testing
- USAJobs specifics: HIGH - Official API documentation confirmed header format and query parameters
- Pitfalls: MEDIUM-HIGH - Some verified from docs (USAJobs headers, RapidAPI case), others inferred from API patterns

**Research date:** 2026-02-13
**Valid until:** ~30 days (stable APIs, unlikely to change rapidly)

**Areas requiring direct API testing:**
1. JSearch exact parameter names and valid values (date_posted, employment_types)
2. JSearch response field availability (job_min_salary, job_is_remote may vary by result)
3. USAJobs response structure for security clearance data (not documented)
4. Rate limit thresholds (start conservative, adjust based on 429 errors)
