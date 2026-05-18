"""Job source fetchers and URL generators."""

import json as _json
import logging
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from bs4 import BeautifulSoup

from .cache import fetch_with_retry, get_cache_stats, reset_cache_stats
from .api_config import get_api_key
from .rate_limits import check_rate_limit
from .deduplication import deduplicate_cross_source
from .manual_sources import (
    MANUAL_SOURCE_REGISTRY,
    _slugify_for_wellfound,
    generate_glassdoor_url,
    generate_indeed_url,
    generate_linkedin_url,
    generate_manual_urls,
    generate_weworkremotely_url,
    generate_wellfound_url,
    get_manual_source_display_names,
)
from .source_config import (
    resolve_max_workers,
    resolve_slow_query_threshold,
    source_cache_ttl,
)
from .source_execution import SourceExecutionState
from .source_mappers import (
    map_adzuna_to_job_result,
    map_authenticjobs_to_job_result,
    map_jsearch_to_job_result,
)
from .source_models import JobResult
from .source_parsing import (
    _DATE_RE,
    _EMPLOYMENT_TYPE_RE,
    _MAX_COMPANY,
    _MAX_LOCATION,
    _MAX_TITLE,
    _SALARY_RE,
    _SKIP_TOKENS,
    _clean_field,
    _parse_arrangement,
    _strip_html,
    parse_location_to_city_state,
    strip_html_and_normalize,
)
from .source_queries import build_search_queries
from .source_registry import (
    SourceDefinition,
    selected_automated_source_display_names,
    source_queries_by_phase,
    source_display_name,
)

log = logging.getLogger(__name__)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ---------------------------------------------------------------------------
# Dice.com fetcher (improved field detection)
# ---------------------------------------------------------------------------


def fetch_dice(query: str, location: str = "") -> list[JobResult]:
    """Fetch job listings from Dice.com by scraping search results."""
    results = []
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://www.dice.com/jobs?q={encoded_q}"
    if location:
        url += f"&location={urllib.parse.quote_plus(location)}"

    body = fetch_with_retry(url, headers=HEADERS, cache_ttl_seconds=source_cache_ttl("dice"))
    if body is None:
        log.warning("[Dice] Fetch failed for '%s'", query)
        return results

    try:
        soup = BeautifulSoup(body, "html.parser")
        cards = soup.select("div.rounded-lg.border")

        for card in cards:
            detail_link = card.select_one('a[href*="/job-detail/"]')
            if not detail_link:
                continue

            detail_url = detail_link.get("href", "")
            if detail_url and not detail_url.startswith("http"):
                detail_url = "https://www.dice.com" + detail_url

            parts = [
                p.strip()
                for p in card.get_text(separator="|||", strip=True).split("|||")
                if p.strip()
            ]

            # Filter out noise tokens
            meaningful = [p for p in parts if p not in _SKIP_TOKENS]

            # Use heuristic field detection instead of fixed positions
            company = "Unknown"
            title = "Unknown Title"
            loc = location or "Unknown"
            posted = "Unknown"
            salary = "Not listed"
            emp_type = ""
            desc_parts = []
            confidence = "high"

            # First meaningful part is usually company
            if meaningful:
                company = _clean_field(meaningful[0], _MAX_COMPANY)

            # Second is usually title (often matches the detail link text)
            if len(meaningful) > 1:
                title = _clean_field(meaningful[1], _MAX_TITLE)

            # Scan remaining parts for typed fields
            for part in meaningful[2:]:
                if _SALARY_RE.search(part) and salary == "Not listed":
                    salary = part.strip()
                elif _DATE_RE.match(part.strip()) and posted == "Unknown":
                    posted = part.strip()
                elif _EMPLOYMENT_TYPE_RE.match(part.strip()):
                    emp_type = part.strip()
                elif loc in (location or "Unknown", "Unknown") and (
                    "," in part or "remote" in part.lower()
                ) and len(part) < 60:
                    loc = _clean_field(part, _MAX_LOCATION)
                else:
                    desc_parts.append(part)

            arrangement = _parse_arrangement(f"{loc} {title}")
            description = " ".join(desc_parts[:3])  # first 3 descriptive chunks

            results.append(JobResult(
                title=title,
                company=company,
                location=loc,
                arrangement=arrangement,
                salary=salary,
                date_posted=posted,
                description=description,
                url=detail_url,
                source="Dice",
                employment_type=emp_type,
                parse_confidence=confidence,
            ))
    except Exception as e:
        log.error("[Dice] Parse error: %s", e)

    log.info("[Dice] Found %d results for '%s'", len(results), query)
    return results


# ---------------------------------------------------------------------------
# HN Hiring (hnhiring.com) fetcher (improved parsing)
# ---------------------------------------------------------------------------

