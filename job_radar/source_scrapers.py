"""HTML/JSON scraper source fetchers."""

import json as _json
import logging
import urllib.parse

from bs4 import BeautifulSoup

from .cache import fetch_with_retry
from .source_config import source_cache_ttl
from .source_models import JobResult
from .source_parsing import (
    _MAX_COMPANY,
    _MAX_LOCATION,
    _MAX_TITLE,
    _clean_field,
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
