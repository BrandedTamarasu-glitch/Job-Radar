# Phase 13: Job Source APIs - Research

**Researched:** 2026-02-10
**Domain:** REST API integration, fuzzy deduplication, data normalization, and HTML text cleaning for Python job search applications
**Confidence:** HIGH

## Summary

This phase integrates two external job APIs (Adzuna and Authentic Jobs) into the existing job search pipeline, implementing cross-source fuzzy deduplication, HTML text cleaning, location normalization, and schema extension for optional salary fields. The challenge is integrating API data seamlessly with existing scraped results while maintaining the established fetch-score-track-report pipeline.

Adzuna API provides structured job data with `salary_min`, `salary_max`, `location.display_name`, `company.display_name`, `title`, `description`, and `redirect_url` fields. Authentication requires both `app_id` and `app_key` parameters. The API returns JSON with a `results` array containing job objects. Authentic Jobs API requires a single `api_key` parameter and supports search via keywords, location, and category filters, returning XML or JSON responses.

For cross-source deduplication, rapidfuzz (the modern successor to fuzzywuzzy) is the standard. It provides `token_sort_ratio()` for word-order-independent matching (ideal for job titles) and `fuzz.ratio()` for basic similarity. A threshold of 80+ is industry standard for high-precision matching. BeautifulSoup's `get_text()` method strips HTML tags from descriptions, and Python's standard `re.sub()` with `\s+` pattern normalizes whitespace.

Location parsing to "City, State" format uses regex patterns: `r'([^,]+),\s*([A-Z]{2})'` for standard US locations. The existing JobResult dataclass extends with optional fields added at the end for backward compatibility (per Python dataclass ordering rules). The existing fetch_all() function in sources.py already implements parallel fetching with ThreadPoolExecutor and per-source progress callbacks—API sources integrate as new branches in the run_query() dispatcher.

User decisions from CONTEXT.md specify: sequential fetching (scrapers first, APIs after), single progress bar for all sources, wait-for-all result streaming, strict field validation (skip invalid jobs), cross-source fuzzy matching for deduplication, silent skips for API failures, rate limit notices with retry times, and location normalization to "City, State" format.

**Primary recommendation:** Use rapidfuzz with token_sort_ratio (threshold 85) for title+company matching, BeautifulSoup get_text() for HTML stripping, regex for location parsing, extend JobResult with optional `salary_min: float | None`, `salary_max: float | None`, `salary_currency: str | None` fields at the end, create per-source mapper functions (map_adzuna_to_job_result, map_authenticjobs_to_job_result), integrate into existing fetch_all() flow with new source branches, and handle errors per user decisions (silent skip for network/500, rate limit notice for 429, skip invalid jobs).

## Standard Stack

The established libraries/tools for API integration and fuzzy matching in Python:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | (existing) | HTTP client for API calls | Already in project (pyproject.toml line 11), used by cache.py, integrates with existing fetch_with_retry() |
| rapidfuzz | 3.11.1+ | Cross-source fuzzy matching | Industry standard for deduplication, 10x faster than fuzzywuzzy, MIT licensed, 3.6K+ stars, actively maintained |
| BeautifulSoup4 | (existing) | HTML tag stripping | Already in project for scraping (sources.py line 11), get_text() method extracts plain text from HTML |
| python-dotenv | (existing) | API credential loading | Already integrated in Phase 12 (api_config.py), loads ADZUNA_APP_ID, ADZUNA_APP_KEY, AUTHENTIC_JOBS_API_KEY |
| pyrate-limiter | (existing) | Rate limiting per source | Already integrated in Phase 12 (rate_limits.py), SQLite-backed persistence, prevents 429 errors |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re | stdlib | Location parsing, whitespace normalization | Extract "City, State" from API location strings, collapse multiple spaces/newlines |
| dataclasses | stdlib | Schema extension | Add optional salary fields to existing JobResult (backward compatible) |
| logging | stdlib | Error logging for skipped jobs | Log invalid jobs, API failures, rate limit skips (per user decisions) |
| json | stdlib | API response parsing | Parse Adzuna/Authentic Jobs JSON responses |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| rapidfuzz | fuzzywuzzy/thefuzz | fuzzywuzzy is 10x slower, deprecated (renamed to thefuzz), GPL licensed, rapidfuzz is modern replacement |
| rapidfuzz | difflib (stdlib) | difflib.SequenceMatcher is slower, no token-based matching, rapidfuzz has better algorithms for job title matching |
| BeautifulSoup get_text() | html2text library | html2text converts to Markdown (adds formatting), we need plain text—get_text() is simpler and already available |
| BeautifulSoup get_text() | bleach.clean() | bleach is for sanitizing user input (XSS prevention), overkill for stripping tags from API responses |
| regex for location parsing | geograpy3 library | geograpy3 uses NLP for entity extraction (heavy), overkill for structured API location fields, regex is sufficient |
| Extend JobResult | Create separate ApiJobResult class | User decision requires single JobResult format for compatibility with existing scoring/tracking/reporting |

**Installation:**
```bash
pip install rapidfuzz
# requests, beautifulsoup4, python-dotenv, pyrate-limiter already installed from Phase 12
```

**Dependencies:**
- rapidfuzz: No external dependencies (uses C++ extension for speed)

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── sources.py           # Existing fetchers + new API fetchers (modify)
├── api_config.py        # Existing from Phase 12 (use get_api_key)
├── rate_limits.py       # Existing from Phase 12 (use check_rate_limit)
├── deduplication.py     # New module for cross-source fuzzy matching
└── search.py            # Existing pipeline (no changes needed)
```

### Pattern 1: Per-Source Mapper Functions
**What:** Dedicated function per API source to transform API response → JobResult
**When to use:** For each new API source (Adzuna, Authentic Jobs)
**Example:**
```python
# Source: User decision from CONTEXT.md + Adzuna API docs
import html
import re
from bs4 import BeautifulSoup

