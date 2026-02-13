"""Job source fetchers and URL generators."""

import html
import json as _json
import logging
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date

from bs4 import BeautifulSoup

from .cache import fetch_with_retry
from .api_config import get_api_key
from .rate_limits import check_rate_limit
from .deduplication import deduplicate_cross_source

log = logging.getLogger(__name__)


@dataclass
class JobResult:
    """A single job listing result."""
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
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None

    def __hash__(self):
        return hash((self.title, self.company, self.source))


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Max field lengths to prevent mangled data in reports
_MAX_TITLE = 100
_MAX_COMPANY = 80
_MAX_LOCATION = 60


def _clean_field(text: str, max_len: int) -> str:
    """Truncate and clean a parsed field."""
    text = text.strip()
    if len(text) > max_len:
        return text[:max_len - 3].rsplit(" ", 1)[0] + "..."
    return text


# ---------------------------------------------------------------------------
# Text cleaning utilities
# ---------------------------------------------------------------------------

def strip_html_and_normalize(text: str) -> str:
    """Strip HTML tags, decode entities, normalize whitespace."""
    if not text:
        return ""
    text = html.unescape(text)
    soup = BeautifulSoup(text, "html.parser")
    plain_text = soup.get_text(separator=" ")
    normalized = re.sub(r'\s+', ' ', plain_text)
    return normalized.strip()


# Map US state names to abbreviations
_STATE_ABBREV = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
}