def fetch_hn_hiring(technology: str) -> list[JobResult]:
    """Fetch job listings from hnhiring.com by technology tag."""
    results = []
    url = f"https://hnhiring.com/technologies/{urllib.parse.quote_plus(technology.lower())}"

    body = fetch_with_retry(url, headers=HEADERS, cache_ttl_seconds=source_cache_ttl("hn_hiring"))
    if body is None:
        log.warning("[HN Hiring] Fetch failed for '%s'", technology)
        return results

    try:
        soup = BeautifulSoup(body, "html.parser")

        jobs_ul = soup.select_one("ul.jobs")
        if not jobs_ul:
            log.info("[HN Hiring] No ul.jobs found on page")
            return results

        items = jobs_ul.select("li.job")
        for item in items:
            # Extract date from the user info span
            date_span = item.select_one("span.type-info, span.gray")
            date_posted = date_span.get_text(strip=True) if date_span else "Unknown"

            # Extract the body div
            body_div = item.select_one("div.body")
            if not body_div:
                continue

            # Get the header line (text before the first <p> tag)
            header_text = ""
            for child in body_div.children:
                if hasattr(child, "name") and child.name == "p":
                    break
                if isinstance(child, str):
                    header_text += child
                elif hasattr(child, "get_text"):
                    header_text += child.get_text()
            header_text = header_text.strip()

            # Parse pipe-separated fields
            parts = [p.strip() for p in header_text.split("|")]
            confidence = "high"

            # Validate parsing quality — if first part is too long,
            # the post doesn't follow the standard format
            if len(parts) < 2 or len(parts[0]) > _MAX_COMPANY:
                # Freeform text — try to extract what we can
                confidence = "low"
                company, title, location = _parse_freeform_hn(header_text)
            else:
                company = _clean_field(parts[0], _MAX_COMPANY)

                if len(parts) >= 2:
                    title = _clean_field(parts[1], _MAX_TITLE)
                else:
                    title = _extract_title_from_text(header_text)
                    confidence = "medium"

                if len(parts) >= 3:
                    location = _clean_field(parts[2], _MAX_LOCATION)
                else:
                    location = _extract_location_from_text(header_text)
                    confidence = "medium" if confidence == "high" else confidence

            # Remaining parts may contain type, salary, etc.
            extra = " | ".join(parts[3:]) if len(parts) > 3 else ""

            arrangement = _parse_arrangement(f"{location} {extra} {header_text}")
            salary = _extract_salary_from_text(f"{extra} {header_text}")
            emp_type = _extract_employment_type(f"{extra} {header_text}")

            # Full description from all <p> tags
            desc_parts = [p.get_text(strip=True) for p in body_div.select("p")]
            description = " ".join(desc_parts)[:500]

            # Find apply link or email
            apply_info = _extract_apply_info(body_div, description)

            results.append(JobResult(
                title=title,
                company=company,
                location=location,
                arrangement=arrangement,
                salary=salary,
                date_posted=date_posted,
                description=description,
                url=apply_info if apply_info.startswith("http") else url,
                source="HN Hiring",
                apply_info=apply_info,
                employment_type=emp_type,
                parse_confidence=confidence,
            ))
    except Exception as e:
        log.error("[HN Hiring] Parse error for '%s': %s", technology, e)

    log.info("[HN Hiring] Found %d results for '%s'", len(results), technology)
    return results


def _parse_freeform_hn(text: str) -> tuple[str, str, str]:
    """Parse a freeform (non-pipe-separated) HN Hiring header.

    Returns (company, title, location).
    """
    company = _extract_company_from_text(text)
    title = _extract_title_from_text(text)
    location = _extract_location_from_text(text)
    return (
        _clean_field(company, _MAX_COMPANY),
        _clean_field(title, _MAX_TITLE),
        _clean_field(location, _MAX_LOCATION),
    )