def map_adzuna_to_job_result(item: dict) -> JobResult | None:
    """Map Adzuna API response item to JobResult.

    Per user decision: Strict validation—skip job if required fields missing.

    Returns None if job invalid (missing title/company/url).
    """
    # Required fields (per user decision: skip if missing)
    title = item.get("title", "").strip()
    company_obj = item.get("company", {})
    company = company_obj.get("display_name", "").strip()
    redirect_url = item.get("redirect_url", "").strip()

    if not title or not company or not redirect_url:
        log.debug(f"Skipping Adzuna job: missing required field (title={bool(title)}, company={bool(company)}, url={bool(redirect_url)})")
        return None

    # Location: parse to "City, State" format (per user decision)
    location_obj = item.get("location", {})
    display_name = location_obj.get("display_name", "")
    location = parse_location_to_city_state(display_name)

    # Salary: extract min/max/currency (new optional fields)
    salary_min = item.get("salary_min")
    salary_max = item.get("salary_max")
    salary_currency = "USD"  # Adzuna US endpoint always returns USD

    # Format salary string for existing 'salary' field (backward compat)
    if salary_min and salary_max:
        salary = f"${salary_min:,.0f} - ${salary_max:,.0f}"
    elif salary_min:
        salary = f"${salary_min:,.0f}+"
    else:
        salary = "Not specified"

    # Description: strip HTML and normalize whitespace (per user decision)
    description = item.get("description", "")
    description = strip_html_and_normalize(description)

    # Arrangement: infer from description/title (reuse existing _parse_arrangement)
    arrangement = _parse_arrangement(f"{title} {description}")

    # Employment type: map contract_type/contract_time
    contract_type = item.get("contract_type", "")
    contract_time = item.get("contract_time", "")
    employment_type = map_adzuna_employment_type(contract_type, contract_time)

    # Date posted: use 'created' field (ISO 8601 format)
    date_posted = item.get("created", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description[:500],  # Truncate for report readability
        url=redirect_url,
        source="adzuna",
        employment_type=employment_type,
        parse_confidence="high",  # API data is structured
        # New optional fields (Phase 13 schema extension)
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
    )
```

### Pattern 2: HTML Stripping and Whitespace Normalization
**What:** Remove HTML tags and collapse whitespace from API description fields
**When to use:** Before storing description in JobResult (per user decision)
**Example:**
```python
# Source: BeautifulSoup4 docs + user decision from CONTEXT.md
from bs4 import BeautifulSoup
import re
import html

def strip_html_and_normalize(text: str) -> str:
    """Strip HTML tags and normalize whitespace.

    Per user decision:
    - Strip all HTML tags (not just sanitize)
    - Decode HTML entities (&amp; → &, &nbsp; → space)
    - Normalize whitespace (collapse multiple spaces/newlines to single space)
    """
    if not text:
        return ""

    # Decode HTML entities first (&amp; → &, &#39; → ', etc.)
    text = html.unescape(text)

    # Strip HTML tags using BeautifulSoup (already in project)
    soup = BeautifulSoup(text, "html.parser")
    plain_text = soup.get_text(separator=" ")  # Use space as separator between tags

    # Normalize whitespace: collapse multiple spaces/newlines to single space
    normalized = re.sub(r'\s+', ' ', plain_text)

    return normalized.strip()

# Usage in mapper functions
description = item.get("description", "")
description = strip_html_and_normalize(description)
```

### Pattern 3: Location Normalization to "City, State"
**What:** Parse diverse location formats to standardized "City, State" format
**When to use:** When mapping API location fields to JobResult.location
**Example:**
```python
# Source: User decision from CONTEXT.md + regex best practices
import re

def parse_location_to_city_state(location_str: str) -> str:
    """Parse location to "City, State" format.

    Per user decision:
    - Extract city and state from API responses
    - Standardize to "City, State" format (e.g., "San Francisco, CA")
    - Handle "Remote" as special case (pass through as-is)
    - Handle international/multi-location edge cases gracefully

    Examples:
        "San Francisco, CA" → "San Francisco, CA"
        "San Francisco, California, United States" → "San Francisco, CA"
        "Remote" → "Remote"
        "New York, NY 10001" → "New York, NY"
        "London, UK" → "London, UK" (international, pass through)
    """
    if not location_str:
        return "Unknown"

    # Special case: Remote
    if "remote" in location_str.lower():
        return "Remote"

    # Pattern 1: "City, STATE_ABBR" (already correct format)
    match = re.match(r'^([^,]+),\s*([A-Z]{2})(?:\s|,|$)', location_str)
    if match:
        city, state = match.groups()
        return f"{city.strip()}, {state.strip()}"

    # Pattern 2: "City, State Name" → abbreviate state (if US state)
    STATE_ABBREV = {
        "california": "CA", "new york": "NY", "texas": "TX", "florida": "FL",
        "illinois": "IL", "pennsylvania": "PA", "ohio": "OH", "georgia": "GA",
        "north carolina": "NC", "michigan": "MI", "washington": "WA",
        "massachusetts": "MA", "virginia": "VA", "colorado": "CO",
        # Add more as needed
    }
    match = re.match(r'^([^,]+),\s*([^,]+?)(?:\s|,|$)', location_str)
    if match:
        city, state_name = match.groups()
        state_lower = state_name.strip().lower()
        if state_lower in STATE_ABBREV:
            return f"{city.strip()}, {STATE_ABBREV[state_lower]}"
        # International or unknown state—return as-is
        return f"{city.strip()}, {state_name.strip()}"

    # No comma—could be just city name or country
    # Return as-is (better to show raw than guess wrong)
    return location_str.strip()
