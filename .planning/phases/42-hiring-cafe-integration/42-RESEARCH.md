# Phase 42: hiring.cafe Integration - Research

**Researched:** 2026-02-16
**Domain:** Job board API integration, data normalization, rate limiting
**Confidence:** MEDIUM

## Summary

hiring.cafe is an AI-powered job search platform that aggregates remote-focused positions with transparent salary information. **Critical finding:** hiring.cafe does NOT have a public official API. Integration must use either third-party scraping services (Apify) or web scraping approaches.

The existing Job Radar architecture uses a source adapter pattern with dedicated mapper functions, built-in deduplication, and SQLite-backed rate limiting. Adding hiring.cafe requires deciding between third-party API services ($1/1000 jobs via Apify) or implementing direct web scraping.

**Primary recommendation:** Use Apify's hiring.cafe scraper API for structured JSON responses with 50+ data points including salary ranges, or implement direct web scraping if cost is a concern.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
**Search & filtering:**
- Use job titles from the user's profile as the search query to hiring.cafe
- Location filtering: use server-side filtering first (if API supports), then refine locally for edge cases
- Remote jobs always included regardless of location preference
- Request volume: match existing sources (~50-100 per query), not the full 1000 maximum

**Salary data handling:**
- Standardized range format: normalize to "$120K-$160K" annual range, consistent across sources
- Missing salary: show "Not listed" as explicit placeholder
- Salary included in scoring — jobs with salary in the user's desired range score higher
- Non-standard formats (hourly, monthly) converted to annual equivalent

**Deduplication strategy:**
- Title + Company exact match for dedup (same title AND same company = duplicate)
- When duplicate found, keep the listing with more data (salary, full description, more metadata)
- Dedup happens before scoring — remove duplicates first, score unique jobs only
- Source label ("hiring.cafe") shown in report — each job shows its source

**Failure & graceful degradation:**
- Silent skip on API failure — other 10 sources continue, no error message to user
- No retry — fail fast, one attempt only, move on to other sources
- Timeout: match existing source timeout values
- Malformed data: skip individual bad entries but keep good ones from same response

### Claude's Discretion
- Exact API endpoint discovery and query parameter mapping
- How to detect and handle hiring.cafe pagination
- Salary normalization formulas (hourly × 2080, monthly × 12, etc.)
- How to integrate into existing source pipeline (adapter pattern, etc.)
- Field mapping from hiring.cafe response to Job Radar schema
- Rate limiting implementation (60 req/hour per requirements)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core: HTTP Client & Parsing
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.31+ | HTTP requests | Already used by all Job Radar sources, proven retry/timeout handling |
| BeautifulSoup4 | 4.12+ | HTML parsing | Used by Dice, HN Hiring, WWR scrapers in existing codebase |
| pyrate-limiter | 3.7+ | Rate limiting | Already integrated with SQLite backend for persistent limits |

### Supporting: Data Handling
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| rapidfuzz | 3.6+ | Fuzzy deduplication | Already used for cross-source dedup with token_sort_ratio |
| sqlite3 | stdlib | Rate limit persistence | Built-in, already configured for .rate_limits/ directory |

### Third-Party API Option
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| apify-client | 1.7+ | Apify API integration | If using paid Apify scraper ($1/1000 jobs) |

**Installation:**
```bash
# No new dependencies needed for scraping approach
# requests, bs4, pyrate-limiter already in requirements.txt

# If using Apify integration
pip install apify-client
```

## Architecture Patterns

### Recommended Project Structure
```
job_radar/
├── sources.py           # Add fetch_hiringcafe() and map_hiringcafe_to_job_result()
├── rate_limits.py       # Add "hiringcafe": [Rate(60, Duration.HOUR)] to RATE_LIMITS
└── deduplication.py     # No changes needed, cross-source dedup already handles it
```

