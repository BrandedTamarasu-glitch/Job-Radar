"""HTML/JSON scraper source fetchers."""

import json as _json
import logging
import re
import urllib.parse

from bs4 import BeautifulSoup

from .cache import fetch_with_retry
from .source_config import source_cache_ttl
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
)

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def fetch_dice(
    query: str,
    location: str = "",
    *,
    fetch_with_retry_func=fetch_with_retry,
) -> list[JobResult]:
    """Fetch job listings from Dice.com by scraping search results."""
    results = []
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://www.dice.com/jobs?q={encoded_q}"
    if location:
        url += f"&location={urllib.parse.quote_plus(location)}"

    body = fetch_with_retry_func(
        url,
        headers=HEADERS,
        cache_ttl_seconds=source_cache_ttl("dice"),
    )
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

            meaningful = [p for p in parts if p not in _SKIP_TOKENS]

            company = "Unknown"
            title = "Unknown Title"
            loc = location or "Unknown"
            posted = "Unknown"
            salary = "Not listed"
            emp_type = ""
            desc_parts = []
            confidence = "high"

            if meaningful:
                company = _clean_field(meaningful[0], _MAX_COMPANY)

            if len(meaningful) > 1:
                title = _clean_field(meaningful[1], _MAX_TITLE)

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
            description = " ".join(desc_parts[:3])

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


def fetch_remoteok(
    query: str,
    *,
    fetch_with_retry_func=fetch_with_retry,
) -> list[JobResult]:
    """Fetch remote job listings from RemoteOK's JSON API."""
    results = []
    url = "https://remoteok.com/api"

    body = fetch_with_retry_func(
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
        query_words = [w for w in query_lower.split() if len(w) >= 3]

        for item in data:
            if not isinstance(item, dict) or "id" not in item:
                continue

            tags = [t.lower() for t in item.get("tags", [])]
            position = item.get("position", "").lower()
            desc = item.get("description", "").lower()
            tags_text = " ".join(tags)

            if query_lower in position or query_lower in tags_text:
                pass
            elif len(query_words) >= 2:
                title_tags = position + " " + tags_text
                if not all(w in title_tags or w in desc for w in query_words):
                    continue
            else:
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


def fetch_weworkremotely(
    query: str,
    *,
    fetch_with_retry_func=fetch_with_retry,
) -> list[JobResult]:
    """Fetch remote job listings from We Work Remotely."""
    results = []
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://weworkremotely.com/remote-jobs/search?term={encoded_q}"

    body = fetch_with_retry_func(
        url,
        headers=HEADERS,
        retries=1,
        cache_ttl_seconds=source_cache_ttl("weworkremotely"),
    )
    if body is None:
        log.info("[WWR] Fetch failed for '%s' - check manual URLs", query)
        return results

    if "Just a moment" in body[:500] or "cf-browser-verification" in body[:2000]:
        log.info("[WWR] Cloudflare protection detected - use manual URL instead")
        return results

    try:
        soup = BeautifulSoup(body, "html.parser")

        listings = soup.select("section.jobs li, section.jobs article")
        if not listings:
            listings = soup.select("li.feature, li.new, article.job")

        for li in listings:
            link = li.select_one("a[href*='/remote-jobs/'], a[href*='/listings/']")
            if not link:
                continue

            href = link.get("href", "")
            if not href.startswith("http"):
                href = f"https://weworkremotely.com{href}"

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


def fetch_hn_hiring(
    technology: str,
    *,
    fetch_with_retry_func=fetch_with_retry,
) -> list[JobResult]:
    """Fetch job listings from hnhiring.com by technology tag."""
    results = []
    url = f"https://hnhiring.com/technologies/{urllib.parse.quote_plus(technology.lower())}"

    body = fetch_with_retry_func(
        url,
        headers=HEADERS,
        cache_ttl_seconds=source_cache_ttl("hn_hiring"),
    )
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
            date_span = item.select_one("span.type-info, span.gray")
            date_posted = date_span.get_text(strip=True) if date_span else "Unknown"

            body_div = item.select_one("div.body")
            if not body_div:
                continue

            header_text = ""
            for child in body_div.children:
                if hasattr(child, "name") and child.name == "p":
                    break
                if isinstance(child, str):
                    header_text += child
                elif hasattr(child, "get_text"):
                    header_text += child.get_text()
            header_text = header_text.strip()

            parts = [p.strip() for p in header_text.split("|")]
            confidence = "high"

            if len(parts) < 2 or len(parts[0]) > _MAX_COMPANY:
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

            extra = " | ".join(parts[3:]) if len(parts) > 3 else ""

            arrangement = _parse_arrangement(f"{location} {extra} {header_text}")
            salary = _extract_salary_from_text(f"{extra} {header_text}")
            emp_type = _extract_employment_type(f"{extra} {header_text}")

            desc_parts = [p.get_text(strip=True) for p in body_div.select("p")]
            description = " ".join(desc_parts)[:500]

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
    """Parse a freeform HN Hiring header.

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
    patterns = [
        r'^([A-Z][\w\s\.]+?)(?:\s+is\s+hiring|\s+[-\u2013]\s)',
        r'^([A-Z][\w\s\.]{2,30}?)(?:\s*\|)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
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
        r'(\$[\d,]+(?:k|K)?(?:\s*[-\u2013]\s*\$[\d,]+(?:k|K)?)?(?:\s*/?\s*(?:yr|year|hr|hour|annually))?)',
        r'([\d,]+(?:k|K)\s*[-\u2013]\s*[\d,]+(?:k|K))',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return "Not listed"