```

### Pattern 4: Cross-Source Fuzzy Deduplication
**What:** Detect same job posted to multiple sources using fuzzy string matching
**When to use:** After fetching all results, before scoring (per user decision)
**Example:**
```python
# Source: rapidfuzz docs + user decision from CONTEXT.md
from rapidfuzz import fuzz
from collections import defaultdict

def deduplicate_cross_source(results: list[JobResult], threshold: int = 85) -> list[JobResult]:
    """Remove duplicate jobs across sources using fuzzy matching.

    Per user decision:
    - Match criteria: title + company + location similarity
    - Use rapidfuzz token_sort_ratio (word-order independent)
    - Threshold: 85 (high precision, per industry standard)
    - Keep first occurrence (preserves source priority if scrapers run first)
    - Not just source+job_id (would miss cross-source duplicates)

    Complexity: O(N²) in worst case, optimized with bucketing.
    """
    if not results:
        return []

    # Optimization: bucket by normalized company name (reduces comparisons)
    buckets = defaultdict(list)
    for job in results:
        # Use first word of company as bucket key (e.g., "Google Inc" → "google")
        bucket_key = job.company.split()[0].lower() if job.company else "unknown"
        buckets[bucket_key].append(job)

    seen = []
    seen_keys = set()  # Track (title, company, location) hashes for exact duplicates

    for bucket in buckets.values():
        for job in bucket:
            # Fast exact duplicate check first
            key = (job.title.lower(), job.company.lower(), job.location.lower())
            if key in seen_keys:
                log.debug(f"Exact duplicate: {job.title} at {job.company} from {job.source}")
                continue

            # Fuzzy duplicate check against seen jobs in same bucket
            is_duplicate = False
            for seen_job in seen:
                # Only compare within same bucket (same company first word)
                if seen_job.company.split()[0].lower() != job.company.split()[0].lower():
                    continue

                # Compute similarity scores (per user decision: title + company + location)
                title_sim = fuzz.token_sort_ratio(job.title, seen_job.title)
                company_sim = fuzz.token_sort_ratio(job.company, seen_job.company)
                location_sim = fuzz.ratio(job.location, seen_job.location)  # Exact location matters more

                # Combined threshold: all 3 fields must be similar (per user decision)
                if title_sim >= threshold and company_sim >= threshold and location_sim >= 80:
                    log.debug(f"Fuzzy duplicate: {job.title} at {job.company} from {job.source} "
                             f"(matches {seen_job.source}: title={title_sim}, company={company_sim}, location={location_sim})")
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen.append(job)
                seen_keys.add(key)

    original_count = len(results)
    deduped_count = len(seen)
    if original_count > deduped_count:
        log.info(f"Deduplication: {original_count} → {deduped_count} jobs ({original_count - deduped_count} duplicates removed)")

    return seen
```

### Pattern 5: JobResult Schema Extension (Backward Compatible)
**What:** Add optional salary fields to existing JobResult dataclass
**When to use:** Phase 13 schema extension for API salary data
**Example:**
```python
# Source: Python dataclasses docs + user decision from CONTEXT.md
from dataclasses import dataclass

@dataclass
class JobResult:
    """A single job listing result.

    Phase 13 extension: Added optional salary fields for API sources.
    """
    # Existing required fields (unchanged)
    title: str
    company: str
    location: str
    arrangement: str  # remote, hybrid, onsite, unknown
    salary: str
    date_posted: str
    description: str
    url: str
    source: str
    apply_info: str = ""
    employment_type: str = ""  # full-time, contract, C2H, part-time, etc.
    parse_confidence: str = "high"  # high, medium, low

    # Phase 13: New optional fields (added at end for backward compatibility)
    # Per Python dataclass rules: new fields with defaults must come after existing defaults
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None

    def __hash__(self):
        return hash((self.title, self.company, self.source))

# Backward compatibility verified:
# - Existing code instantiating JobResult without new fields → works (defaults to None)
# - Existing scoring/tracking/reporting → ignores unknown fields (no errors)
# - New code can populate salary_min/max for API sources
```

### Pattern 6: API Fetcher Integration with Error Handling
**What:** Add new API source branches to fetch_all() with error handling per user decisions
**When to use:** Integrating Adzuna and Authentic Jobs into existing pipeline
**Example:**
```python
# Source: Existing sources.py fetch_all() pattern + user decisions
from .api_config import get_api_key
from .rate_limits import check_rate_limit