### Pattern 1: Source Adapter Pattern (Follow Existing Sources)
**What:** Implement two functions: fetcher and mapper
**When to use:** All new sources follow this pattern
**Example:**
```python
# Source: Existing Job Radar codebase (sources.py)

def fetch_hiringcafe(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from hiring.cafe (via scraping or API)."""
    results = []

    # Check rate limit first
    if not check_rate_limit("hiringcafe", verbose=verbose):
        return results

    # Build request URL/params
    # - Use query as job title search
    # - Apply location filter if supported
    # - Limit results to ~50-100 (not 1000 max)

    # Fetch with retry (timeout=15, retries=3)
    body = fetch_with_retry(url, headers=HEADERS, use_cache=True)
    if body is None:
        log.debug("[hiring.cafe] Fetch failed for '%s'", query)
        return results

    # Parse response
    data = json.loads(body)  # or BeautifulSoup(body, "html.parser") for scraping

    for item in data.get("jobs", []):
        job = map_hiringcafe_to_job_result(item)
        if job:
            results.append(job)

    log.info("[hiring.cafe] Found %d results for '%s'", len(results), query)
    return results


def map_hiringcafe_to_job_result(item: dict) -> JobResult | None:
    """Map hiring.cafe API response item to JobResult."""
    # Validate required fields first
    title = item.get("jobTitle", "").strip()
    company = item.get("companyName", "").strip()
    url = item.get("url", "").strip()

    if not title or not company or not url:
        log.debug("[hiring.cafe] Skipping job with missing required fields")
        return None

    # Parse salary with normalization
    salary_min = item.get("salary_min")
    salary_max = item.get("salary_max")
    salary = _format_salary_range(salary_min, salary_max)

    # Location normalization
    location_raw = item.get("location", "Remote")
    location = parse_location_to_city_state(location_raw)

    # Description cleaning
    description = strip_html_and_normalize(item.get("description", ""))
    if len(description) > 500:
        description = description[:497] + "..."

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=_parse_arrangement(f"{title} {description}"),
        salary=salary,
        date_posted=item.get("date_posted", ""),
        description=description,
        url=url,
        source="hiringcafe",
        employment_type=item.get("employment_type", ""),
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="USD",
    )
```

### Pattern 2: Pipeline Integration (Add to build_search_queries)
**What:** Generate search queries for hiring.cafe using profile's target titles
**When to use:** All sources that use per-title queries
**Example:**
```python
# Source: sources.py lines 1717-1807

def build_search_queries(profile: dict) -> list[dict]:
    """Generate search queries from a candidate profile."""
    queries = []
    titles = profile.get("target_titles", [])[:4]
    location = profile.get("target_market", profile.get("location", ""))

    # ... existing queries for other sources ...

    # hiring.cafe queries: each target title (match pattern of Dice, Adzuna)
    for title in titles:
        hiringcafe_query = {"source": "hiringcafe", "query": title}
        if location:
            hiringcafe_query["location"] = location
        queries.append(hiringcafe_query)

    return queries
```

### Pattern 3: Rate Limiting Configuration
**What:** Add conservative rate limit (60 req/hour per requirements)
**When to use:** All API-based sources
**Example:**
```python
# Source: rate_limits.py lines 55-63

RATE_LIMITS = {
    # ... existing sources ...
    "hiringcafe": [Rate(60, Duration.HOUR)],  # Conservative 60 req/hour
}
```