def _extract_company_from_text(text: str) -> str:
    """Try to extract a company name from freeform text."""
    # Pattern: "Company is hiring" or "Company -"
    patterns = [
        r'^([A-Z][\w\s\.]+?)(?:\s+is\s+hiring|\s+[-–]\s)',
        r'^([A-Z][\w\s\.]{2,30}?)(?:\s*\|)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    # Fallback: first sentence-like chunk
    first = text.split(".")[0].split(",")[0].split("(")[0].strip()
    return first[:_MAX_COMPANY] if first else "Unknown"


def _extract_apply_info(body_div, description: str) -> str:
    """Extract apply link or email from an HN Hiring body div."""
    apply_info = ""
    for link in body_div.select("a[href]"):
        href = link.get("href", "")
        if "news.ycombinator.com/user" in href:
            continue
        if any(kw in href for kw in [
            "mailto:", "careers", "jobs", "apply", "lever.co",
            "greenhouse", "ashby", "applytojob",
        ]):
            apply_info = href
            break
    if not apply_info:
        for link in body_div.select("a[href]"):
            href = link.get("href", "")
            if "news.ycombinator.com" not in href and href.startswith("http"):
                apply_info = href
                break
    if not apply_info:
        email_match = re.search(r'[\w.+-]+@[\w.-]+\.\w+', description)
        if email_match:
            apply_info = f"mailto:{email_match.group()}"
    return apply_info


def _extract_title_from_text(text: str) -> str:
    """Try to extract a job title from freeform text."""
    title_patterns = [
        r'(?:hiring|looking for|seeking)\s+(?:a\s+)?(.+?)(?:\.|,|\||\n|$)',
        r'((?:Senior|Junior|Staff|Lead|Principal)?\s*(?:Software|Full[ -]?Stack|Frontend|Backend|Web|Product|DevOps|Data|ML|QA|Business)\s+(?:Engineer|Developer|Analyst|Owner|Architect|Manager))',
        r'((?:Sr\.?|Jr\.?)\s+\w+\s+(?:Engineer|Developer|Analyst|Consultant))',
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:_MAX_TITLE]
    first_line = text.split("\n")[0].split("|")[0].strip()
    return first_line[:_MAX_TITLE] if first_line else "Unknown Title"


def _extract_location_from_text(text: str) -> str:
    """Try to extract location from freeform text."""
    loc_patterns = [
        r'(?:location|based in|located in|office in)[:\s]+([A-Z][a-z]+(?:[\s,]+[A-Z]{2})?)',
        r'([A-Z][a-z]+,\s*[A-Z]{2})\b',
        r'\b(REMOTE(?:\s*[\(/]\s*\w+[\s\w]*[\)/])?)\b',
        r'\b(Remote(?:\s*\/\s*\w+)?)\b',
    ]
    for pattern in loc_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return "Unknown"


def _extract_employment_type(text: str) -> str:
    """Try to extract employment type from text."""
    lower = text.lower()
    if "contract to hire" in lower or "c2h" in lower or "contract-to-hire" in lower:
        return "C2H"
    if re.search(r'\bcontract\b', lower):
        return "Contract"
    if re.search(r'\bpart[ -]?time\b', lower):
        return "Part-time"
    if re.search(r'\bfull[ -]?time\b', lower):
        return "Full-time"
    if re.search(r'\bfreelance\b', lower):
        return "Contract"
    if re.search(r'\btemp\b', lower):
        return "Contract"
    return ""


def _extract_salary_from_text(text: str) -> str:
    """Try to extract salary/rate information from text."""
    patterns = [
        r'(\$[\d,]+(?:k|K)?(?:\s*[-–]\s*\$[\d,]+(?:k|K)?)?(?:\s*/?\s*(?:yr|year|hr|hour|annually))?)',
        r'([\d,]+(?:k|K)\s*[-–]\s*[\d,]+(?:k|K))',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return "Not listed"


# ---------------------------------------------------------------------------
# RemoteOK fetcher (JSON API)
# ---------------------------------------------------------------------------

def fetch_remoteok(query: str) -> list[JobResult]:
    """Fetch remote job listings from RemoteOK's JSON API."""
    results = []
    url = "https://remoteok.com/api"

    body = fetch_with_retry(
        url,
        headers={**HEADERS, "Accept": "application/json"},
        use_cache=True,
        cache_ttl_seconds=source_cache_ttl("remoteok"),
    )
    if body is None:
        log.warning("[RemoteOK] Fetch failed")
        return results

    try:
        data = _json.loads(body)
        query_lower = query.lower()
        # Only keep significant words (3+ chars) for multi-word matching
        query_words = [w for w in query_lower.split() if len(w) >= 3]

        for item in data:
            if not isinstance(item, dict) or "id" not in item:
                continue  # skip the legal notice entry

            # Match by tags or position title
            tags = [t.lower() for t in item.get("tags", [])]
            position = item.get("position", "").lower()
            desc = item.get("description", "").lower()
            tags_text = " ".join(tags)

            # Full phrase match in title or tags (best signal)
            if query_lower in position or query_lower in tags_text:
                pass  # strong match, proceed
            elif len(query_words) >= 2:
                # Multi-word query: require ALL significant words present
                # in either the title+tags, or title+description
                title_tags = position + " " + tags_text
                if not all(w in title_tags or w in desc for w in query_words):
                    continue
            else:
                # Single-word query: require match in title or tags (not just description)
                if not any(w in position or w in tags_text for w in query_words):
                    continue

            salary_min = item.get("salary_min", "")
            salary_max = item.get("salary_max", "")
            salary = "Not listed"
            if salary_min and salary_max:
                salary = f"${salary_min:,} - ${salary_max:,}" if isinstance(salary_min, int) else f"${salary_min} - ${salary_max}"
            elif salary_min:
                salary = f"${salary_min}+"

            location_text = item.get("location", "Remote")
            if not location_text or location_text.strip() == "":
                location_text = "Remote"

            apply_url = item.get("apply_url", item.get("url", ""))
            detail_url = item.get("url", "")
            if detail_url and not detail_url.startswith("http"):
                detail_url = f"https://remoteok.com{detail_url}"

            results.append(JobResult(
                title=_clean_field(item.get("position", "Unknown Title"), _MAX_TITLE),
                company=_clean_field(item.get("company", "Unknown"), _MAX_COMPANY),
                location=_clean_field(location_text, _MAX_LOCATION),
                arrangement="remote",
                salary=salary,
                date_posted=item.get("date", "Unknown")[:10],
                description=_strip_html(item.get("description", ""))[:500],
                url=detail_url,
                source="RemoteOK",
                apply_info=apply_url or "",
                employment_type=item.get("job_type", ""),
            ))
    except Exception as e:
        log.error("[RemoteOK] Parse error: %s", e)

    log.info("[RemoteOK] Found %d results matching '%s'", len(results), query)
    return results


# ---------------------------------------------------------------------------
# We Work Remotely fetcher
# ---------------------------------------------------------------------------

# Map source identifiers to display names for progress messages
_SOURCE_DISPLAY_NAMES = {
    "dice": "Dice",
    "hn_hiring": "HN Hiring",
    "remoteok": "RemoteOK",
    "weworkremotely": "We Work Remotely",
    "adzuna": "Adzuna",
    "authentic_jobs": "Authentic Jobs",
    "linkedin": "LinkedIn",
    "indeed": "Indeed",
    "glassdoor": "Glassdoor",
    "jsearch": "JSearch",
    "jsearch_other": "JSearch (Other)",
    "usajobs": "USAJobs (Federal)",
    "serpapi": "SerpAPI (Google Jobs)",
    "jobicy": "Jobicy (Remote)",
    "hiringcafe": "hiring.cafe",
}


def fetch_weworkremotely(query: str) -> list[JobResult]:
    """Fetch remote job listings from We Work Remotely.

    Note: WWR uses Cloudflare protection which blocks automated access.
    This fetcher detects the block and returns empty results gracefully.
    WWR is included in manual-check URLs as an alternative.
    """
    results = []
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://weworkremotely.com/remote-jobs/search?term={encoded_q}"

    body = fetch_with_retry(
        url,
        headers=HEADERS,
        retries=1,
        cache_ttl_seconds=source_cache_ttl("weworkremotely"),
    )
    if body is None:
        log.info("[WWR] Fetch failed for '%s' — check manual URLs", query)
        return results

    # Detect Cloudflare challenge page
    if "Just a moment" in body[:500] or "cf-browser-verification" in body[:2000]:
        log.info("[WWR] Cloudflare protection detected — use manual URL instead")
        return results

    try:
        soup = BeautifulSoup(body, "html.parser")

        # WWR listing structure: <section class="jobs"> > <article> or <li>
        listings = soup.select("section.jobs li, section.jobs article")
        if not listings:
            # Fallback: try broader selectors
            listings = soup.select("li.feature, li.new, article.job")

        for li in listings:
            link = li.select_one("a[href*='/remote-jobs/'], a[href*='/listings/']")
            if not link:
                continue

            href = link.get("href", "")
            if not href.startswith("http"):
                href = f"https://weworkremotely.com{href}"

            # Try multiple selector patterns for company/title/region
            company_el = (
                li.select_one(".company")
                or li.select_one("[class*='company']")
                or li.select_one("span.companyName")
            )
            title_el = (
                li.select_one(".title")
                or li.select_one("[class*='title']")
                or li.select_one("span.listing-title")
            )
            region_el = (
                li.select_one(".region")
                or li.select_one("[class*='region']")
                or li.select_one(".location")
            )

            company = company_el.get_text(strip=True) if company_el else "Unknown"
            title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True) or "Unknown Title"
            region = region_el.get_text(strip=True) if region_el else "Remote"

            # Skip if we couldn't extract a meaningful title
            if title in ("Unknown Title", ""):
                continue

            results.append(JobResult(
                title=_clean_field(title, _MAX_TITLE),
                company=_clean_field(company, _MAX_COMPANY),
                location=_clean_field(region, _MAX_LOCATION),
                arrangement="remote",
                salary="Not listed",
                date_posted="Recent",
                description="",
                url=href,
                source="WWR",
                apply_info=href,
            ))
    except Exception as e:
        log.error("[WWR] Parse error: %s", e)

    log.info("[WWR] Found %d results for '%s'", len(results), query)
    return results


# ---------------------------------------------------------------------------
# Adzuna API fetcher
# ---------------------------------------------------------------------------

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

    # Build API URL
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
        body = fetch_with_retry(
            url,
            headers=HEADERS,
            use_cache=True,
            cache_ttl_seconds=source_cache_ttl("adzuna"),
        )
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
        # Check for HTTPError-like exceptions
        error_str = str(e).lower()
        if "401" in error_str or "403" in error_str or "unauthorized" in error_str:
            log.error("[Adzuna] Authentication failed - run 'job-radar --setup-apis' to reconfigure")
        else:
            log.debug("[Adzuna] Request failed: %s", e)

    log.info("[Adzuna] Found %d results for '%s'", len(results), query)
    return results


# ---------------------------------------------------------------------------
# Authentic Jobs API fetcher
# ---------------------------------------------------------------------------

def fetch_authenticjobs(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from Authentic Jobs API."""
    results = []

    # Check credentials
    api_key = get_api_key("AUTHENTIC_JOBS_API_KEY", "Authentic Jobs")
    if not api_key:
        return results

    # Check rate limit
    if not check_rate_limit("authentic_jobs", verbose=verbose):
        return results

    # Build API URL
    params = {
        "api_key": api_key,
        "method": "aj.jobs.search",
        "format": "json",
        "keywords": query,
        "perpage": "50",
    }
    if location:
        params["location"] = location

    url = "https://authenticjobs.com/api/?" + urllib.parse.urlencode(params)

    # Fetch with retry
    try:
        body = fetch_with_retry(
            url,
            headers=HEADERS,
            use_cache=True,
            cache_ttl_seconds=source_cache_ttl("authentic_jobs"),
        )
        if body is None:
            log.debug("[Authentic Jobs] Fetch failed for '%s'", query)
            return results

        data = _json.loads(body)

        # Handle response structure - may have listings.listing as array or single dict
        listings = data.get("listings", {}).get("listing", [])
        if isinstance(listings, dict):
            listings = [listings]
        elif not isinstance(listings, list):
            listings = []

        for item in listings:
            job = map_authenticjobs_to_job_result(item)
            if job:
                results.append(job)

    except _json.JSONDecodeError as e:
        log.debug("[Authentic Jobs] JSON parse error: %s", e)
    except Exception as e:
        # Check for HTTPError-like exceptions
        error_str = str(e).lower()
        if "401" in error_str or "403" in error_str or "unauthorized" in error_str:
            log.error("[Authentic Jobs] Authentication failed - run 'job-radar --setup-apis' to reconfigure")
        else:
            log.debug("[Authentic Jobs] Request failed: %s", e)

    log.info("[Authentic Jobs] Found %d results for '%s'", len(results), query)
    return results


# ---------------------------------------------------------------------------
# JSearch API fetcher (LinkedIn, Indeed, Glassdoor aggregator)
# ---------------------------------------------------------------------------

def fetch_jsearch(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from JSearch API (aggregates LinkedIn, Indeed, Glassdoor)."""
    results = []

    # Check credentials
    api_key = get_api_key("JSEARCH_API_KEY", "JSearch")
    if not api_key:
        return results

    # Check rate limit (uses "jsearch" backend shared across linkedin/indeed/glassdoor)
    if not check_rate_limit("jsearch", verbose=verbose):
        return results

    # Build API URL
    headers = {
        **HEADERS,
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {
        "query": query,
        "page": "1",
        "num_pages": "1",
        "date_posted": "week",
    }
    if location:
        params["location"] = location

    url = "https://jsearch.p.rapidapi.com/search?" + urllib.parse.urlencode(params)

    # Fetch with retry
    try:
        body = fetch_with_retry(
            url,
            headers=headers,
            use_cache=True,
            cache_ttl_seconds=source_cache_ttl("jsearch"),
        )
        if body is None:
            log.debug("[JSearch] Fetch failed for '%s'", query)
            return results

        data = _json.loads(body)
        items = data.get("data", [])

        for item in items:
            job = map_jsearch_to_job_result(item)
            if job:
                results.append(job)

    except _json.JSONDecodeError as e:
        log.debug("[JSearch] JSON parse error: %s", e)
    except Exception as e:
        # Check for HTTPError-like exceptions
        error_str = str(e).lower()
        if "401" in error_str or "403" in error_str or "unauthorized" in error_str:
            log.error("[JSearch] Authentication failed - run 'job-radar --setup-apis' to reconfigure")
        else:
            log.debug("[JSearch] Request failed: %s", e)

    log.info("[JSearch] Found %d results for '%s'", len(results), query)
    return results


# ---------------------------------------------------------------------------
# USAJobs API fetcher (Federal government jobs)
# ---------------------------------------------------------------------------

def fetch_usajobs(query: str, location: str = "", profile: dict = None, verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from USAJobs federal government API."""
    results = []

    # Check credentials (both API key and email required)
    api_key = get_api_key("USAJOBS_API_KEY", "USAJobs")
    email = get_api_key("USAJOBS_EMAIL", "USAJobs")
    if not api_key or not email:
        return results

    # Check rate limit
    if not check_rate_limit("usajobs", verbose=verbose):
        return results

    # Build request with required headers
    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": email,  # REQUIRED: must contain email from API registration
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
            params["PayGradeLow"] = f"{gs_min:02d}"  # Format as 2-digit string
        if gs_max:
            params["PayGradeHigh"] = f"{gs_max:02d}"

        agencies = profile.get("preferred_agencies", [])
        if agencies:
            # Semicolon-delimited agency codes
            params["Organization"] = ";".join(agencies)

        # Security clearance not available as API parameter (per research)

    url = "https://data.usajobs.gov/api/search?" + urllib.parse.urlencode(params)

    # Fetch with retry
    try:
        body = fetch_with_retry(
            url,
            headers=headers,
            use_cache=True,
            cache_ttl_seconds=source_cache_ttl("usajobs"),
        )
        if body is None:
            log.debug("[USAJobs] Fetch failed for '%s'", query)
            return results

        data = _json.loads(body)
        # USAJobs uses nested structure
        search_result = data.get("SearchResult", {})
        items = search_result.get("SearchResultItems", [])

        for item in items:
            job = map_usajobs_to_job_result(item)
            if job:
                results.append(job)

    except _json.JSONDecodeError as e:
        log.debug("[USAJobs] JSON parse error: %s", e)
    except Exception as e:
        # Check for HTTPError-like exceptions
        error_str = str(e).lower()
        if "401" in error_str or "403" in error_str or "unauthorized" in error_str:
            log.error("[USAJobs] Authentication failed - run 'job-radar --setup-apis' to reconfigure")
        else:
            log.debug("[USAJobs] Request failed: %s", e)

    log.info("[USAJobs] Found %d results for '%s'", len(results), query)
    return results


def map_usajobs_to_job_result(item: dict) -> JobResult | None:
    """Map USAJobs API response item to JobResult.

    Handles nested MatchedObjectDescriptor structure.
    """
    # USAJobs uses nested MatchedObjectDescriptor
    descriptor = item.get("MatchedObjectDescriptor", {})

    # Extract and validate required fields
    title = descriptor.get("PositionTitle", "").strip()
    company = descriptor.get("OrganizationName", "").strip()
    url = descriptor.get("PositionURI", "").strip()

    if not title or not company or not url:
        log.debug("[USAJobs] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                 bool(title), bool(company), bool(url))
        return None

    # Location normalization
    location = descriptor.get("PositionLocationDisplay", "")
    if not location:
        # Fallback to first item in PositionLocation array
        locations = descriptor.get("PositionLocation", [])
        if locations and isinstance(locations, list):
            loc_obj = locations[0]
            city = loc_obj.get("LocationName", "")
            state = loc_obj.get("CountrySubDivisionCode", "")
            location = f"{city}, {state}" if city and state else (city or "Unknown")

    # Salary fields (PositionRemuneration array)
    salary = "Not specified"
    salary_min = None
    salary_max = None
    remuneration = descriptor.get("PositionRemuneration", [])
    if remuneration and isinstance(remuneration, list):
        rem = remuneration[0]
        min_range = rem.get("MinimumRange")
        max_range = rem.get("MaximumRange")
        if min_range and max_range:
            try:
                salary_min = float(min_range)
                salary_max = float(max_range)
                salary = f"${salary_min:,.0f} - ${salary_max:,.0f}"
            except (ValueError, TypeError):
                pass

    # Description cleaning
    user_area = descriptor.get("UserArea", {})
    details = user_area.get("Details", {}) if isinstance(user_area, dict) else {}
    description_raw = details.get("JobSummary", "") if isinstance(details, dict) else ""
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    # Date posted (extract YYYY-MM-DD)
    date_posted = descriptor.get("PublicationStartDate", "")
    if len(date_posted) >= 10:
        date_posted = date_posted[:10]

    # Arrangement detection
    arrangement = _parse_arrangement(f"{title} {description}")

    # Employment type (PositionSchedule array)
    emp_type = ""
    schedules = descriptor.get("PositionSchedule", [])
    if schedules and isinstance(schedules, list) and len(schedules) > 0:
        emp_type = schedules[0].get("Name", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="usajobs",
        employment_type=emp_type,
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="USD" if salary_min or salary_max else None,
    )


# ---------------------------------------------------------------------------
# SerpAPI Google Jobs fetcher
# ---------------------------------------------------------------------------

def map_serpapi_to_job_result(item: dict) -> JobResult | None:
    """Map SerpAPI Google Jobs response item to JobResult.

    Validates required fields (title, company_name, apply link) and returns
    None if any are missing. Uses detected_extensions for work arrangement
    and employment type.
    """
    title = item.get("title", "").strip()
    company = item.get("company_name", "").strip()

    # URL from apply_options (first link) or fall back to share_link
    apply_options = item.get("apply_options", [])
    url = ""
    if apply_options and isinstance(apply_options, list):
        url = apply_options[0].get("link", "").strip()
    if not url:
        url = item.get("share_link", "").strip()

    if not title or not company or not url:
        log.debug("[SerpAPI] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                 bool(title), bool(company), bool(url))
        return None

    # Location
    location_raw = item.get("location", "")
    location = parse_location_to_city_state(location_raw)

    # Work arrangement from detected_extensions
    extensions = item.get("detected_extensions", {})
    if extensions.get("work_from_home"):
        arrangement = "remote"
    else:
        arrangement = _parse_arrangement(f"{title} {item.get('description', '')}")

    # Description
    description_raw = item.get("description", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    # Employment type
    emp_type = extensions.get("schedule_type", "")

    # Salary (SerpAPI rarely includes salary)
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


def map_jobicy_to_job_result(item: dict) -> JobResult | None:
    """Map Jobicy API response item to JobResult.

    Validates required fields (jobTitle, companyName, url). Cleans HTML
    from jobDescription using strip_html_and_normalize(). Jobicy jobs are
    always remote by definition.
    """
    title = item.get("jobTitle", "").strip()
    company = item.get("companyName", "").strip()
    url = item.get("url", "").strip()

    if not title or not company or not url:
        log.debug("[Jobicy] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                 bool(title), bool(company), bool(url))
        return None

    # Location (Jobicy's jobGeo is region, not city/state)
    location_raw = item.get("jobGeo", "")
    location = location_raw if location_raw else "Remote"

    # All Jobicy jobs are remote by definition
    arrangement = "remote"

    # Description: HTML content, must be cleaned
    description_raw = item.get("jobDescription", "")
    if not description_raw:
        description_raw = item.get("jobExcerpt", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    # Skip jobs with empty description after cleaning (required for scoring)
    if not description:
        log.debug("[Jobicy] Skipping job with empty description: %s at %s", title, company)
        return None

    # Employment type
    emp_type = item.get("jobType", "")

    # Salary
    salary_min_str = item.get("annualSalaryMin", "")
    salary_max_str = item.get("annualSalaryMax", "")
    salary_currency = item.get("salaryCurrency", "USD")
    salary_min = None
    salary_max = None

    if salary_min_str and salary_max_str:
        try:
            salary_min = float(salary_min_str)
            salary_max = float(salary_max_str)
            salary = f"{salary_currency} {int(salary_min):,}-{int(salary_max):,}/yr"
        except (ValueError, TypeError):
            salary = "Not specified"
    elif salary_min_str:
        try:
            salary_min = float(salary_min_str)
            salary = f"{salary_currency} {int(salary_min):,}+/yr"
        except (ValueError, TypeError):
            salary = "Not specified"
    else:
        salary = "Not specified"

    # Date posted
    date_posted = item.get("pubDate", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="jobicy",
        employment_type=emp_type,
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
    )


# ---------------------------------------------------------------------------
# hiring.cafe helpers and mapper
# ---------------------------------------------------------------------------

def _normalize_salary_to_annual(value: float, period: str) -> float:
    """Convert salary to annual equivalent."""
    period_lower = period.lower()
    if period_lower in ("hour", "hourly"):
        return value * 2080  # 40 hrs/week x 52 weeks
    elif period_lower in ("month", "monthly"):
        return value * 12
    elif period_lower in ("year", "yearly", "annual", "annually"):
        return value
    else:
        # Heuristic: if < 500, likely hourly; if < 20000, likely monthly
        if value < 500:
            return value * 2080
        elif value < 20000:
            return value * 12
        return value


def _format_hiringcafe_salary(salary_min: float | None, salary_max: float | None) -> str:
    """Format salary to standardized $XXXK range per user decision."""
    if salary_min and salary_max:
        return f"${int(salary_min / 1000)}K - ${int(salary_max / 1000)}K"
    elif salary_min:
        return f"${int(salary_min / 1000)}K+"
    return "Not listed"


def map_hiringcafe_to_job_result(item: dict) -> JobResult | None:
    """Map hiring.cafe response item to JobResult.

    Validates required fields (title, company, url) and returns None if
    any are missing. Normalizes salary to annual range format. Skips
    malformed entries gracefully per user decision.
    """
    title = item.get("title", "").strip()
    company = item.get("company", "").strip()
    url = item.get("url", "").strip()

    if not title or not company or not url:
        log.debug("[hiring.cafe] Skipping job with missing required fields: "
                  "title=%s, company=%s, url=%s",
                  bool(title), bool(company), bool(url))
        return None

    # Salary normalization: convert to annual if period specified
    salary_min_raw = item.get("salary_min")
    salary_max_raw = item.get("salary_max")
    salary_period = item.get("salary_period", "yearly")

    salary_min = None
    salary_max = None
    if salary_min_raw is not None:
        try:
            salary_min = _normalize_salary_to_annual(float(salary_min_raw), salary_period)
        except (ValueError, TypeError):
            pass
    if salary_max_raw is not None:
        try:
            salary_max = _normalize_salary_to_annual(float(salary_max_raw), salary_period)
        except (ValueError, TypeError):
            pass

    salary = _format_hiringcafe_salary(salary_min, salary_max)

    # Location normalization
    location_raw = item.get("location", "")
    location = parse_location_to_city_state(location_raw)

    # Description cleaning
    description_raw = item.get("description", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    # Arrangement detection
    arrangement = _parse_arrangement(f"{title} {description} {location}")

    # Employment type
    emp_type = item.get("employment_type", "")

    # Date posted
    date_posted = item.get("date_posted", "")

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
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="USD" if salary_min or salary_max else None,
    )


# hiring.cafe fetcher configuration constants
_HIRINGCAFE_API_URL = "https://hiring.cafe/api/jobs/search"  # Discovered endpoint
_HIRINGCAFE_PER_QUERY_LIMIT = 50  # Per user decision (overrides phase goal max of 1000)


def fetch_hiringcafe(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from hiring.cafe.

    hiring.cafe is an AI-powered job search platform with remote-focused positions
    and transparent salary information. Uses discovered internal API endpoint.

    Args:
        query: Job title search query
        location: Optional location filter (remote jobs always included)
        verbose: Enable verbose logging

    Returns:
        List of JobResult objects, empty list on failure (silent skip)
    """
    results = []

    # Check rate limit (60 req/hour)
    if not check_rate_limit("hiringcafe", verbose=verbose):
        return results

    # Build request URL with query parameters
    params = {
        "q": query,
        "limit": _HIRINGCAFE_PER_QUERY_LIMIT,
    }
    if location:
        params["location"] = location

    url = _HIRINGCAFE_API_URL + "?" + urllib.parse.urlencode(params)

    # Fetch with retry (retries=1 per user decision "No retry -- fail fast")
    try:
        body = fetch_with_retry(
            url,
            headers=HEADERS,
            use_cache=True,
            retries=1,
            cache_ttl_seconds=source_cache_ttl("hiringcafe"),
        )
        if body is None:
            log.debug("[hiring.cafe] Fetch failed for '%s'", query)
            return results

        # Try parsing as JSON first (API endpoint)
        try:
            data = _json.loads(body)
            items = data.get("jobs", []) or data.get("data", []) or data.get("results", [])
        except _json.JSONDecodeError:
            # If JSON parsing fails, might be HTML - try BeautifulSoup fallback
            log.debug("[hiring.cafe] Response is not JSON, attempting HTML parsing")
            soup = BeautifulSoup(body, "html.parser")
            # NOTE: HTML parsing pattern would go here if needed
            # For now, return empty list since we expect JSON
            return results

        # Parse each item with individual error handling
        for item in items:
            try:
                job = map_hiringcafe_to_job_result(item)
                if job:
                    # Location filtering: include if location matches OR arrangement is remote
                    if location:
                        # Remote jobs always included regardless of location preference
                        if job.arrangement == "remote":
                            results.append(job)
                        # Local jobs: check if location matches target
                        elif _location_matches(job.location, location):
                            results.append(job)
                    else:
                        # No location filter: include all
                        results.append(job)
            except Exception as e:
                # Skip malformed individual job, keep processing others
                log.debug("[hiring.cafe] Skipping malformed job: %s", e)
                continue

    except Exception as e:
        # Silent skip on any failure (per user decision)
        log.debug("[hiring.cafe] Request failed: %s", e)

    log.info("[hiring.cafe] Found %d results for '%s'", len(results), query)
    return results


def _location_matches(job_location: str, target_location: str) -> bool:
    """Check if job location matches target (city, state, or abbreviation).

    Args:
        job_location: Job location string (e.g., "San Francisco, CA")
        target_location: Target location string (e.g., "California" or "CA")

    Returns:
        True if locations match, False otherwise
    """
    if not job_location or not target_location:
        return False

    job_parts = job_location.lower().replace(",", " ").split()
    target_parts = target_location.lower().replace(",", " ").split()

    # Check if any target part appears in job location
    return any(part in job_parts for part in target_parts if len(part) > 1)


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
        body = fetch_with_retry(
            url,
            headers=HEADERS,
            use_cache=True,
            cache_ttl_seconds=source_cache_ttl("serpapi"),
        )
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


def fetch_jobicy(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch remote job listings from Jobicy API.

    Jobicy is a public API (no key required) but rate limited to 1 request/hour.
    Returns remote-focused job listings with HTML descriptions cleaned.
    """
    results = []

    # Check rate limit (no API key needed, but strict rate limit)
    if not check_rate_limit("jobicy", verbose=verbose):
        return results

    # Build API URL
    params = {"count": "20"}

    # Map location to Jobicy geo filter if applicable
    if location:
        location_lower = location.lower()
        if any(term in location_lower for term in ["usa", "united states", "us"]):
            params["geo"] = "usa"
        elif any(term in location_lower for term in ["uk", "united kingdom", "britain"]):
            params["geo"] = "uk"
        elif any(term in location_lower for term in ["canada"]):
            params["geo"] = "canada"
        elif any(term in location_lower for term in ["europe"]):
            params["geo"] = "europe"
        # For specific cities/states, skip geo filter (Jobicy uses broad regions)

    # Use query as tag parameter for filtering
    if query:
        params["tag"] = query.lower().replace(" ", "-")

    url = "https://jobicy.com/api/v2/remote-jobs?" + urllib.parse.urlencode(params)

    # Fetch with retry
    try:
        body = fetch_with_retry(
            url,
            headers=HEADERS,
            use_cache=True,
            cache_ttl_seconds=source_cache_ttl("jobicy"),
        )
        if body is None:
            log.debug("[Jobicy] Fetch failed for '%s'", query)
            return results

        data = _json.loads(body)
        # Jobicy returns {"jobs": [...]} wrapper
        items = data.get("jobs", [])
        if not isinstance(items, list):
            items = []

        for item in items:
            job = map_jobicy_to_job_result(item)
            if job:
                results.append(job)

    except _json.JSONDecodeError as e:
        log.debug("[Jobicy] JSON parse error: %s", e)
    except Exception as e:
        log.debug("[Jobicy] Request failed: %s", e)

    log.info("[Jobicy] Found %d results for '%s'", len(results), query)
    return results


# ---------------------------------------------------------------------------
# Parallel fetcher orchestration
# ---------------------------------------------------------------------------

def _fetch_dice_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_dice(query["query"], query.get("location", ""))


def _fetch_hn_hiring_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_hn_hiring(query["query"])


def _fetch_remoteok_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_remoteok(query["query"])


def _fetch_weworkremotely_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_weworkremotely(query["query"])


def _fetch_adzuna_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_adzuna(query["query"], query.get("location", ""))


def _fetch_authentic_jobs_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_authenticjobs(query["query"], query.get("location", ""))


def _fetch_jsearch_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_jsearch(query["query"], query.get("location", ""))


def _fetch_usajobs_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_usajobs(query["query"], query.get("location", ""), profile=profile)


def _fetch_serpapi_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_serpapi(query["query"], query.get("location", ""))


def _fetch_jobicy_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_jobicy(query["query"], query.get("location", ""))


def _fetch_hiringcafe_query(query: dict, profile: dict) -> list[JobResult]:
    return fetch_hiringcafe(query["query"], query.get("location", ""))


SOURCE_PHASE_ORDER = ("scraper", "api", "aggregator")


SOURCE_REGISTRY: dict[str, SourceDefinition] = {
    "dice": SourceDefinition("dice", "Dice", "scraper", _fetch_dice_query),
    "hn_hiring": SourceDefinition("hn_hiring", "HN Hiring", "scraper", _fetch_hn_hiring_query),
    "remoteok": SourceDefinition("remoteok", "RemoteOK", "scraper", _fetch_remoteok_query),
    "weworkremotely": SourceDefinition("weworkremotely", "We Work Remotely", "scraper", _fetch_weworkremotely_query),
    "adzuna": SourceDefinition("adzuna", "Adzuna", "api", _fetch_adzuna_query),
    "authentic_jobs": SourceDefinition("authentic_jobs", "Authentic Jobs", "api", _fetch_authentic_jobs_query),
    "usajobs": SourceDefinition("usajobs", "USAJobs (Federal)", "api", _fetch_usajobs_query),
    "jobicy": SourceDefinition("jobicy", "Jobicy (Remote)", "api", _fetch_jobicy_query),
    "hiringcafe": SourceDefinition("hiringcafe", "hiring.cafe", "api", _fetch_hiringcafe_query),
    "jsearch": SourceDefinition("jsearch", "JSearch", "aggregator", _fetch_jsearch_query),
    "serpapi": SourceDefinition("serpapi", "SerpAPI (Google Jobs)", "aggregator", _fetch_serpapi_query),
}


def get_automated_source_display_names() -> list[str]:
    """Return automated source names in execution order for reports."""
    return get_selected_source_display_names(None)


def get_selected_source_display_names(selected_sources: list[str] | None = None) -> list[str]:
    """Return automated source display names for selected source keys."""
    return selected_automated_source_display_names(
        SOURCE_REGISTRY,
        SOURCE_PHASE_ORDER,
        selected_sources,
    )


def _source_display_name(source: str) -> str:
    """Return a human-readable source name for query or result source keys."""
    return source_display_name(SOURCE_REGISTRY, _SOURCE_DISPLAY_NAMES, source)


def get_source_display_name(source: str) -> str:
    """Return a public human-readable source name for diagnostics."""
    return _source_display_name(source)


def fetch_all(
    profile: dict,
    on_progress=None,
    on_source_progress=None,
    max_workers: int | str | None = None,
    slow_query_seconds: int | float | str | None = None,
    selected_sources: list[str] | None = None,
    cancellation_event=None,
) -> list[JobResult]:
    """Fetch from all automated sources with three-phase source ordering.

    Runs scrapers first, native APIs second, and aggregators last so native
    sources win when cross-source deduplication keeps an equally rich listing.
    All results are deduplicated using cross-source fuzzy matching.

    Args:
        profile: Candidate profile dict.
        on_progress: Optional callback(completed, total, source_name) called
                     after each query finishes (backward compatibility).
        on_source_progress: Optional callback(source_name, count, total, status, job_count)
                           called when a source starts ('started') or finishes ('complete').
                           job_count is the number of deduplicated results from that source (0 for 'started').
        max_workers: Optional parallel query worker count. Defaults to JOB_RADAR_MAX_WORKERS or 6.
        slow_query_seconds: Optional threshold for slow-query warnings.
                            Defaults to JOB_RADAR_SLOW_QUERY_SECONDS or 8.
        selected_sources: Optional list of source keys to query. Defaults to all sources.
        cancellation_event: Optional threading.Event-like object. When set,
                            stops new query submission and skips later phases.
    """
    worker_count = resolve_max_workers(max_workers)
    slow_query_threshold = resolve_slow_query_threshold(slow_query_seconds)
    reset_cache_stats()
    queries = build_search_queries(profile)
    queries, queries_by_phase = source_queries_by_phase(
        queries,
        SOURCE_REGISTRY,
        SOURCE_PHASE_ORDER,
        selected_sources,
    )

    all_results = []
    run_state = SourceExecutionState(queries)

    def run_query(q):
        if cancellation_event is not None and cancellation_event.is_set():
            return []
        source = SOURCE_REGISTRY.get(q["source"])
        if source is None:
            log.warning("Unknown source skipped: %s", q["source"])
            return []
        return source.fetch(q, profile)

    def _run_queries_parallel(query_list, phase_name):
        """Helper to run queries in parallel and collect results."""
        phase_results = []

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            # Submit queries grouped by source — fire START callback before each source's queries
            futures = {}
            future_started_at = {}
            started_sources_in_phase = set()
            for q in query_list:
                if cancellation_event is not None and cancellation_event.is_set():
                    break
                source = q["source"]
                if source not in started_sources_in_phase:
                    started_sources_in_phase.add(source)
                    source_index = run_state.mark_source_started()
                    if on_source_progress:
                        display_name = _source_display_name(source)
                        on_source_progress(
                            display_name,
                            source_index,
                            run_state.total_sources,
                            "started",
                            0,
                        )
                future = executor.submit(run_query, q)
                futures[future] = q
                future_started_at[future] = time.perf_counter()

            # Process results as they complete — fire COMPLETE callback when source finishes
            for future in as_completed(futures):
                if cancellation_event is not None and cancellation_event.is_set():
                    for pending in futures:
                        if not pending.done():
                            pending.cancel()
                    break
                q = futures[future]
                completed = run_state.mark_query_complete()
                source = q["source"]
                elapsed = time.perf_counter() - future_started_at[future]
                if elapsed >= slow_query_threshold:
                    run_state.record_slow_query(q, elapsed, slow_query_threshold)
                try:
                    results = future.result()
                    for r in results:
                        if run_state.record_result(source, r):
                            phase_results.append(r)
                except Exception as e:
                    run_state.record_failure(q, e)
                    log.error("Query failed (%s): %s", q, e)
                if on_progress:
                    on_progress(completed, run_state.total_queries, source)

                # Source-level completion tracking
                if run_state.mark_source_query_complete(source):
                    if on_source_progress:
                        display_name = _source_display_name(source)
                        on_source_progress(
                            display_name,
                            run_state.completed_source_count(),
                            run_state.total_sources,
                            "complete",
                            run_state.job_count_for_source(source),
                        )

        return phase_results

    log.info("Running %d search queries in sequential phases with %d workers...", len(queries), worker_count)

    for phase in SOURCE_PHASE_ORDER:
        if cancellation_event is not None and cancellation_event.is_set():
            break
        phase_queries = queries_by_phase[phase]
        if phase_queries:
            log.debug("Running %d %s queries", len(phase_queries), phase)
            all_results.extend(_run_queries_parallel(phase_queries, phase))

    log.info("Total results before deduplication: %d", len(all_results))

    # Cross-source deduplication
    dedup_result = deduplicate_cross_source(all_results)
    all_results = dedup_result["results"]
    dedup_stats = dedup_result["stats"]
    dedup_stats["query_failures"] = len(run_state.query_failures)
    dedup_stats["failed_sources"] = sorted({f["source"] for f in run_state.query_failures})
    dedup_stats["query_failure_details"] = run_state.query_failures
    dedup_stats["slow_query_warnings"] = run_state.slow_query_warnings
    dedup_stats["slow_queries"] = len(run_state.slow_query_warnings)
    dedup_stats["max_workers"] = worker_count
    dedup_stats["slow_query_threshold_seconds"] = slow_query_threshold
    dedup_stats["cache_stats"] = get_cache_stats()
    dedup_stats["cancelled"] = bool(cancellation_event and cancellation_event.is_set())

    log.info("Total unique results after deduplication: %d", len(all_results))
    return all_results, dedup_stats