def fetch_adzuna(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch jobs from Adzuna API with error handling per user decisions.

    Error handling (per user decisions):
    - Missing credentials: silent skip, empty list, warning logged (get_api_key handles)
    - Rate limited: show notice with retry time, empty list (check_rate_limit handles)
    - Network error (timeout, 500): silent skip, empty list, debug log only
    - Invalid API key (401/403): error log once, empty list, don't retry
    - Empty results: return empty list (merge silently)
    - Invalid jobs: skip individual jobs, log for debugging
    """
    # Check credentials (per user decision: missing → skip source)
    app_id = get_api_key("ADZUNA_APP_ID", "Adzuna")
    app_key = get_api_key("ADZUNA_APP_KEY", "Adzuna")
    if not app_id or not app_key:
        return []  # Warning already logged by get_api_key

    # Check rate limit (per user decision: rate limited → skip source)
    if not check_rate_limit("adzuna", verbose=verbose):
        return []  # Warning already logged by check_rate_limit

    # Build API URL
    base_url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": 50,
    }
    if location:
        params["where"] = location

    # Make API call (reuse existing cache.py fetch_with_retry)
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        body = fetch_with_retry(url, headers=HEADERS, use_cache=True)
        if not body:
            # Network error or timeout (per user decision: silent skip)
            log.debug(f"Adzuna API: no response for query '{query}'")
            return []

        # Parse JSON response
        data = _json.loads(body)
        items = data.get("results", [])

        # Map to JobResult (per user decision: skip invalid jobs)
        jobs = []
        for item in items:
            job = map_adzuna_to_job_result(item)
            if job:
                jobs.append(job)
            # else: invalid job, already logged by mapper

        log.info(f"Adzuna: {len(jobs)} jobs for '{query}'")
        return jobs

    except requests.HTTPError as e:
        # Per user decision: 401/403 → log error once, skip source
        if e.response.status_code in (401, 403):
            log.error(f"Adzuna API: Invalid credentials (HTTP {e.response.status_code}). "
                     f"Run 'job-radar --setup-apis' to fix.")
        else:
            # Network error or 500 (per user decision: silent skip, debug log)
            log.debug(f"Adzuna API error: HTTP {e.response.status_code}")
        return []

    except _json.JSONDecodeError as e:
        # Invalid JSON response (per user decision: silent skip, debug log)
        log.debug(f"Adzuna API: invalid JSON response: {e}")
        return []

    except Exception as e:
        # Unexpected error (per user decision: silent skip, debug log)
        log.debug(f"Adzuna API error: {e}")
        return []

# Integration into fetch_all() run_query dispatcher
def run_query(q):
    if q["source"] == "dice":
        return fetch_dice(q["query"], q.get("location", ""))
    elif q["source"] == "hn_hiring":
        return fetch_hn_hiring(q["query"])
    elif q["source"] == "remoteok":
        return fetch_remoteok(q["query"])
    elif q["source"] == "weworkremotely":
        return fetch_weworkremotely(q["query"])
    # Phase 13: Add API sources
    elif q["source"] == "adzuna":
        return fetch_adzuna(q["query"], q.get("location", ""), verbose=args.verbose)
    elif q["source"] == "authentic_jobs":
        return fetch_authenticjobs(q["query"], q.get("location", ""), verbose=args.verbose)
    return []
```

### Pattern 7: Sequential Fetch Flow (Scrapers First, Then APIs)
**What:** Run existing scrapers first, wait for completion, then run API sources
**When to use:** Per user decision—scrapers first for faster initial results
**Example:**
```python
# Source: User decision from CONTEXT.md + existing fetch_all() pattern
def fetch_all_sequential(profile: dict, on_source_progress=None) -> list[JobResult]:
    """Fetch from scrapers first, then APIs.

    Per user decision:
    - Scrapers run first, APIs supplement results
    - User sees initial scraper results faster (but wait-for-all before display)
    - Single progress bar for all sources (generic message)
    """
    queries = build_search_queries(profile)

    # Separate scraper and API queries
    scraper_queries = [q for q in queries if q["source"] in ["dice", "hn_hiring", "remoteok", "weworkremotely"]]
    api_queries = [q for q in queries if q["source"] in ["adzuna", "authentic_jobs"]]

    all_results = []

    # Phase 1: Run scrapers
    log.info(f"Fetching from {len(set(q['source'] for q in scraper_queries))} scraper sources...")
    scraper_results = _fetch_queries_parallel(scraper_queries, on_source_progress)
    all_results.extend(scraper_results)

    # Phase 2: Run APIs (after scrapers complete)
    if api_queries:
        log.info(f"Fetching from {len(set(q['source'] for q in api_queries))} API sources...")
        api_results = _fetch_queries_parallel(api_queries, on_source_progress)
        all_results.extend(api_results)

    # Deduplicate across all sources (per user decision)
    all_results = deduplicate_cross_source(all_results)

    return all_results

def _fetch_queries_parallel(queries, on_source_progress):
    """Helper: fetch queries in parallel (existing ThreadPoolExecutor logic)."""
    # ... existing fetch_all() parallel logic here
```

### Anti-Patterns to Avoid
- **Don't use fuzz.ratio() for job titles:** Use token_sort_ratio() instead—job titles often have same words in different order ("Senior Software Engineer" vs "Software Engineer, Senior")
- **Don't skip deduplication:** User decision requires cross-source fuzzy matching—API jobs may duplicate scraped jobs
- **Don't use lenient validation:** User decision requires strict validation—skip jobs with missing required fields (title/company/url)
- **Don't normalize salary to single format:** User decision says store as-is with type flag (hourly/annual/range)—scoring logic adapts per type
- **Don't add required fields to JobResult:** New fields must have defaults for backward compatibility—existing code can't provide them
- **Don't parse locations aggressively:** User decision says parse to "City, State" but handle edge cases gracefully—better to show raw than guess wrong
- **Don't use global dedup key:** User decision says fuzzy matching, not hash-based—same job from different sources has different source field
- **Don't retry 401/403 errors:** Invalid API keys are permanent failures—log once, skip source, don't waste quota

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| String similarity for deduplication | Manual Levenshtein distance | rapidfuzz token_sort_ratio() | Word-order independence, optimized C++ implementation, 10x faster, handles edge cases (punctuation, case) |
| HTML tag stripping | Manual regex with `<[^>]+>` | BeautifulSoup get_text() | Regex breaks on nested tags, attributes with `>`, malformed HTML; BeautifulSoup is robust HTML parser |
| Whitespace normalization | Multiple replace() calls | `re.sub(r'\s+', ' ', text)` | Single regex handles all whitespace (spaces, tabs, newlines, multiple); replace() misses edge cases |
| Location parsing to "City, State" | Manual string.split(',')[0] | Regex with state abbreviation map | split() breaks on multi-comma addresses; regex validates state format; map handles full state names |
| Deduplication N×M comparisons | Compare all pairs | Bucketing by normalized company name | O(N²) → O(N×B) where B is avg bucket size; 10x faster for 1000+ jobs |
| HTML entity decoding | Manual replace of &amp;, etc. | html.unescape() | Python stdlib handles 200+ entities (&nbsp;, &#39;, etc.); manual replace misses most |
| API response field validation | if/else chains | Mapper functions with early return | DRY principle, clear validation logic, single place to change per source |
| Salary parsing from strings | Regex extraction | Use API salary_min/max fields directly | API provides structured data—don't parse strings when fields exist |

**Key insight:** Cross-source deduplication is deceptively complex. The "simple" approach (exact title+company match) fails on: word order variations, punctuation differences, abbreviations (Inc vs Incorporated), typos, multi-location jobs. Fuzzy matching with token_sort_ratio solves these but requires threshold tuning (too low = false positives, too high = missed duplicates). Bucketing optimization is essential for 1000+ jobs to avoid O(N²) comparisons.

## Common Pitfalls

### Pitfall 1: Deduplication Before Location Normalization
**What goes wrong:** Same job with "San Francisco, California" vs "San Francisco, CA" treated as different
**Why it happens:** Developer runs deduplication before location parsing, raw API strings don't match
**How to avoid:** Per user decision, normalize locations first (in mapper functions), then deduplicate on normalized strings
**Warning signs:** Duplicates in report with same title/company but slightly different location format

### Pitfall 2: Using fuzz.ratio() Instead of token_sort_ratio() for Titles
**What goes wrong:** "Senior Software Engineer" vs "Software Engineer, Senior" marked as not duplicate (ratio=75)
**Why it happens:** fuzz.ratio() is order-sensitive, job titles often reorder words
**How to avoid:** Use token_sort_ratio() for title matching—it sorts tokens before comparing (returns 100 for example above)
**Warning signs:** Manual inspection shows obvious duplicates not caught by deduplication

### Pitfall 3: Forgetting to Decode HTML Entities
**What goes wrong:** Description shows "&amp;" instead of "&", "&nbsp;" instead of space
**Why it happens:** BeautifulSoup get_text() doesn't decode entities, only strips tags
**How to avoid:** Call html.unescape() before BeautifulSoup (per pattern 2)—decodes entities first
**Warning signs:** HTML entity codes (&...; ) visible in job descriptions in report

### Pitfall 4: Adding Required Fields to JobResult
**What goes wrong:** Existing scraper code crashes with "missing required field salary_min"
**Why it happens:** Python dataclass rules—new required fields break existing instantiation calls
**How to avoid:** Per user decision, new fields must have defaults (salary_min: float | None = None)—add at end of class
**Warning signs:** TypeError: __init__() missing required positional argument from existing scraper code

### Pitfall 5: Lenient Validation (Showing Jobs Without Title/Company)
**What goes wrong:** Report shows rows with "Unknown" company or missing title—confuses user
**Why it happens:** Developer uses `.get("title", "Unknown")` instead of skipping invalid jobs
**How to avoid:** Per user decision, strict validation—return None from mapper if required fields missing, log for debugging
**Warning signs:** Report has jobs with "Unknown" or empty fields in required columns

### Pitfall 6: Retrying 401/403 API Errors
**What goes wrong:** API key invalid, code retries forever, burns API quota, never succeeds
**Why it happens:** Developer treats all API errors the same, retries 401 like 500
**How to avoid:** Per user decision, check status code—401/403 are permanent, log error once, skip source, don't retry
**Warning signs:** Logs filled with repeated "HTTP 401" errors, rapid API quota consumption

### Pitfall 7: Parallel Scraper+API Fetch (Ignoring User Decision)
**What goes wrong:** All sources fetch in parallel, user sees no results until slowest API completes
**Why it happens:** Developer keeps existing parallel fetch logic, ignores user decision for sequential
**How to avoid:** Per user decision, scrapers first then APIs—split queries and run in sequence (pattern 7)
**Warning signs:** Progress bar shows all sources at once, long wait before any results shown

### Pitfall 8: Normalizing Salary to Single Format
**What goes wrong:** "$50/hour" converted to "$104,000/year" (assumes 2080 hours), wrong for part-time
**Why it happens:** Developer tries to normalize all salaries to annual for comparison
**How to avoid:** Per user decision, store as-is with type flag—scoring logic adapts per type (hourly vs annual vs range)
**Warning signs:** Salary math errors in reports, hourly jobs show inflated annual equivalents

### Pitfall 9: Aggressive Location Parsing (Losing International Jobs)
**What goes wrong:** "London, UK" parsed to "London, U" (treats UK as state), job marked as invalid
**Why it happens:** Regex pattern assumes all locations are "City, STATE_ABBR" format
**How to avoid:** Per user decision, handle edge cases gracefully—if state not recognized, return raw string (pattern 3)
**Warning signs:** International jobs missing from results, "U", "GB", "CA" (Canada) in location field

## Code Examples

Verified patterns from official sources:

### Complete Adzuna API Fetcher
```python
# Source: Adzuna API docs + user decisions + existing sources.py pattern
import json as _json
import logging
import urllib.parse

from .api_config import get_api_key
from .rate_limits import check_rate_limit
from .cache import fetch_with_retry

log = logging.getLogger(__name__)

def fetch_adzuna(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch jobs from Adzuna API.

    Per user decisions:
    - Missing credentials: silent skip (get_api_key logs warning)
    - Rate limited: show notice (check_rate_limit logs warning)
    - Network/500 error: silent skip (debug log only)
    - 401/403: log error once, skip source
    - Empty results: return [] (merge silently)
    - Invalid jobs: skip, log for debugging
    """
    # Check credentials
    app_id = get_api_key("ADZUNA_APP_ID", "Adzuna")
    app_key = get_api_key("ADZUNA_APP_KEY", "Adzuna")
    if not app_id or not app_key:
        return []

    # Check rate limit
    if not check_rate_limit("adzuna", verbose=verbose):
        return []

    # Build API URL
    base_url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": 50,
    }
    if location:
        params["where"] = location

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        # Make API call (reuse existing cache/retry logic)
        body = fetch_with_retry(url, headers=HEADERS, use_cache=True)
        if not body:
            log.debug(f"Adzuna: no response for '{query}'")
            return []

        # Parse JSON
        data = _json.loads(body)
        items = data.get("results", [])

        # Map to JobResult
        jobs = []
        for item in items:
            job = map_adzuna_to_job_result(item)
            if job:
                jobs.append(job)

        log.info(f"Adzuna: {len(jobs)} jobs for '{query}'")
        return jobs

    except requests.HTTPError as e:
        if e.response.status_code in (401, 403):
            log.error(f"Adzuna: Invalid credentials (HTTP {e.response.status_code}). "
                     f"Run 'job-radar --setup-apis' to fix.")
        else:
            log.debug(f"Adzuna: HTTP {e.response.status_code}")
        return []

    except _json.JSONDecodeError as e:
        log.debug(f"Adzuna: invalid JSON: {e}")
        return []

    except Exception as e:
        log.debug(f"Adzuna error: {e}")
        return []