### Anti-Patterns to Avoid
- **Don't parse salary client-side from description text:** hiring.cafe provides structured salary data, use it
- **Don't implement custom retry logic:** Use existing `fetch_with_retry()` with timeout=15, retries=3
- **Don't add hiring.cafe to JSEARCH_KNOWN_SOURCES:** It's a native source, not an aggregator
- **Don't skip validation in mapper:** Always check title, company, url are present before creating JobResult

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fuzzy deduplication | Custom title matching | `deduplicate_cross_source()` with rapidfuzz | Already handles token_sort_ratio ≥85 threshold, bucketing optimization, multi-source tracking |
| Rate limiting | Manual timestamp tracking | `pyrate-limiter` with SQLiteBucket | Persistent across restarts, handles multiple rate windows (60/hr + 1000/day) |
| Salary parsing | Regex for every format | Structured API fields + normalization helper | hiring.cafe returns structured min/max, just format to "$120K-$160K" |
| HTTP retry | try/except loops | `fetch_with_retry()` | Exponential backoff, timeout handling, caching, already tested |
| Location normalization | String manipulation | `parse_location_to_city_state()` | Handles "City, STATE_ABBR", state name mapping, remote detection |

**Key insight:** Job Radar has mature data pipeline components. Don't rebuild — compose existing functions.

## Common Pitfalls

### Pitfall 1: Assuming Official API Exists
**What goes wrong:** Documentation searches return third-party scrapers, not official endpoints
**Why it happens:** hiring.cafe does not publish official API documentation
**How to avoid:** Use Apify's scraper API ($1/1000 jobs) or implement web scraping with BeautifulSoup
**Warning signs:** 404 errors on api.hiring.cafe endpoints, authentication failures

### Pitfall 2: Salary Format Inconsistency
**What goes wrong:** Mixing "$120k" with "$120,000" in reports breaks sorting and filtering
**Why it happens:** Different sources use different formats, need normalization
**How to avoid:** Always use `_format_salary_range(min, max)` pattern from existing sources
**Warning signs:** Reports show "$120k - $160000" instead of "$120K - $160K"

### Pitfall 3: Over-Requesting Data
**What goes wrong:** Fetching 1000 jobs per query overwhelms reports and violates rate limits
**Why it happens:** API supports up to 1000, but user decision is ~50-100 per query
**How to avoid:** Match existing source volume in query parameters (limit=50 or results_per_page=50)
**Warning signs:** 429 rate limit errors, reports with 500+ hiring.cafe jobs when other sources have 20-50

### Pitfall 4: Silent Dedup Removal of Better Data
**What goes wrong:** Dedup removes hiring.cafe job with salary when duplicate from Dice has "Not listed"
**Why it happens:** Dedup keeps first occurrence, not best occurrence
**How to avoid:** Run hiring.cafe in Phase 1 (scrapers) or Phase 2 (APIs), before aggregators
**Warning signs:** Users complain "I saw a job with salary on hiring.cafe but report shows Not listed"

### Pitfall 5: Blocking on API Failure
**What goes wrong:** hiring.cafe timeout blocks entire search, user sees no results
**Why it happens:** Not following "silent skip" pattern from requirements
**How to avoid:** Return empty list on failure, log debug message only
**Warning signs:** User reports "search hangs" or "no results when hiring.cafe is down"

## Code Examples

Verified patterns from official sources:

### Salary Normalization (Annual Conversion)
```python
# Source: scoring.py lines 123-152 + Industry standard 2080 hours/year

def _normalize_salary_to_annual(value: float, period: str) -> float:
    """Convert salary to annual equivalent.

    Args:
        value: Numeric salary value
        period: One of "hour", "month", "year"

    Returns:
        Annual salary in dollars
    """
    if period == "hour":
        return value * 2080  # 40 hours/week × 52 weeks
    elif period == "month":
        return value * 12
    elif period == "year":
        return value
    else:
        # Heuristic: if < 500, assume hourly; if < 1000, assume thousands
        if value < 500:
            return value * 2080
        elif value < 1000:
            return value * 1000
        return value

def _format_salary_range(salary_min: float | None, salary_max: float | None) -> str:
    """Format salary min/max to standardized range string."""
    if salary_min and salary_max:
        # Use K format for readability: "$120K - $160K"
        return f"${int(salary_min/1000)}K - ${int(salary_max/1000)}K"
    elif salary_min:
        return f"${int(salary_min/1000)}K+"
    else:
        return "Not listed"
```

