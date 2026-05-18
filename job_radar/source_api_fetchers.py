"""API-backed source fetchers that do not require HTML scraping."""

import json as _json
import logging
import urllib.parse

from .api_config import get_api_key
from .cache import fetch_with_retry
from .rate_limits import check_rate_limit
from .source_config import source_cache_ttl
from .source_mappers import map_jobicy_to_job_result, map_serpapi_to_job_result
from .source_models import JobResult

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def fetch_serpapi(query: str, location: str = "", verbose: bool = False) -> list[JobResult]:
    """Fetch job listings from SerpAPI Google Jobs API."""
    results = []

    api_key = get_api_key("SERPAPI_API_KEY", "SerpAPI")
    if not api_key:
        return results

    if not check_rate_limit("serpapi", verbose=verbose):
        return results

    params = {
        "engine": "google_jobs",
        "q": query,
        "api_key": api_key,
    }
    if location:
        params["location"] = location

    url = "https://serpapi.com/search?" + urllib.parse.urlencode(params)

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
    """Fetch remote job listings from Jobicy API."""
    results = []

    if not check_rate_limit("jobicy", verbose=verbose):
        return results

    params = {"count": "20"}

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

    if query:
        params["tag"] = query.lower().replace(" ", "-")

    url = "https://jobicy.com/api/v2/remote-jobs?" + urllib.parse.urlencode(params)

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