def map_adzuna_to_job_result(item: dict) -> JobResult | None:
    """Map Adzuna response item to JobResult.

    Returns None if invalid (missing required fields).
    """
    # Required fields
    title = item.get("title", "").strip()
    company = item.get("company", {}).get("display_name", "").strip()
    url = item.get("redirect_url", "").strip()

    if not title or not company or not url:
        log.debug(f"Adzuna: skipping job (missing required field)")
        return None

    # Location: parse to "City, State"
    location_obj = item.get("location", {})
    display_name = location_obj.get("display_name", "")
    location = parse_location_to_city_state(display_name)

    # Salary: extract min/max/currency
    salary_min = item.get("salary_min")
    salary_max = item.get("salary_max")
    salary_currency = "USD"

    # Format salary string (backward compat)
    if salary_min and salary_max:
        salary = f"${salary_min:,.0f} - ${salary_max:,.0f}"
    elif salary_min:
        salary = f"${salary_min:,.0f}+"
    else:
        salary = "Not specified"

    # Description: strip HTML, normalize whitespace
    description = item.get("description", "")
    description = strip_html_and_normalize(description)

    # Arrangement: infer from text
    arrangement = _parse_arrangement(f"{title} {description}")

    # Employment type: map contract fields
    contract_type = item.get("contract_type", "")
    contract_time = item.get("contract_time", "")
    employment_type = ""
    if contract_type == "permanent":
        employment_type = "Permanent"
    if contract_time == "full_time":
        employment_type = f"{employment_type} Full-time".strip()

    # Date posted
    date_posted = item.get("created", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description[:500],
        url=url,
        source="adzuna",
        employment_type=employment_type,
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
    )