def parse_location_to_city_state(location_str: str) -> str:
    """Parse location to 'City, State' format.

    Handles:
    - Empty string -> "Unknown"
    - "remote" (case-insensitive) -> "Remote"
    - "City, STATE_ABBR" -> return as-is
    - "City, State Name" -> abbreviate using state map
    - "City, State, Country" -> extract City, State
    - Fallback: return raw string
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

    # Pattern 2: "City, State Name" -> abbreviate state (if US state)
    match = re.match(r'^([^,]+),\s*([^,]+?)(?:\s|,|$)', location_str)
    if match:
        city, state_name = match.groups()
        state_lower = state_name.strip().lower()
        if state_lower in _STATE_ABBREV:
            return f"{city.strip()}, {_STATE_ABBREV[state_lower]}"
        # Pattern 3: "City, State, Country" - if we have a third comma, try extracting just City, State
        remaining = location_str[match.end():].strip()
        if remaining and ',' not in remaining:
            # Second part looks like a country, return City, State_Name as-is
            return f"{city.strip()}, {state_name.strip()}"

    # Fallback: return raw string (better to show raw than guess wrong)
    return location_str.strip()


# ---------------------------------------------------------------------------
# Arrangement detection
# ---------------------------------------------------------------------------

def _parse_arrangement(text: str) -> str:
    """Infer work arrangement from text."""
    lower = text.lower()
    if "remote" in lower:
        return "remote"
    if "hybrid" in lower:
        return "hybrid"
    if "on-site" in lower or "onsite" in lower or "in-office" in lower:
        return "onsite"
    return "unknown"


# ---------------------------------------------------------------------------
# Dice.com fetcher (improved field detection)
# ---------------------------------------------------------------------------

_SALARY_RE = re.compile(
    r'\$[\d,]+(?:\.\d+)?(?:k|K)?(?:\s*[-–]\s*\$[\d,]+(?:\.\d+)?(?:k|K)?)?'
    r'(?:\s*/?\s*(?:yr|year|hr|hour|annually|monthly|weekly))?'
)
_DATE_RE = re.compile(
    r'(?:Today|Yesterday|\d+\s*d(?:ays?)?\s+ago|'
    r'(?:about\s+)?\d+\s*(?:hours?|minutes?)\s+ago|'
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s*\d{4}|'
    r'\d{4}-\d{2}-\d{2})',
    re.IGNORECASE,
)
_EMPLOYMENT_TYPE_RE = re.compile(
    r'^(?:Full[ -]?time|Part[ -]?time|Contract|C2H|Contract to Hire|Temp|Freelance)$',
    re.IGNORECASE,
)
_SKIP_TOKENS = {"Easy Apply", "Apply Now", "\u2022", "•", ""}


def fetch_dice(query: str, location: str = "") -> list[JobResult]:
    """Fetch job listings from Dice.com by scraping search results."""
    results = []
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://www.dice.com/jobs?q={encoded_q}"
    if location:
        url += f"&location={urllib.parse.quote_plus(location)}"

    body = fetch_with_retry(url, headers=HEADERS)
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

    body = fetch_with_retry(url, headers=HEADERS)
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


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', ' ', text).strip()


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
    "jsearch_other": "JSearch (Other)",
    "usajobs": "USAJobs (Federal)",
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

    body = fetch_with_retry(url, headers=HEADERS, retries=1)
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
        # Check for HTTPError-like exceptions
        error_str = str(e).lower()
        if "401" in error_str or "403" in error_str or "unauthorized" in error_str:
            log.error("[Adzuna] Authentication failed - run 'job-radar --setup-apis' to reconfigure")
        else:
            log.debug("[Adzuna] Request failed: %s", e)

    log.info("[Adzuna] Found %d results for '%s'", len(results), query)
    return results


def map_adzuna_to_job_result(item: dict) -> JobResult | None:
    """Map Adzuna API response item to JobResult.

    Validates required fields (title, company, url) and returns None if any are missing.
    """
    # Extract and validate required fields
    title = item.get("title", "").strip()
    company = item.get("company", {}).get("display_name", "").strip()
    url = item.get("redirect_url", "").strip()

    if not title or not company or not url:
        log.debug("[Adzuna] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                 bool(title), bool(company), bool(url))
        return None

    # Location normalization
    location_raw = item.get("location", {}).get("display_name", "")
    location = parse_location_to_city_state(location_raw)

    # Salary fields
    salary_min = item.get("salary_min")
    salary_max = item.get("salary_max")
    salary_currency = "USD"  # Adzuna US endpoint

    # Format salary string for backward compatibility
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

    # Employment type mapping
    contract_type = item.get("contract_type", "").lower()
    contract_time = item.get("contract_time", "").lower()
    emp_type = ""
    if "permanent" in contract_type:
        emp_type = "Permanent"
    if "full_time" in contract_time or "full-time" in contract_time:
        emp_type = "Full-time" if not emp_type else f"{emp_type}, Full-time"

    # Date posted
    date_posted = item.get("created", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="adzuna",
        employment_type=emp_type,
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=salary_currency,
    )


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
        body = fetch_with_retry(url, headers=HEADERS, use_cache=True)
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


def map_authenticjobs_to_job_result(item: dict) -> JobResult | None:
    """Map Authentic Jobs API response item to JobResult.

    Validates required fields (title, company, url) and returns None if any are missing.
    Defensive implementation for unclear API structure per RESEARCH.md.
    """
    # Extract and validate required fields
    title = item.get("title", "").strip()

    # Company may be nested or at top level
    company_raw = item.get("company", {})
    if isinstance(company_raw, dict):
        company = company_raw.get("name", "").strip()
    else:
        company = str(company_raw).strip() if company_raw else ""

    # Try both url and apply_url
    url = item.get("url", "").strip() or item.get("apply_url", "").strip()

    if not title or not company or not url:
        log.debug("[Authentic Jobs] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                 bool(title), bool(company), bool(url))
        return None

    # Location normalization (defensive nested access)
    location_raw = ""
    if isinstance(company_raw, dict):
        location_obj = company_raw.get("location", {})
        if isinstance(location_obj, dict):
            location_raw = location_obj.get("name", "")
        elif location_obj:
            location_raw = str(location_obj)
    location = parse_location_to_city_state(location_raw)

    # Salary - typically not available from Authentic Jobs
    salary = "Not specified"

    # Description cleaning
    description_raw = item.get("description", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    # Arrangement detection
    arrangement = _parse_arrangement(f"{title} {description}")

    # Employment type (defensive access)
    emp_type_obj = item.get("type", {})
    if isinstance(emp_type_obj, dict):
        emp_type = emp_type_obj.get("name", "")
    else:
        emp_type = str(emp_type_obj) if emp_type_obj else ""

    # Date posted
    date_posted = item.get("post_date", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source="authentic_jobs",
        employment_type=emp_type,
        parse_confidence="high",
    )


# ---------------------------------------------------------------------------
# JSearch API fetcher (LinkedIn, Indeed, Glassdoor aggregator)
# ---------------------------------------------------------------------------

# Known JSearch publishers that we treat as separate sources
JSEARCH_KNOWN_SOURCES = {"LinkedIn", "Indeed", "Glassdoor"}


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
        body = fetch_with_retry(url, headers=headers, use_cache=True)
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


def map_jsearch_to_job_result(item: dict) -> JobResult | None:
    """Map JSearch API response item to JobResult.

    Uses job_publisher field for source attribution (LinkedIn, Indeed, Glassdoor).
    Unknown publishers are mapped to "jsearch_other".
    """
    # Extract and validate required fields
    title = item.get("job_title", "").strip()
    company = item.get("employer_name", "").strip()
    url = item.get("job_apply_link", "").strip()

    if not title or not company or not url:
        log.debug("[JSearch] Skipping job with missing required fields: title=%s, company=%s, url=%s",
                 bool(title), bool(company), bool(url))
        return None

    # Source attribution: use original publisher, not "JSearch"
    publisher = item.get("job_publisher", "")
    if publisher in JSEARCH_KNOWN_SOURCES:
        source = publisher.lower()  # "LinkedIn" -> "linkedin"
    else:
        source = "jsearch_other"
        if publisher:
            log.debug("[JSearch] Unknown publisher '%s' mapped to jsearch_other", publisher)

    # Location normalization
    is_remote = item.get("job_is_remote", False)
    if is_remote:
        location = "Remote"
    else:
        city = item.get("job_city", "")
        state = item.get("job_state", "")
        if city and state:
            location = f"{city}, {state}"
        else:
            location = item.get("job_country", "Unknown")

    # Salary fields
    salary_min = item.get("job_min_salary")
    salary_max = item.get("job_max_salary")

    # Format salary string
    if salary_min and salary_max:
        salary = f"${salary_min:,.0f} - ${salary_max:,.0f}"
    elif salary_min:
        salary = f"${salary_min:,.0f}+"
    else:
        salary = "Not specified"

    # Description cleaning
    description_raw = item.get("job_description", "")
    description = strip_html_and_normalize(description_raw)
    if len(description) > 500:
        description = description[:497] + "..."

    # Date posted (extract YYYY-MM-DD)
    date_posted = item.get("job_posted_at_datetime_utc", "")
    if len(date_posted) >= 10:
        date_posted = date_posted[:10]

    # Arrangement detection
    arrangement = _parse_arrangement(f"{title} {description} {location}")

    # Employment type
    emp_type = item.get("job_employment_type", "")

    return JobResult(
        title=_clean_field(title, _MAX_TITLE),
        company=_clean_field(company, _MAX_COMPANY),
        location=_clean_field(location, _MAX_LOCATION),
        arrangement=arrangement,
        salary=salary,
        date_posted=date_posted,
        description=description,
        url=url,
        source=source,
        employment_type=emp_type,
        parse_confidence="high",
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="USD" if salary_min or salary_max else None,
    )


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
        body = fetch_with_retry(url, headers=headers, use_cache=True)
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
# Manual-check URL generators
# ---------------------------------------------------------------------------

def _slugify_for_wellfound(text: str) -> str:
    """Convert text to Wellfound URL slug format.

    Wellfound uses lowercase, hyphen-separated slugs in URL paths.

    Examples:
        "Software Engineer" -> "software-engineer"
        "San Francisco, CA" -> "san-francisco-ca"
        "Senior Full-Stack Developer" -> "senior-full-stack-developer"

    Args:
        text: Text to slugify (job title or location)

    Returns:
        URL-safe slug (lowercase, hyphens, alphanumeric only)
    """
    # Lowercase and strip whitespace
    slug = text.lower().strip()
    # Remove commas (for locations like "San Francisco, CA")
    slug = slug.replace(",", "")
    # Replace spaces with hyphens
    slug = slug.replace(" ", "-")
    # Filter to alphanumeric + hyphens only
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    # Collapse consecutive hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    # Strip leading/trailing hyphens
    return slug.strip("-")


def generate_wellfound_url(title: str, location: str) -> str:
    """Generate a Wellfound search URL with role and optional location.

    Wellfound (formerly AngelList Talent) specializes in startup jobs and
    equity-heavy roles. URL patterns:
    - Remote only: https://wellfound.com/role/r/{role-slug}
    - Role + location: https://wellfound.com/role/l/{role-slug}/{location-slug}

    Examples:
        generate_wellfound_url("Software Engineer", "Remote")
        -> "https://wellfound.com/role/r/software-engineer"

        generate_wellfound_url("Backend Developer", "San Francisco, CA")
        -> "https://wellfound.com/role/l/backend-developer/san-francisco-ca"

    Args:
        title: Job title (e.g., "Software Engineer")
        location: Location string (e.g., "San Francisco, CA" or "Remote")

    Returns:
        Wellfound search URL (no validation performed)
    """
    role_slug = _slugify_for_wellfound(title)

    # Remote detection (case-insensitive)
    if "remote" in location.lower():
        return f"https://wellfound.com/role/r/{role_slug}"

    # Location-specific URL
    location_slug = _slugify_for_wellfound(location)
    return f"https://wellfound.com/role/l/{role_slug}/{location_slug}"


def generate_indeed_url(title: str, location: str, from_days: int = 3) -> str:
    """Generate an Indeed search URL with filters."""
    params = {
        "q": title,
        "l": location,
        "fromage": str(from_days),
        "sort": "date",
    }
    return "https://www.indeed.com/jobs?" + urllib.parse.urlencode(params)


def generate_linkedin_url(title: str, location: str) -> str:
    """Generate a LinkedIn job search URL."""
    params = {
        "keywords": title,
        "location": location,
        "f_TPR": "r604800",
        "sortBy": "DD",
    }
    return "https://www.linkedin.com/jobs/search/?" + urllib.parse.urlencode(params)


def generate_glassdoor_url(title: str, location: str) -> str:
    """Generate a Glassdoor job search URL."""
    params = {
        "sc.keyword": title,
        "locT": "",
        "locId": "",
        "locKeyword": location,
        "fromAge": "3",
        "sortBy": "date",
    }
    return "https://www.glassdoor.com/Job/jobs.htm?" + urllib.parse.urlencode(params)


def generate_weworkremotely_url(query: str) -> str:
    """Generate a We Work Remotely search URL."""
    return f"https://weworkremotely.com/remote-jobs/search?term={urllib.parse.quote_plus(query)}"


def generate_manual_urls(profile: dict) -> list[dict]:
    """Generate manual-check URLs for a candidate profile, sorted by source."""
    urls = []
    titles = profile.get("target_titles", [])[:3]
    location = profile.get("target_market", profile.get("location", ""))

    generators = [
        ("Wellfound", generate_wellfound_url),
        ("Indeed", generate_indeed_url),
        ("LinkedIn", generate_linkedin_url),
        ("Glassdoor", generate_glassdoor_url),
    ]

    # Group by source for cleaner report output
    for source_name, gen_fn in generators:
        for title in titles:
            url = gen_fn(title, location)
            urls.append({
                "source": source_name,
                "title": title,
                "url": url,
            })

    # WWR — Cloudflare blocks automated access, so always include as manual
    for title in titles:
        urls.append({
            "source": "We Work Remotely",
            "title": title,
            "url": generate_weworkremotely_url(title),
        })

    return urls


# ---------------------------------------------------------------------------
# Parallel fetcher orchestration
# ---------------------------------------------------------------------------

# Map skill names to hnhiring.com technology slugs.
_HN_SKILL_SLUGS = {
    "react": "react",
    "python": "python",
    "typescript": "typescript",
    "node.js": "node",
    "node": "node",
    "go": "go",
    "golang": "go",
    "javascript": "javascript",
    "kubernetes": "kubernetes",
    "ruby": "ruby",
    "java": "java",
    "rails": "rails",
    "rust": "rust",
    "vue": "vue",
    "angular": "angular",
    ".net": "dotnet",
    "c#": "csharp",
    "kotlin": "kotlin",
    "scala": "scala",
    "swift": "swift",
    "elixir": "elixir",
    "next.js": "nextjs",
    "nextjs": "nextjs",
    "clojure": "clojure",
    "php": "php",
    "django": "python",
    "flutter": "flutter",
    "svelte": "svelte",
    "react native": "react-native",
}


def build_search_queries(profile: dict) -> list[dict]:
    """Generate search queries from a candidate profile."""
    queries = []
    titles = profile.get("target_titles", [])[:4]
    location = profile.get("target_market", profile.get("location", ""))
    core_skills = profile.get("core_skills", [])
    secondary_skills = profile.get("secondary_skills", [])

    # Dice queries: each target title
    for title in titles:
        queries.append({
            "source": "dice",
            "query": title,
            "location": location,
        })

    # HN Hiring queries: map skills to known slugs, deduplicate
    hn_slugs_seen = set()
    for skill in core_skills + secondary_skills[:5]:
        slug = _HN_SKILL_SLUGS.get(skill.lower())
        if slug and slug not in hn_slugs_seen:
            hn_slugs_seen.add(slug)
            queries.append({
                "source": "hn_hiring",
                "query": slug,
            })

    # RemoteOK queries: top 2 target titles
    for title in titles[:2]:
        queries.append({
            "source": "remoteok",
            "query": title,
        })

    # We Work Remotely queries: top 2 target titles
    for title in titles[:2]:
        queries.append({
            "source": "weworkremotely",
            "query": title,
        })

    # Adzuna queries: each target title (same pattern as Dice)
    for title in titles:
        queries.append({
            "source": "adzuna",
            "query": title,
            "location": location,
        })

    # Authentic Jobs queries: top 2 target titles
    for title in titles[:2]:
        queries.append({
            "source": "authentic_jobs",
            "query": title,
            "location": location,
        })

    return queries


def fetch_all(profile: dict, on_progress=None, on_source_progress=None) -> list[JobResult]:
    """Fetch from all automated sources with sequential scraper-then-API flow.

    Runs scrapers first (Dice, HN Hiring, RemoteOK, WWR), then APIs (Adzuna, Authentic Jobs).
    All results are deduplicated using cross-source fuzzy matching.

    Args:
        profile: Candidate profile dict.
        on_progress: Optional callback(completed, total, source_name) called
                     after each query finishes (backward compatibility).
        on_source_progress: Optional callback(source_name, count, total, status, job_count)
                           called when a source starts ('started') or finishes ('complete').
                           job_count is the number of deduplicated results from that source (0 for 'started').
    """
    queries = build_search_queries(profile)

    # Split queries into scraper and API groups
    SCRAPER_SOURCES = {"dice", "hn_hiring", "remoteok", "weworkremotely"}
    API_SOURCES = {"adzuna", "authentic_jobs"}

    scraper_queries = [q for q in queries if q["source"] in SCRAPER_SOURCES]
    api_queries = [q for q in queries if q["source"] in API_SOURCES]

    all_results = []
    seen = set()
    total = len(queries)
    completed = 0

    # Source-level tracking
    source_names = list(dict.fromkeys(q["source"] for q in queries))  # unique, ordered
    source_query_counts = {}
    source_completed = {}
    source_job_counts = {}
    for q in queries:
        source_query_counts[q["source"]] = source_query_counts.get(q["source"], 0) + 1
        source_completed[q["source"]] = 0
        source_job_counts[q["source"]] = 0
    sources_started = 0
    sources_done = 0
    total_sources = len(source_names)

    def run_query(q):
        if q["source"] == "dice":
            return fetch_dice(q["query"], q.get("location", ""))
        elif q["source"] == "hn_hiring":
            return fetch_hn_hiring(q["query"])
        elif q["source"] == "remoteok":
            return fetch_remoteok(q["query"])
        elif q["source"] == "weworkremotely":
            return fetch_weworkremotely(q["query"])
        elif q["source"] == "adzuna":
            return fetch_adzuna(q["query"], q.get("location", ""))
        elif q["source"] == "authentic_jobs":
            return fetch_authenticjobs(q["query"], q.get("location", ""))
        return []

    def _run_queries_parallel(query_list, phase_name):
        """Helper to run queries in parallel and collect results."""
        nonlocal completed, sources_started, sources_done
        phase_results = []

        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit queries grouped by source — fire START callback before each source's queries
            futures = {}
            started_sources_in_phase = set()
            for q in query_list:
                source = q["source"]
                if source not in started_sources_in_phase:
                    started_sources_in_phase.add(source)
                    sources_started += 1
                    if on_source_progress:
                        display_name = _SOURCE_DISPLAY_NAMES.get(source, source)
                        on_source_progress(display_name, sources_started, total_sources, "started", 0)
                futures[executor.submit(run_query, q)] = q

            # Process results as they complete — fire COMPLETE callback when source finishes
            for future in as_completed(futures):
                q = futures[future]
                completed += 1
                source = q["source"]
                try:
                    results = future.result()
                    for r in results:
                        key = (r.title.lower().strip(), r.company.lower().strip())
                        if key not in seen:
                            seen.add(key)
                            phase_results.append(r)
                            # Track per-source job count
                            source_job_counts[source] += 1
                except Exception as e:
                    log.error("Query failed (%s): %s", q, e)
                if on_progress:
                    on_progress(completed, total, source)

                # Source-level completion tracking
                source_completed[source] += 1
                if source_completed[source] == source_query_counts[source]:
                    sources_done += 1
                    if on_source_progress:
                        display_name = _SOURCE_DISPLAY_NAMES.get(source, source)
                        on_source_progress(display_name, sources_done, total_sources, "complete", source_job_counts.get(source, 0))

        return phase_results

    log.info("Running %d search queries in sequential phases...", len(queries))

    # Phase 1: Scrapers
    if scraper_queries:
        log.debug("Phase 1: Running %d scraper queries", len(scraper_queries))
        scraper_results = _run_queries_parallel(scraper_queries, "scraper")
        all_results.extend(scraper_results)

    # Phase 2: APIs
    if api_queries:
        log.debug("Phase 2: Running %d API queries", len(api_queries))
        api_results = _run_queries_parallel(api_queries, "api")
        all_results.extend(api_results)

    log.info("Total results before deduplication: %d", len(all_results))

    # Cross-source deduplication
    all_results = deduplicate_cross_source(all_results)

    log.info("Total unique results after deduplication: %d", len(all_results))
    return all_results