### Location Filtering (Server-Side + Client-Side)
```python
# Source: User decision — server-side first, then local refinement

def fetch_hiringcafe(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch with location filtering."""
    # Server-side filter (if API supports it)
    params = {"query": query, "limit": 50}
    if location:
        params["location"] = location  # hiring.cafe may support this

    # Fetch results
    results = _fetch_and_parse(params)

    # Client-side refinement for edge cases
    if location:
        results = [r for r in results if _location_matches(r.location, location) or r.arrangement == "remote"]

    # Always include remote jobs (per user decision)
    remote_jobs = [r for r in results if r.arrangement == "remote"]
    local_jobs = [r for r in results if r.arrangement != "remote"]

    return remote_jobs + local_jobs  # Remote first, then local matches

def _location_matches(job_location: str, target_location: str) -> bool:
    """Check if job location matches target (city, state, or abbreviation)."""
    # Similar to existing _locations_match in scoring.py
    job_parts = job_location.lower().replace(",", " ").split()
    target_parts = target_location.lower().replace(",", " ").split()
    return any(part in job_parts for part in target_parts if len(part) > 1)
```

### Graceful Failure Handling
```python
# Source: sources.py lines 690-743 (Adzuna pattern)

def fetch_hiringcafe(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from hiring.cafe."""
    results = []

    # Silent skip on rate limit (no error to user)
    if not check_rate_limit("hiringcafe", verbose=verbose):
        return results

    # Build request
    url = build_hiringcafe_url(query, location)

    # Fetch with retry (timeout=15, retries=3 from existing pattern)
    try:
        body = fetch_with_retry(url, headers=HEADERS, use_cache=True)
        if body is None:
            log.debug("[hiring.cafe] Fetch failed for '%s'", query)
            return results  # Silent skip, other sources continue

        data = json.loads(body)
        items = data.get("jobs", [])

        for item in items:
            try:
                job = map_hiringcafe_to_job_result(item)
                if job:
                    results.append(job)
            except Exception as e:
                # Skip malformed individual job, keep processing others
                log.debug("[hiring.cafe] Skipping malformed job: %s", e)
                continue

    except json.JSONDecodeError as e:
        log.debug("[hiring.cafe] JSON parse error: %s", e)
    except Exception as e:
        log.debug("[hiring.cafe] Request failed: %s", e)

    log.info("[hiring.cafe] Found %d results for '%s'", len(results), query)
    return results  # Return whatever we successfully parsed
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sequential source fetching | Three-phase parallel fetching (scraper → API → aggregator) | Phase 33 (2026-02) | Native sources win in dedup, hiring.cafe should run in Phase 1 or 2 |
| Global rate limits | Per-backend-API shared limits | Phase 31 (2026-02) | JSearch sources share one limiter, hiring.cafe needs dedicated limiter |
| Manual dedup (title + company exact) | Fuzzy cross-source dedup (token_sort_ratio ≥85) | Phase 13 (2026-01) | Catches variations like "Google Inc" vs "Google" |
| String-only salary | Structured min/max + currency fields | Phase 33 (2026-02) | Enables scoring, filtering, sorting by salary |

**Deprecated/outdated:**
- Exact duplicate detection only: Replaced with fuzzy matching (rapidfuzz), catches near-duplicates
- Single-threaded source fetching: Replaced with ThreadPoolExecutor (max_workers=6)
- Fixed timeout values: Now configurable via `fetch_with_retry(timeout=15)`

## Open Questions

1. **Which integration approach to use?**
   - What we know: hiring.cafe has no official public API, Apify offers paid scraper ($1/1000 jobs)
   - What's unclear: Whether direct web scraping is reliable enough, or if we should pay for Apify
   - Recommendation: Start with Apify integration (reliable, structured JSON), fallback to scraping if budget is concern

2. **What are the actual API endpoint URLs?**
   - What we know: GitHub scrapers mention "official API endpoints" but don't document them
   - What's unclear: Does hiring.cafe have undocumented internal API we can use?
   - Recommendation: Inspect hiring.cafe website network traffic to find JSON endpoints, use those if available

3. **How does pagination work?**
   - What we know: API supports "up to 1000 jobs per request", Apify has "smart pagination"
   - What's unclear: Is pagination page-based (page=1,2,3) or offset-based (offset=0,50,100)?
   - Recommendation: Limit first request to 50-100 jobs (per user decision), only paginate if needed

4. **What's the exact response field mapping?**
   - What we know: Apify returns 50+ fields including salary_min, salary_max, location, employment_type
   - What's unclear: Field names from direct API vs Apify scraper
   - Recommendation: Fetch sample response, map to JobResult schema, document in mapper function

5. **Is server-side location filtering supported?**
   - What we know: User decision assumes it might be, with fallback to local filtering
   - What's unclear: Whether API accepts location parameter and how it filters
   - Recommendation: Try location parameter, measure results, apply local refinement if needed

## Sources

### Primary (HIGH confidence)
- Job Radar codebase: `/home/corye/Claude/Job-Radar/job_radar/sources.py` — established patterns for source adapters, mappers, dedup integration
- Job Radar codebase: `/home/corye/Claude/Job-Radar/job_radar/rate_limits.py` — SQLite-backed rate limiting with pyrate-limiter
- Job Radar codebase: `/home/corye/Claude/Job-Radar/job_radar/scoring.py` — salary parsing with `_parse_salary_number()` and comp_floor checking
- Job Radar codebase: `/home/corye/Claude/Job-Radar/job_radar/deduplication.py` — fuzzy dedup with rapidfuzz token_sort_ratio ≥85
- Industry standard: 2080 hours/year calculation (40 hrs/week × 52 weeks) — verified across [Indeed](https://www.indeed.com/hire/hourly-to-salary-calculator-for-employers), [CalculatorSoup](https://www.calculatorsoup.com/calculators/financial/hourly-to-salary-calculator.php), [OmniCalculator](https://www.omnicalculator.com/finance/salary-to-hourly)

### Secondary (MEDIUM confidence)
- [Apify hiring.cafe Scraper API](https://apify.com/memo23/apify-hiring-cafe-scraper/api) — third-party scraper with 50+ fields, $1/1000 jobs pricing
- [Apify hiring.cafe Scraper (up to 10k)](https://apify.com/genz-coder/hiringcafe-jobs-scraper-upto-10k/api) — alternative scraper with higher volume support
- [Automatio.ai hiring.cafe Scraper](https://automatio.ai/templates/en/hiringcafe-web-scraper) — no-code scraper showing available fields (title, location, pay, type, contract, company, description)
- [GitHub hiring.cafe job scraper](https://github.com/umur957/hiring-cafe-job-scraper) — Python scraper mentioning "official API endpoints" (details not verified)

### Tertiary (LOW confidence — needs verification)
- hiring.cafe "official API endpoints" mentioned in GitHub projects — no documentation found, may be internal/undocumented
- Server-side location filtering support — assumed possible in user decisions, not confirmed in available docs
- 1000 jobs per request maximum — mentioned in Apify docs, not verified against actual API limits

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use, proven integration patterns
- Architecture: HIGH — source adapter pattern well-established across 10 existing sources
- Integration approach: MEDIUM — official API not confirmed, relying on third-party scrapers or reverse engineering
- Salary normalization: HIGH — 2080 hours/year standard verified, existing scoring.py has working parser
- Rate limiting: HIGH — pyrate-limiter SQLite backend proven, just need to add hiring.cafe config
- Pitfalls: MEDIUM — based on existing source patterns, but hiring.cafe-specific edge cases unknown

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (30 days — stable codebase, but hiring.cafe API may change)