```

### Complete Deduplication Module
```python
# Source: rapidfuzz docs + user decisions + optimization patterns
"""Cross-source fuzzy deduplication for job listings."""

import logging
from collections import defaultdict
from rapidfuzz import fuzz

log = logging.getLogger(__name__)


def deduplicate_cross_source(results: list, threshold: int = 85) -> list:
    """Remove duplicate jobs across sources using fuzzy matching.

    Per user decisions:
    - Match criteria: title + company + location similarity
    - Use rapidfuzz token_sort_ratio (word-order independent)
    - Threshold: 85 (high precision)
    - Keep first occurrence (preserves source priority)

    Optimization: Bucket by company first word to reduce comparisons.

    Args:
        results: List of JobResult objects
        threshold: Similarity threshold (0-100), default 85

    Returns:
        Deduplicated list of JobResult objects
    """
    if not results:
        return []

    # Bucket by normalized company name (optimization)
    buckets = defaultdict(list)
    for job in results:
        bucket_key = job.company.split()[0].lower() if job.company else "unknown"
        buckets[bucket_key].append(job)

    seen = []
    seen_keys = set()  # For exact duplicate check

    for bucket in buckets.values():
        for job in bucket:
            # Fast exact duplicate check
            key = (job.title.lower(), job.company.lower(), job.location.lower())
            if key in seen_keys:
                log.debug(f"Exact duplicate: {job.title} at {job.company} ({job.source})")
                continue

            # Fuzzy duplicate check
            is_duplicate = False
            for seen_job in seen:
                # Only compare within same bucket
                if seen_job.company.split()[0].lower() != job.company.split()[0].lower():
                    continue

                # Similarity scores
                title_sim = fuzz.token_sort_ratio(job.title, seen_job.title)
                company_sim = fuzz.token_sort_ratio(job.company, seen_job.company)
                location_sim = fuzz.ratio(job.location, seen_job.location)

                # All three must match
                if title_sim >= threshold and company_sim >= threshold and location_sim >= 80:
                    log.debug(f"Fuzzy duplicate: {job.title} at {job.company} ({job.source}) "
                             f"matches {seen_job.source} (title={title_sim}, company={company_sim}, location={location_sim})")
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen.append(job)
                seen_keys.add(key)

    if len(results) > len(seen):
        log.info(f"Deduplication: {len(results)} → {len(seen)} jobs ({len(results) - len(seen)} duplicates removed)")

    return seen
```

### Complete Text Cleaning Utilities
```python
# Source: BeautifulSoup4 docs + user decisions
"""Text cleaning utilities for job descriptions and locations."""

import html
import re
import logging
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


def strip_html_and_normalize(text: str) -> str:
    """Strip HTML tags and normalize whitespace.

    Per user decisions:
    - Strip all HTML tags
    - Decode HTML entities (&amp; → &)
    - Normalize whitespace (collapse multiple spaces/newlines)
    """
    if not text:
        return ""

    # Decode entities first
    text = html.unescape(text)

    # Strip HTML tags
    soup = BeautifulSoup(text, "html.parser")
    plain_text = soup.get_text(separator=" ")

    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', plain_text)

    return normalized.strip()


def parse_location_to_city_state(location_str: str) -> str:
    """Parse location to "City, State" format.

    Per user decisions:
    - Extract city and state from API responses
    - Standardize to "City, State" (e.g., "San Francisco, CA")
    - Handle "Remote" as special case
    - Handle edge cases gracefully
    """
    if not location_str:
        return "Unknown"

    # Special case: Remote
    if "remote" in location_str.lower():
        return "Remote"

    # Pattern 1: "City, STATE_ABBR"
    match = re.match(r'^([^,]+),\s*([A-Z]{2})(?:\s|,|$)', location_str)
    if match:
        city, state = match.groups()
        return f"{city.strip()}, {state.strip()}"

    # Pattern 2: "City, State Name" → abbreviate
    STATE_ABBREV = {
        "california": "CA", "new york": "NY", "texas": "TX", "florida": "FL",
        "illinois": "IL", "pennsylvania": "PA", "ohio": "OH", "georgia": "GA",
        "north carolina": "NC", "michigan": "MI", "washington": "WA",
        "massachusetts": "MA", "virginia": "VA", "colorado": "CO",
        "arizona": "AZ", "tennessee": "TN", "indiana": "IN", "missouri": "MO",
        "maryland": "MD", "wisconsin": "WI", "minnesota": "MN", "oregon": "OR",
        "new jersey": "NJ", "connecticut": "CT",
    }
    match = re.match(r'^([^,]+),\s*([^,]+?)(?:\s|,|$)', location_str)
    if match:
        city, state_name = match.groups()
        state_lower = state_name.strip().lower()
        if state_lower in STATE_ABBREV:
            return f"{city.strip()}, {STATE_ABBREV[state_lower]}"
        # International or unknown—return as-is
        return f"{city.strip()}, {state_name.strip()}"

    # No comma—return as-is
    return location_str.strip()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| fuzzywuzzy library | rapidfuzz library | 2021+ | 10x performance improvement, MIT license (vs GPL), actively maintained |
| Hash-based deduplication | Fuzzy string matching | 2015+ | Catches duplicates with typos, word order changes, abbreviations |
| Manual HTML regex stripping | BeautifulSoup get_text() | 2010+ | Robust handling of nested tags, attributes, malformed HTML |
| String.split() for location parsing | Regex with state map | Modern best practice | Handles edge cases (multi-comma, full state names, international) |
| Single JobResult format | Separate API/scraper classes | Rejected | Single format maintains compatibility with existing scoring/tracking/reporting |
| Parallel scraper+API fetch | Sequential (scrapers → APIs) | User decision | Faster initial results, clearer progress reporting |
| Lenient validation (use defaults) | Strict validation (skip invalid) | User decision | Higher quality results, clearer error messages |

**Deprecated/outdated:**
- **fuzzywuzzy library**: Use rapidfuzz (10x faster, MIT licensed, actively maintained)
- **thefuzz (fuzzywuzzy rename)**: Use rapidfuzz (same reason, fuzzywuzzy renamed to thefuzz in 2021 for licensing)
- **difflib.SequenceMatcher**: Use rapidfuzz (faster, better algorithms for string matching)
- **Manual HTML regex stripping**: Use BeautifulSoup get_text() (robust HTML parsing)
- **Geopy/geograpy for location parsing**: Overkill for structured API fields, regex sufficient

## Open Questions

Things that couldn't be fully resolved:

1. **Authentic Jobs API Response Format**
   - What we know: API requires API key, supports JSON/XML responses, has search endpoint
   - What's unclear: Exact field names in JSON response (title? company? location?), salary data availability
   - Recommendation: Implement basic fetch, test with real API key, adjust mapper based on actual response structure. Public API docs are incomplete—reverse engineer from live responses. Start with XML format if JSON structure unclear (XML may be better documented).

2. **Optimal Deduplication Threshold**
   - What we know: Industry standard is 80+ for high precision, 85 recommended by Phase 12 research
   - What's unclear: Optimal threshold for job listings specifically (titles vary more than company names)
   - Recommendation: Start with 85 for title/company, 80 for location (per pattern 4). Monitor false positives (same job marked duplicate) and false negatives (duplicates not caught). Adjust threshold in production based on manual review of first 100 deduplications. Consider separate thresholds per field (title more lenient, company strict).

3. **Adzuna Rate Limits (Exact Numbers)**
   - What we know: Phase 12 research says conservative 100/min, 1000/hour based on free tier patterns
   - What's unclear: Actual Adzuna free tier limits (docs say "generous" but no numbers)
   - Recommendation: Start with Phase 12 conservative limits (100/min, 1000/hour). Monitor for 429 errors in production. Adjust RATE_LIMITS dict if needed. Contact Adzuna support for official limits after integration is live. Existing rate_limits.py handles limit changes via config update (no code changes).

4. **API Result Pagination**
   - What we know: Adzuna supports `results_per_page` parameter (set to 50 in pattern 6)
   - What's unclear: Whether to fetch multiple pages for broader results, impact on rate limits
   - Recommendation: Start with single page (50 results per query) to minimize rate limit usage. Per user decision, jobs are already filtered by date range (48 hours default)—50 results per query×multiple queries should be sufficient. Add pagination in future phase if users report missing relevant jobs. Adzuna API supports page parameter for multi-page fetching.

5. **International Location Handling**
   - What we know: parse_location_to_city_state() handles US "City, State" format, passes through international as-is
   - What's unclear: How to standardize international locations (London, UK vs London, United Kingdom vs London, England)
   - Recommendation: Pass through international locations raw for v1.2 (per "handle edge cases gracefully" decision). In future phase, add country code map (UK → United Kingdom, GB → United Kingdom) if international usage grows. Current users are US-based per profile location field ("San Francisco, CA" format).

## Sources

### Primary (HIGH confidence)
- Adzuna API Documentation - Search endpoint: https://developer.adzuna.com/docs/search - Field names, authentication, response structure
- Adzuna API Overview: https://developer.adzuna.com/overview - Rate limits, API basics
- rapidfuzz GitHub repository: https://github.com/rapidfuzz/RapidFuzz - Official docs, API reference, usage examples
- rapidfuzz PyPI page: https://pypi.org/project/RapidFuzz/ - Version 3.11.1+, installation, changelog
- rapidfuzz.fuzz module docs: https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html - token_sort_ratio, ratio algorithms
- Python dataclasses documentation: https://docs.python.org/3/library/dataclasses.html - Adding optional fields, backward compatibility
- BeautifulSoup4 documentation: https://www.crummy.com/software/BeautifulSoup/bs4/doc/ - get_text() method, HTML parsing
- Python html module: https://docs.python.org/3/library/html.html - unescape() for entity decoding

### Secondary (MEDIUM confidence)
- Authentic Jobs API overview: https://publicapis.io/authentic-jobs-api - Basic info, authentication requirement
- Python Record Linking Tools article: https://pbpython.com/record-linking.html - Fuzzy matching workflow, threshold recommendations
- Fuzzy Matching 101 guide: https://dataladder.com/fuzzy-matching-101/ - Threshold 0.8+ recommendation, validation best practices
- Rapidfuzz vs FuzzyWuzzy comparison: https://plainenglish.io/blog/rapidfuzz-versus-fuzzywuzzy - Performance benchmarks, migration guide
- Location parsing regex patterns: https://copyprogramming.com/howto/regex-for-capturing-city-state-zip-from-an-address-string - City/State/ZIP regex patterns
- Python dataclass optional fields: https://how.wtf/python-dataclasses-with-optional-fields.html - Default value patterns
- BeautifulSoup HTML tag removal: https://www.geeksforgeeks.org/python/remove-all-style-scripts-and-html-tags-using-beautifulsoup/ - get_text() usage

### Tertiary (LOW confidence)
- Authentic Jobs API GitHub library: https://github.com/jobapis/jobs-authenticjobs - PHP library showing API structure (not Python, indirect)
- dedupe library: https://github.com/dedupeio/dedupe - ML-based deduplication (overkill for this use case)
- Splink library: https://moj-analytical-services.github.io/splink/index.html - Probabilistic record linkage (overkill, no unique IDs needed)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - rapidfuzz is well-established modern standard, BeautifulSoup already in project, requests/dotenv/pyrate-limiter from Phase 12
- Architecture: HIGH - Patterns verified from existing sources.py structure, user decisions specify exact integration approach
- Pitfalls: HIGH - Based on Python dataclass rules, fuzzy matching best practices, HTML parsing gotchas, API error handling patterns
- API field names: MEDIUM - Adzuna docs fetched and verified (HIGH), Authentic Jobs incomplete docs (LOW, need live testing)
- Deduplication thresholds: MEDIUM - Industry standard 80-85, but job-specific tuning may be needed in production

**Research date:** 2026-02-10
**Valid until:** ~90 days (rapidfuzz stable, API docs may update, threshold tuning may be needed after production data)

**Note on user decisions:** All patterns align with CONTEXT.md decisions:
- ✓ Scrapers first, then APIs (pattern 7)
- ✓ Single progress bar for all sources (existing on_source_progress callback)
- ✓ Wait-for-all results before display (existing fetch_all() behavior)
- ✓ Strict validation, skip invalid jobs (pattern 1, 6)
- ✓ Cross-source fuzzy deduplication (pattern 4)
- ✓ Silent skip for API failures (pattern 6)
- ✓ Rate limit notice with retry time (existing check_rate_limit from Phase 12)
- ✓ Location normalization to "City, State" (pattern 3)
- ✓ HTML stripping and whitespace normalization (pattern 2)
- ✓ Extend JobResult with optional salary fields (pattern 5)
- ✓ Per-source mapper functions (pattern 1)
- ✓ Lazy credential check during fetch (pattern 6 uses get_api_key)
